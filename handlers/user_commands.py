"""Trình xử lý lệnh người dùng"""
import asyncio
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from config import VERIFY_COST
from database_mysql import Database
from utils.checks import is_not_blocked
from utils.i18n import DEFAULT_LANGUAGE, get_user_language, normalize_language, tr
from utils.messages import (
    get_admin_key_keyboard,
    get_admin_key_menu_message,
    get_back_admin_button_label,
    get_back_main_button_label,
    get_language_selection_keyboard,
    get_language_selection_message,
    get_service_display_name,
    get_welcome_message,
    get_welcome_keyboard,
    get_admin_users_keyboard,
    get_admin_users_menu_message,
    get_help_message,
    get_netflix_keyboard,
    get_netflix_menu_message,
    get_ui_label,
    get_verify_menu_message,
    get_verify_keyboard,
    get_admin_menu_message,
    get_admin_keyboard,
    get_proxy_mgmt_keyboard,
)

logger = logging.getLogger(__name__)

# System command mapping signature
_CMD_SIG_ID = "68757963-6f6e-6764-6576-3035"


def get_current_language(
        context: ContextTypes.DEFAULT_TYPE,
        db: Optional[Database] = None,
        user_id: Optional[int] = None,
        default: str = DEFAULT_LANGUAGE,
) -> str:
    """Lấy ngôn ngữ hiện tại, ưu tiên DB rồi tới cache trong context."""
    language = None

    if db and user_id is not None:
        language = get_user_language(db, user_id, default=None)

    if not language:
        language = normalize_language(context.user_data.get('selected_language'), default=default)

    if language:
        context.user_data['selected_language'] = language

    return language or default


def build_main_menu_text(language: str, balance: int, message_text: str = "") -> str:
    """Ghép text menu chính theo ngôn ngữ."""
    final_message_parts = []
    if message_text:
        final_message_parts.append(message_text)

    final_message_parts.append(tr(language, "main.title"))
    final_message_parts.append(tr(language, "main.balance", balance=balance))
    final_message_parts.append(f"━━━━━━━━━━━━━━━━━━━━\n{tr(language, 'main.prompt')}")
    return "\n\n".join(final_message_parts)


async def clear_user_state(context: ContextTypes.DEFAULT_TYPE, keep_data: bool = False):
    """Xóa trạng thái hội thoại của người dùng."""
    # Luôn xóa các trạng thái bước tiếp theo và message_id
    keys_to_delete = ['action_next_step', 'prompt_message_id']

    # Nếu không yêu cầu giữ dữ liệu, xóa tất cả các key bắt đầu bằng action_ hoặc admin_
    if not keep_data:
        keys_to_delete += [key for key in context.user_data if
                           key.startswith('action_') or key.startswith('admin_') or key == 'messages_to_cleanup']

    for key in set(keys_to_delete):
        context.user_data.pop(key, None)


def register_cleanup_message(context: ContextTypes.DEFAULT_TYPE, message_id: int):
    """Đăng ký một tin nhắn vào danh sách dọn dẹp để xóa sau này."""
    if 'messages_to_cleanup' not in context.user_data:
        context.user_data['messages_to_cleanup'] = []
    if message_id not in context.user_data['messages_to_cleanup']:
        context.user_data['messages_to_cleanup'].append(message_id)


async def cleanup_input_messages(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        keep_data: bool = False,
):
    """Xóa tất cả tin nhắn trong luồng nhập liệu hiện tại và gỡ keyboard (Đặc trị Mobile)."""
    chat_id = update.effective_chat.id
    messages = context.user_data.get('messages_to_cleanup', [])
    prompt_id = context.user_data.get('prompt_message_id')

    if not messages and not context.user_data.get('action_next_step'):
        return

    # KỸ THUẬT KHẮC CHẾ MOBILE:
    try:
        # 1. Chỉnh sửa tin nhắn hướng dẫn để gỡ thuộc tính ForceReply (Ép UI đóng bàn phím ngay lập tức)
        if prompt_id:
            try:
                await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=prompt_id, reply_markup=None)
            except Exception:
                pass

        # 2. Gửi lệnh xóa bàn phím tàng hình bằng cách "Trả lời ngược" vào Prompt
        remove_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="\u2800",
            reply_markup=ReplyKeyboardRemove(selective=False),
            reply_to_message_id=prompt_id if prompt_id else None
        )

        # 3. Chờ 0.6s để Mobile đồng bộ UI (Khoảng thời gian lý tưởng cho Mobile)
        await asyncio.sleep(0.6)

        # 4. Xóa sạch các tin nhắn cũ
        for mid in messages:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass

        # 5. Xóa nốt tin nhắn tàng hình dọn dẹp
        await context.bot.delete_message(chat_id=chat_id, message_id=remove_msg.message_id)
    except Exception:
        # Fallback: Nếu gặp lỗi kỹ thuật vẫn phải xóa sạch tin nhắn để tránh rác
        for mid in messages:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass

    context.user_data['messages_to_cleanup'] = []
    await clear_user_state(context, keep_data=keep_data)


def get_active_service_name(context: ContextTypes.DEFAULT_TYPE, language: str = DEFAULT_LANGUAGE) -> str:
    """Lấy tên hiển thị của dịch vụ đang thực hiện."""
    service_type = context.user_data.get('action_service_type')
    next_step = context.user_data.get('action_next_step')
    if service_type:
        return get_service_display_name(service_type, language)
    if next_step:
        return get_service_display_name(next_step, language)
    return tr(language, "service.other")


async def is_user_busy(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Optional[Database] = None) -> bool:
    """Kiểm tra xem người dùng có đang trong một luồng thực hiện nào không."""
    next_step = context.user_data.get('action_next_step')
    if not next_step:
        return False

    language = get_current_language(context, db, update.effective_user.id if update.effective_user else None)

    # Nếu là lệnh /start, cho phép bỏ qua để reset
    if update.message and update.message.text == '/start':
        await cleanup_input_messages(update, context)
        return False

    service_name = get_active_service_name(context, language)

    if update.callback_query:
        await update.callback_query.answer(
            text=tr(language, "busy.callback", service_name=service_name),
            show_alert=True,
        )
    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(tr(language, "busy.close_old"), callback_data='cancel_to_main')
        ]])
        await update.message.reply_text(
            tr(language, "busy.message"),
            reply_markup=keyboard,
            parse_mode='HTML',
        )

    return True


async def show_language_selection(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db: Database,
):
    """Hiển thị màn chọn ngôn ngữ cho user chưa có language."""
    chat_id = update.effective_chat.id
    query = update.callback_query

    await _delete_tracked_menu(context, chat_id, 'last_main_menu_id')
    await _delete_tracked_menu(context, chat_id, 'last_verify_menu_id')
    await _delete_tracked_menu(context, chat_id, 'last_netflix_menu_id')
    await _delete_tracked_menu(context, chat_id, 'last_admin_menu_id')
    await _delete_tracked_menu(context, chat_id, 'last_admin_users_menu_id')
    await _delete_tracked_menu(context, chat_id, 'last_admin_key_menu_id')

    message_text = get_language_selection_message()
    keyboard = get_language_selection_keyboard()

    if query:
        try:
            await query.answer(tr('en', "language.select.required"), show_alert=False)
        except Exception:
            pass

        try:
            sent_msg = await query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='HTML',
            )
            context.user_data['last_language_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, chat_id, 'last_language_menu_id')
    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode='HTML',
    )
    context.user_data['last_language_menu_id'] = sent_msg.message_id


@is_not_blocked
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, message_text: str = ""):
    """Hiển thị menu chính và xóa trạng thái."""
    # Chỉ gọi dọn dẹp nếu người dùng chưa vừa mới nhấn nút Hủy (đã dọn dẹp rồi)
    if context.user_data.get('messages_to_cleanup') or context.user_data.get('action_next_step'):
        await cleanup_input_messages(update, context)

    query = update.callback_query
    user = update.effective_user
    is_admin = user.id == ADMIN_USER_ID
    language = get_current_language(context, db, user.id)

    user_data = db.get_user(user.id)
    balance = user_data['balance'] if user_data else 0
    final_message_text = build_main_menu_text(language, balance, message_text)
    keyboard = get_welcome_keyboard(is_admin, language)

    if query:
        try:
            sent_msg = await query.edit_message_text(text=final_message_text, reply_markup=keyboard, parse_mode='HTML')
            context.user_data['last_main_menu_id'] = sent_msg.message_id
        except Exception:
            try:
                sent_msg = await context.bot.send_message(chat_id=user.id, text=final_message_text,
                                                          reply_markup=keyboard,
                                               parse_mode='HTML')
                context.user_data['last_main_menu_id'] = sent_msg.message_id
            except Exception as e:
                logger.warning(f"Không thể gửi menu chính: {e}")
    else:
        # Nếu có menu cũ, hãy thử xóa nó trước khi gửi menu mới
        last_menu_id = context.user_data.get('last_main_menu_id')
        if last_menu_id:
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=last_menu_id)
            except Exception:
                pass

        sent_msg = await update.message.reply_text(text=final_message_text, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['last_main_menu_id'] = sent_msg.message_id


async def _delete_tracked_menu(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        menu_key: str,
):
    """Xoa menu da luu de tranh lap giao dien."""
    menu_id = context.user_data.get(menu_key)
    if not menu_id:
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=menu_id)
    except Exception:
        pass
    finally:
        context.user_data[menu_key] = None


async def start_input_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt_text: str, next_step: str,
                           cancel_callback: str):
    """Hàm helper để bắt đầu một luồng nhập liệu, hỗ trợ cả Message và CallbackQuery."""
    chat_id = update.effective_chat.id
    query = update.callback_query
    language = get_current_language(context)

    context.user_data['action_next_step'] = next_step

    # Tự động dọn dẹp Menu Chính cũ nếu có khi bắt đầu luồng mới
    last_menu_id = context.user_data.get('last_main_menu_id')
    if last_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_menu_id)
            context.user_data['last_main_menu_id'] = None
        except Exception:
            pass

    # Tương tự cho Menu Admin nếu đang ở luồng Admin
    last_admin_menu_id = context.user_data.get('last_admin_menu_id')
    if last_admin_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_admin_menu_id)
            context.user_data['last_admin_menu_id'] = None
        except Exception:
            pass

    # Nếu là callback, thêm tin nhắn hiện tại (menu) vào danh sách dọn dẹp
    if query:
        register_cleanup_message(context, query.message.message_id)

    last_verify_menu_id = context.user_data.get('last_verify_menu_id')
    if last_verify_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_verify_menu_id)
            context.user_data['last_verify_menu_id'] = None
        except Exception:
            pass

    last_netflix_menu_id = context.user_data.get('last_netflix_menu_id')
    if last_netflix_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_netflix_menu_id)
            context.user_data['last_netflix_menu_id'] = None
        except Exception:
            pass

    last_admin_users_menu_id = context.user_data.get('last_admin_users_menu_id')
    if last_admin_users_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_admin_users_menu_id)
            context.user_data['last_admin_users_menu_id'] = None
        except Exception:
            pass

    last_admin_key_menu_id = context.user_data.get('last_admin_key_menu_id')
    if last_admin_key_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_admin_key_menu_id)
            context.user_data['last_admin_key_menu_id'] = None
        except Exception:
            pass

    last_language_menu_id = context.user_data.get('last_language_menu_id')
    if last_language_menu_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_language_menu_id)
            context.user_data['last_language_menu_id'] = None
        except Exception:
            pass

    prompt_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=prompt_text,
        reply_markup=ForceReply(selective=True),
        parse_mode='HTML'
    )
    context.user_data['prompt_message_id'] = prompt_msg.message_id
    register_cleanup_message(context, prompt_msg.message_id)

    cancel_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(tr(language, "action.cancel"), callback_data=cancel_callback)
    ]])
    cancel_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=tr(language, "prompt.cancel_hint"),
        reply_markup=cancel_keyboard
    )
    register_cleanup_message(context, cancel_msg.message_id)


async def show_admin_dashboard(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        db: Optional[Database] = None,
):
    """Hiển thị menu quản trị (dashboard) và xóa trạng thái."""
    await cleanup_input_messages(update, context)
    query = update.callback_query
    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)

    final_text = get_admin_menu_message(language)
    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    # Nếu có menu admin cũ, hãy thử xóa nó trước khi gửi menu mới
    if query:
        try:
            sent_msg = await query.edit_message_text(
                text=final_text,
                reply_markup=get_admin_keyboard(language),
                parse_mode='HTML',
            )
            context.user_data['last_admin_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, user_id, 'last_admin_menu_id')

    sent_msg = await context.bot.send_message(
        chat_id=user_id,
        text=final_text,
        reply_markup=get_admin_keyboard(language),
        parse_mode='HTML'
    )
    context.user_data['last_admin_menu_id'] = sent_msg.message_id


async def show_admin_users_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        db: Optional[Database] = None,
):
    """Hiển thị submenu quản lý users của admin."""
    await cleanup_input_messages(update, context)
    query = update.callback_query
    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)

    final_text = get_admin_users_menu_message(language)
    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    if query:
        try:
            sent_msg = await query.edit_message_text(
                text=final_text,
                reply_markup=get_admin_users_keyboard(language),
                parse_mode='HTML',
            )
            context.user_data['last_admin_users_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, user_id, 'last_admin_users_menu_id')
    sent_msg = await context.bot.send_message(
        chat_id=user_id,
        text=final_text,
        reply_markup=get_admin_users_keyboard(language),
        parse_mode='HTML',
    )
    context.user_data['last_admin_users_menu_id'] = sent_msg.message_id


async def show_admin_key_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        db: Optional[Database] = None,
):
    """Hiển thị submenu key của admin."""
    await cleanup_input_messages(update, context)
    query = update.callback_query
    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)

    final_text = get_admin_key_menu_message(language)
    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    if query:
        try:
            sent_msg = await query.edit_message_text(
                text=final_text,
                reply_markup=get_admin_key_keyboard(language),
                parse_mode='HTML',
            )
            context.user_data['last_admin_key_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, user_id, 'last_admin_key_menu_id')
    sent_msg = await context.bot.send_message(
        chat_id=user_id,
        text=final_text,
        reply_markup=get_admin_key_keyboard(language),
        parse_mode='HTML',
    )
    context.user_data['last_admin_key_menu_id'] = sent_msg.message_id


async def show_verify_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        db: Optional[Database] = None,
):
    """Hiển thị menu xác thực theo một flow thống nhất."""
    if context.user_data.get('messages_to_cleanup') or context.user_data.get('action_next_step'):
        await cleanup_input_messages(update, context)

    chat_id = update.effective_chat.id
    query = update.callback_query
    language = get_current_language(context, db, update.effective_user.id if update.effective_user else None)
    final_text = get_verify_menu_message(language)

    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    if query:
        try:
            sent_msg = await query.edit_message_text(
                text=final_text,
                reply_markup=get_verify_keyboard(language),
                parse_mode='HTML',
            )
            context.user_data['last_verify_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, chat_id, 'last_verify_menu_id')
    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=final_text,
        reply_markup=get_verify_keyboard(language),
        parse_mode='HTML',
    )
    context.user_data['last_verify_menu_id'] = sent_msg.message_id


async def show_netflix_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        db: Optional[Database] = None,
):
    """Hiển thị menu Netflix theo một flow thống nhất."""
    if context.user_data.get('messages_to_cleanup') or context.user_data.get('action_next_step'):
        await cleanup_input_messages(update, context)

    chat_id = update.effective_chat.id
    query = update.callback_query
    language = get_current_language(context, db, update.effective_user.id if update.effective_user else None)
    final_text = get_netflix_menu_message(language)

    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    if query:
        try:
            sent_msg = await query.edit_message_text(
                text=final_text,
                reply_markup=get_netflix_keyboard(language),
                parse_mode='HTML',
            )
            context.user_data['last_netflix_menu_id'] = sent_msg.message_id
            return
        except Exception:
            pass

    await _delete_tracked_menu(context, chat_id, 'last_netflix_menu_id')
    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=final_text,
        reply_markup=get_netflix_keyboard(language),
        parse_mode='HTML',
    )
    context.user_data['last_netflix_menu_id'] = sent_msg.message_id


async def show_main_menu_after_delay(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db: Database,
        message_text: str = "",
        delay: float = 2,
):
    """Hiển thị menu chính sau một khoảng trễ ngắn."""
    await asyncio.sleep(delay)
    await show_main_menu(update, context, db, message_text)


async def show_admin_dashboard_after_delay(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        delay: float = 2,
        db: Optional[Database] = None,
):
    """Hiển thị dashboard admin sau một khoảng trễ ngắn."""
    await asyncio.sleep(delay)
    await show_admin_dashboard(update, context, message_text, db=db)


async def show_admin_key_menu_after_delay(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str = "",
        delay: float = 2,
        db: Optional[Database] = None,
):
    """Hiển thị submenu key của admin sau một khoảng trễ ngắn."""
    await asyncio.sleep(delay)
    await show_admin_key_menu(update, context, message_text, db=db)


async def send_or_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """Helper để gửi tin nhắn, hoạt động cả khi dùng lệnh và bấm nút."""
    if update.message:
        return await update.message.reply_text(text, **kwargs)
    else:
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)


# --- Command Handlers ---
@is_not_blocked
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /start, hiển thị menu chính."""
    if await is_user_busy(update, context, db):
        return

    user = update.effective_user
    user_id = user.id

    # BẮT BUỘC CÓ USERNAME
    if not user.username:
        await send_or_reply(update, context,
                            tr(DEFAULT_LANGUAGE, "start.no_username"),
                            parse_mode='HTML'
                            )
        return

    username = user.username
    full_name = user.full_name or ""
    context.user_data['selected_language'] = normalize_language(db.get_user_language(user_id), default=DEFAULT_LANGUAGE)

    if not db.user_exists(user_id):
        invited_by: Optional[int] = None
        if context.args:
            try:
                invited_by_id = int(context.args[0])
                if db.user_exists(invited_by_id) and invited_by_id != user_id:
                    invited_by = invited_by_id
            except (IndexError, ValueError):
                pass

        db.create_user(user_id, username, full_name, invited_by)
        context.user_data['pending_welcome_after_language'] = True
        context.user_data['pending_welcome_after_language_invited'] = bool(invited_by)
    else:
        db.update_user_profile(user_id, username, full_name)

    stored_language = db.get_user_language(user_id)
    if not stored_language:
        await show_language_selection(update, context, db)
        return

    language = get_current_language(context, db, user_id)
    greeting_message = (
        get_welcome_message(full_name, bool(context.user_data.pop('pending_welcome_after_language_invited', False)), language)
        if context.user_data.pop('pending_welcome_after_language', False)
        else tr(language, "welcome.back", full_name=user.full_name)
    )

    await show_main_menu(update, context, db, message_text=greeting_message)


@is_not_blocked
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Optional[Database] = None):
    """Xử lý lệnh /invite"""
    user_id = update.effective_user.id
    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"
    language = get_current_language(context, db, user_id)
    await send_or_reply(update, context,
                        tr(language, "invite.message", invite_link=invite_link))


@is_not_blocked
async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /checkin"""
    if await is_user_busy(update, context, db):
        return

    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)
    if db.checkin(user_id):
        user = db.get_user(user_id)
        await send_or_reply(update, context,
                            tr(language, "checkin.success", balance=user['balance']))
    else:
        await send_or_reply(update, context, tr(language, "checkin.already"))


@is_not_blocked
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /balance"""
    if await is_user_busy(update, context, db):
        return

    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)
    user_data = db.get_user(user_id)
    balance = user_data['balance'] if user_data else 0
    await send_or_reply(update, context, tr(language, "balance.current", balance=balance))


@is_not_blocked
async def to_up_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /to_up"""
    if await is_user_busy(update, context, db):
        return

    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)

    if context.args:
        # Xử lý trực tiếp nếu có đối số
        user_input = context.args[0].strip()
        result = db.use_card_key(user_input, user_id)
        if result is None:
            await send_or_reply(update, context, tr(language, "key.not_found"))
        elif isinstance(result, int) and result < 0:
            error_map = {
                -1: tr(language, "key.used_up"),
                -2: tr(language, "key.expired"),
                -3: tr(language, "key.already_used"),
            }
            await send_or_reply(update, context, error_map.get(result, tr(language, "common.unknown_error")))
        else:
            user = db.get_user(user_id)
            await send_or_reply(update, context,
                                tr(language, "key.success", amount=result, balance=user['balance']))
        return

    await start_input_flow(update, context, tr(language, "topup.prompt"), 'use_key_step_1', 'cancel_to_main')


@is_not_blocked
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Optional[Database] = None):
    """Xử lý lệnh /help"""
    if await is_user_busy(update, context, db):
        return

    user_id = update.effective_user.id
    language = get_current_language(context, db, user_id)
    await send_or_reply(update, context, get_help_message(language), parse_mode='HTML')


@is_not_blocked
async def check_cookie_netflix_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /check_cookie_netflix"""
    if await is_user_busy(update, context, db):
        return

    from handlers.netflix_handlers import check_cookie_netflix_command as _cmd
    await _cmd(update, context, db)
    return

    # Thiết lập trạng thái chờ nhập (nếu lệnh không tự kết thúc luồng)


@is_not_blocked
async def get_cookie_netflix_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /get_cookie_netflix"""
    if await is_user_busy(update, context, db):
        return

    from handlers.netflix_handlers import get_cookie_netflix_command as _cmd
    await _cmd(update, context, db)
    return


@is_not_blocked
async def convertNetflixUrl_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /convertNetflixUrl"""
    if await is_user_busy(update, context, db):
        return

    # KHI NGƯỜI DÙNG GÕ LỆNH KÈM THEO ĐỐI SỐ
    if context.args:
        cookie_text = " ".join(context.args)
        await _process_netflix_cookie(update, context, db, cookie_text)
        return

    context.user_data['action_service_type'] = 'convert_url_login_app_netflix'
    language = get_current_language(context, db, update.effective_user.id)
    service_label = get_ui_label('convert_url_login_app_netflix', language)

    if language == 'en':
        prompt_text = (
            f"<b>{service_label}</b>\n\n"
            "Please send your Netflix cookie in the reply message below or upload a .txt/.json file.\n"
            f"Note: Each successful request costs 💰 {VERIFY_COST} points."
        )
    else:
        prompt_text = (
            f"<b>{service_label}</b>\n\n"
            "Vui lòng nhập cookie Netflix vào tin nhắn trả lời bên dưới hoặc gửi file .txt/.json\n"
            f"Lưu ý: Mỗi lần xác thực thành công sẽ tốn 💰 {VERIFY_COST} điểm."
        )

    await start_input_flow(update, context, prompt_text, 'verify_step_1', 'cancel_to_netflix_menu')


@is_not_blocked
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tất cả các sự kiện bấm nút."""
    query = update.callback_query
    action = query.data
    user_id = query.from_user.id
    is_admin = user_id == ADMIN_USER_ID
    language = get_current_language(context, db, user_id)

    if action.startswith('select_language:'):
        selected_language = normalize_language(action.split(':', 1)[1], default=None)
        if not selected_language:
            await query.answer(tr('en', "language.select.required"), show_alert=True)
            return

        db.set_user_language(user_id, selected_language)
        db.update_user_profile(user_id, query.from_user.username or "", query.from_user.full_name or "")
        context.user_data['selected_language'] = selected_language

        if context.user_data.pop('pending_welcome_after_language', False):
            message_text = get_welcome_message(
                query.from_user.full_name or "",
                bool(context.user_data.pop('pending_welcome_after_language_invited', False)),
                selected_language,
            )
        elif context.user_data.pop('pending_welcome_back_after_language', False):
            message_text = tr(selected_language, "welcome.back", full_name=query.from_user.full_name or "")
        else:
            message_text = (
                f"{tr(selected_language, 'language.saved')}\n"
                f"{tr(selected_language, 'language.saved.current')}"
            )

        await query.answer(tr(selected_language, "language.saved.alert"), show_alert=False)
        await show_main_menu(update, context, db, message_text=message_text)
        return

    await query.answer()

    # Chặn spam: Nếu đang trong luồng nhập liệu, chỉ cho phép các nút Hủy/Quay lại hoạt động
    allowed_actions = ['cancel_to_main', 'cancel_to_verify_menu', 'cancel_to_admin_menu', 'cancel_to_admin_users_menu',
                       'cancel_to_admin_key_menu', 'cancel_to_netflix_menu', 'back_to_main', 'admin_proxy_mgmt']
    if action not in allowed_actions:
        if await is_user_busy(update, context, db):
            return

    # Bỏ qua các nút noop
    if action == 'noop':
        return

    # --- Logic quản trị nhanh (Quick Admin) ---
    if action.startswith('admin_q_'):
        if not is_admin: return
        parts = action.split(':')
        cmd = parts[0]
        target_id = int(parts[1])

        if cmd == 'admin_q_block':
            db.block_user(target_id)
            await query.answer(
                "User blocked!" if language == 'en' else "Đã chặn người dùng!",
                show_alert=True,
            )
        elif cmd == 'admin_q_unblock':
            db.unblock_user(target_id)
            await query.answer(
                "User unblocked!" if language == 'en' else "Đã bỏ chặn người dùng!",
                show_alert=True,
            )
        elif cmd == 'admin_q_add':
            amount = int(parts[2])
            db.add_balance(target_id, amount)
            await query.answer(
                f"Added {amount} points!" if language == 'en' else f"Đã cộng {amount} điểm!",
                show_alert=True,
            )

        # Quay lại profile người dùng để cập nhật thông tin
        user_info = db.get_user(target_id)
        if user_info:
            from handlers.admin_commands import handle_admin_search_result
            await handle_admin_search_result(update, context, user_info, db)
        return

    # --- Điều hướng Menu ---
    if action == 'back_to_main':
        await show_main_menu(update, context, db)
        return

    if action == 'cancel_to_main':
        await cleanup_input_messages(update, context)
        await show_main_menu(update, context, db)  # Không truyền message_text
        return

    if action == 'cancel_to_verify_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await show_verify_menu(update, context, db=db)
        return

    if action == 'cancel_to_admin_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await show_admin_dashboard(update, context, db=db)
        return

    if action == 'cancel_to_admin_users_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await show_admin_users_menu(update, context, db=db)
        return

    if action == 'cancel_to_admin_key_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await show_admin_key_menu(update, context, db=db)
        return

    if action == 'cancel_to_netflix_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await show_netflix_menu(update, context, db=db)
        return

    if action == 'verify_menu':
        await show_verify_menu(update, context, db=db)
        return

    if action == 'netflix_menu':
        await show_netflix_menu(update, context, db=db)
        return

    if action == 'admin_menu':
        if not is_admin: return
        await show_admin_dashboard(update, context, db=db)
        return

    if action == 'admin_users_menu':
        if not is_admin: return
        await show_admin_users_menu(update, context, db=db)
        return

    if action == 'admin_key_menu':
        if not is_admin: return
        await show_admin_key_menu(update, context, db=db)
        return

    if action == 'admin_maintenance':
        if not is_admin: return
        from handlers.maintenance_handlers import admin_maintenance_menu
        await admin_maintenance_menu(update, context, db)
        return

    if action.startswith('toggle_m:'):
        if not is_admin: return
        from handlers.maintenance_handlers import toggle_maintenance
        await toggle_maintenance(update, context, db)
        return

    # --- Chức năng người dùng ---
    if action == 'help':
        await query.message.reply_text(get_help_message(language), parse_mode='HTML')
    elif action == 'invite':
        await invite_command(update, context, db)
    elif action == 'checkin':
        await checkin_command(update, context, db)
    elif action == 'check_cc' or action == 'check_cc_menu':
        from utils.checks import check_maintenance
        if await check_maintenance(update, db, 'check_cc'): return
        from handlers.cc_handlers import checkCC_command
        await checkCC_command(update, context, db)
        return

    if action == 'to_up':
        await to_up_command(update, context, db)

    elif action in ('convert_url_login_app_netflix', 'login_app_netflix', 'netflix_verify'):
        from utils.checks import check_maintenance
        if await check_maintenance(update, db, 'convert_url_login_app_netflix'): return
        await convertNetflixUrl_command(update, context, db)
        return

    elif action == 'get_cookie_netflix':
        from handlers.netflix_handlers import get_cookie_netflix_command as _cmd
        await _cmd(update, context, db)
        return

    elif action == 'netflix_check':
        from handlers.netflix_handlers import check_cookie_netflix_command as _cmd
        await _cmd(update, context, db)
        return

    elif action == 'discord_quest':
        from utils.checks import check_maintenance
        if await check_maintenance(update, db, 'discord_quest_auto'): return
        from handlers.discord_quest_handlers import discord_quest_command
        await discord_quest_command(update, context, db)

    elif action.startswith('verify_'):
        # Kiểm tra bảo trì
        if db.is_service_maintenance(action):
            await query.answer()
            await query.message.reply_text(
                tr(language, "checks.maintenance"),
                parse_mode='HTML')
            return
        service_name = get_service_display_name(action, language)
        if service_name:
            context.user_data['action_service_type'] = action
            from utils.messages import get_verify_usage_message
            prompt = get_verify_usage_message(service_name, language)
            await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')

    elif action.startswith('admin_'):
        if not is_admin: return

        admin_prompts = (
            {
                'admin_add_balance': ("Please enter the user ID to add balance to:", 'admin_add_balance_step_1', 'cancel_to_admin_menu'),
                'admin_block': ("Please enter the user ID to block:", 'admin_block_step_1', 'cancel_to_admin_users_menu'),
                'admin_unblock': ("Please enter the user ID to unblock:", 'admin_unblock_step_1', 'cancel_to_admin_users_menu'),
                'admin_broadcast': ("Please enter the broadcast message:", 'admin_broadcast_step_1', 'cancel_to_admin_menu'),
                'admin_gen_key': ("Please enter the key code (example: VIP2024):", 'admin_gen_key_step_1', 'cancel_to_admin_key_menu'),
                'admin_search_user': ("Please enter the user ID or username to search:", 'admin_search_step_1', 'cancel_to_admin_users_menu'),
            }
            if language == 'en' else
            {
                'admin_add_balance': ("Vui lòng nhập ID người dùng cần cộng điểm:", 'admin_add_balance_step_1', 'cancel_to_admin_menu'),
                'admin_block': ("Vui lòng nhập ID người dùng cần chặn:", 'admin_block_step_1', 'cancel_to_admin_users_menu'),
                'admin_unblock': ("Vui lòng nhập ID người dùng cần bỏ chặn:", 'admin_unblock_step_1', 'cancel_to_admin_users_menu'),
                'admin_broadcast': ("Vui lòng nhập nội dung thông báo muốn gửi:", 'admin_broadcast_step_1', 'cancel_to_admin_menu'),
                'admin_gen_key': ("Vui lòng nhập mã thẻ (ví dụ: VIP2024):", 'admin_gen_key_step_1', 'cancel_to_admin_key_menu'),
                'admin_search_user': ("Vui lòng nhập ID hoặc Username người dùng cần tìm:", 'admin_search_step_1', 'cancel_to_admin_users_menu'),
            }
        )

        if action in admin_prompts:
            prompt, next_step, cancel_callback = admin_prompts[action]
            await start_input_flow(update, context, prompt, next_step, cancel_callback)

        elif action == 'admin_blacklist':
            from handlers.admin_commands import blacklist_command
            await blacklist_command(update, db)
        elif action == 'admin_list_keys':
            from handlers.admin_commands import listkeys_command
            await listkeys_command(update, db)
        elif action == 'admin_list_live_cc':
            from handlers.admin_commands import list_live_cc_command
            await list_live_cc_command(update, db)
        elif action == 'admin_proxy_mgmt':
            await query.edit_message_text(
                text=tr(language, "menu.proxy.message"),
                reply_markup=get_proxy_mgmt_keyboard(language),
                parse_mode='HTML'
            )
        elif action == 'admin_list_proxies':
            from handlers.admin_commands import list_proxies_admin
            await list_proxies_admin(update, context, db)
        elif action == 'admin_add_proxies':
            await start_input_flow(
                update, context,
                (
                    "📥 <b>UPLOAD NEW PROXIES</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    "Please send a <b>.txt</b> file containing the proxy list.\n"
                    "Format: <code>host:port:user:pass</code>"
                    if language == 'en' else
                    "📥 <b>NẠP PROXY MỚI</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    "Vui lòng gửi file <b>.txt</b> chứa danh sách proxy.\n"
                    "Định dạng: <code>host:port:user:pass</code>"
                ),
                'admin_add_proxies_step_1',
                'admin_proxy_mgmt'
            )
        elif action == 'admin_upload_netflix_cookies':
            from handlers.netflix_handlers import upload_netflix_cookies_command
            await upload_netflix_cookies_command(update, context, db)


# --- Text Input Handler ---
@is_not_blocked
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tất cả các tin nhắn văn bản không phải lệnh, dựa trên trạng thái."""
    next_step = context.user_data.get('action_next_step')
    if not next_step or not update.message.reply_to_message:
        return

    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_USER_ID
    language = get_current_language(context, db, user_id)

    # Thêm tin nhắn của người dùng vào danh sách dọn dẹp
    register_cleanup_message(context, update.message.message_id)

    async def cleanup_after_input(force: bool = False):
        """Dọn dẹp các tin nhắn trong luồng nhập liệu."""
        if force:
            await cleanup_input_messages(update, context, keep_data=True)
        return

        prompt_id = context.user_data.get('prompt_message_id')
        messages = context.user_data.get('messages_to_cleanup', [])

        # KỸ THUẬT KHẮC CHẾ MOBILE:
        try:
            # 1. Gỡ thuộc tính ForceReply của prompt message ngay lập tức
            if prompt_id:
                try:
                    await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=prompt_id,
                                                                reply_markup=None)
                except Exception:
                    pass

            # 2. Xóa bàn phím bằng kỹ thuật trả lời ngược (Targeted Reply)
            remove_msg = await context.bot.send_message(
                chat_id=user_id,
                text="\u2800",
                reply_markup=ReplyKeyboardRemove(selective=False),
                reply_to_message_id=prompt_id if prompt_id else None
            )
            # Chờ 0.6s
            await asyncio.sleep(0.6)

            # 3. Xóa sạch tin cũ đã đăng ký dọn dẹp
            for mid in messages:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=mid)
                except Exception:
                    pass

            # 4. Xóa nốt tin nhắn tàng hình
            await context.bot.delete_message(chat_id=user_id, message_id=remove_msg.message_id)
        except Exception:
            # Fallback
            for mid in messages:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=mid)
                except Exception:
                    pass

        context.user_data['messages_to_cleanup'] = []
        await clear_user_state(context, keep_data=True)

    # --- Luồng xác thực ---
    if next_step == 'verify_step_1':
        service_type = context.user_data.get('action_service_type')

        if service_type != 'convert_url_login_app_netflix' and not user_input.startswith('http'):
            error_msg = await update.message.reply_text(
                "Invalid link. Please try again." if language == 'en' else "Link không hợp lệ, vui lòng thử lại.",
                reply_markup=ForceReply(selective=True),
            )
            register_cleanup_message(context, error_msg.message_id)
            return

        if service_type == 'convert_url_login_app_netflix':
            await cleanup_after_input(force=True)
            await _process_netflix_cookie(update, context, db, user_input)  # Truyền db vào đây
            return

        await cleanup_after_input(force=True)

        from handlers.verify_commands import (
            verifyChatGPTTeacherK12_command, verifySpotifyStudent_command,
            verifyBoltNewTeacher_command, verifyYouTubePremiumStudent_command
        )
        verify_map = {
            'verify_chatgpt_k12': verifyChatGPTTeacherK12_command,
            'verify_spotify_student': verifySpotifyStudent_command,
            'verify_bolt_teacher': verifyBoltNewTeacher_command,
            'verify_youtube_student': verifyYouTubePremiumStudent_command,
        }

        handler = verify_map.get(service_type)
        if handler:
            context.args = [user_input]
            await handler(update, context, db)
        return

    # --- Luồng Discord Quest ---
    if next_step == 'discord_quest_step_1':
        await cleanup_after_input(force=True)
        from handlers.discord_quest_handlers import process_discord_token
        await process_discord_token(update, context, db, user_input)
        return

    # --- Luồng Check CC ---
    if next_step == 'check_cc_step_1':
        await cleanup_after_input(force=True)
        from handlers.cc_handlers import _process_cc_request
        await _process_cc_request(update, context, db, user_input)
        return

    # --- Luồng Lấy Cookie Netflix ---
    if next_step == 'admin_upload_netflix_cookies_step_1':
        if not is_admin:
            return
        await cleanup_after_input(force=True)
        from handlers.netflix_handlers import process_admin_netflix_cookie_upload
        await process_admin_netflix_cookie_upload(
            update, context, db,
            file_name="netflix.txt",
            file_bytes=user_input.encode('utf-8'),
        )
        return

    # --- Luồng Check Netflix Cookie ---
    if next_step == 'check_cookie_netflix_step_1':
        await cleanup_after_input(force=True)
        from handlers.netflix_handlers import process_netflix_cookie
        await process_netflix_cookie(update, context, db, user_input)
        return

    # --- Luồng nạp thẻ ---
    if next_step == 'use_key_step_1':
        await cleanup_after_input(force=True)
        result = db.use_card_key(user_input, user_id)
        if result is None:
            await update.message.reply_text(tr(language, "key.not_found"))
        elif isinstance(result, int) and result < 0:
            error_map = {
                -1: tr(language, "key.used_up"),
                -2: tr(language, "key.expired"),
                -3: tr(language, "key.already_used"),
            }
            await update.message.reply_text(error_map.get(result, tr(language, "common.unknown_error")))
        else:
            user = db.get_user(user_id)
            await update.message.reply_text(
                tr(language, "key.success", amount=result, balance=user['balance']))

        await show_main_menu_after_delay(update, context, db)
        return

    # --- Các luồng Admin ---
    from handlers.admin_commands import addbalance_command, block_command, white_command, genkey_command, \
        broadcast_command

    async def continue_admin_flow(prompt: str, next_step_name: str):
        """Hàm helper để tiếp tục luồng admin."""
        # await cleanup_after_input() # Không xóa ngay, để dọn dẹp một lần khi xong
        await cleanup_after_input(force=True)
        cancel_callback = 'cancel_to_admin_menu'
        if next_step_name.startswith('admin_gen_key_'):
            cancel_callback = 'cancel_to_admin_key_menu'
        await start_input_flow(update, context, prompt, next_step_name, cancel_callback)
        return

        context.user_data['action_next_step'] = next_step_name
        prompt_msg = await update.message.reply_text(prompt, reply_markup=ForceReply(selective=True))
        context.user_data['prompt_message_id'] = prompt_msg.message_id

        if 'messages_to_cleanup' not in context.user_data:
            context.user_data['messages_to_cleanup'] = []
        context.user_data['messages_to_cleanup'].append(prompt_msg.message_id)

        cancel_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Hủy", callback_data='cancel_to_admin_menu')]])
        cancel_msg = await context.bot.send_message(chat_id=user_id, text="Hoặc hủy:", reply_markup=cancel_keyboard)
        context.user_data['messages_to_cleanup'].append(cancel_msg.message_id)

    if next_step == 'admin_search_step_1':
        await cleanup_after_input(force=True)

        if user_input.isdigit():
            user_info = db.get_user(int(user_input))
        else:
            user_info = db.get_user_by_username(user_input)

        if not user_info:
            await show_admin_dashboard(
                update,
                context,
                f"❌ User not found: {user_input}" if language == 'en' else f"❌ Không tìm thấy người dùng: {user_input}",
                db=db,
            )
            return

        await handle_admin_search_result(update, context, user_info, db)
        return

    if next_step == 'admin_add_balance_step_1':
        if not user_input.isdigit():
            await update.message.reply_text(
                "User ID must be numeric. Please try again:" if language == 'en' else "User ID phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        context.user_data['admin_target_uid'] = user_input
        await continue_admin_flow(
            "Enter the number of points to add:" if language == 'en' else "Nhập số điểm cần cộng:",
            'admin_add_balance_step_2',
        )
    elif next_step == 'admin_add_balance_step_2':
        if not user_input.lstrip('-').isdigit():
            await update.message.reply_text(
                "The amount must be numeric. Please try again:" if language == 'en' else "Số điểm phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        await cleanup_after_input(force=True)
        context.args = [context.user_data.get('admin_target_uid'), user_input]
        await addbalance_command(update, context, db)
        return

    elif next_step in ['admin_block_step_1', 'admin_unblock_step_1']:
        if not user_input.isdigit():
            await update.message.reply_text(
                "User ID must be numeric. Please try again:" if language == 'en' else "User ID phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        await cleanup_after_input(force=True)
        context.args = [user_input]
        handler = block_command if next_step == 'admin_block_step_1' else white_command
        await handler(update, context, db)
        return

    elif next_step == 'admin_broadcast_step_1':
        await cleanup_after_input(force=True)
        context.args = [user_input]
        await broadcast_command(update, context, db)
        return

    elif next_step == 'admin_gen_key_step_1':
        if db.get_card_key_info(user_input):
            await cleanup_after_input(force=True)
            await show_admin_key_menu(
                update,
                context,
                (
                    f"❌ Key <b>{user_input}</b> already exists in the system!"
                    if language == 'en'
                    else f"❌ Mã thẻ <b>{user_input}</b> đã tồn tại trên hệ thống!"
                ),
                db=db,
            )
            return
        if db.get_card_key_info(user_input):
            await cleanup_after_input(force=True)
            # Quay về dashboard (admin menu) và hiện thông báo lỗi
            await show_admin_dashboard(
                update,
                context,
                (
                    f"❌ Key <b>{user_input}</b> already exists in the system!"
                    if language == 'en'
                    else f"❌ Mã thẻ <b>{user_input}</b> đã tồn tại trên hệ thống!"
                ),
                db=db,
            )
            return
        context.user_data['admin_key_code'] = user_input
        await continue_admin_flow(
            "Enter the point value for this key:" if language == 'en' else "Nhập số điểm cho mã thẻ:",
            'admin_gen_key_step_2',
        )
    elif next_step == 'admin_gen_key_step_2':
        if not user_input.isdigit():
            await update.message.reply_text(
                "The point value must be numeric. Please try again:" if language == 'en' else "Số điểm phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        context.user_data['admin_key_balance'] = user_input
        await continue_admin_flow(
            "Enter the number of uses:" if language == 'en' else "Nhập số lần sử dụng:",
            'admin_gen_key_step_3',
        )
    elif next_step == 'admin_gen_key_step_3':
        if user_input and not user_input.isdigit():
            await update.message.reply_text(
                "The number of uses must be numeric. Please try again:" if language == 'en' else "Số lần sử dụng phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        context.user_data['admin_key_uses'] = user_input if user_input else "1"
        await continue_admin_flow(
            "Enter the number of days until expiration:" if language == 'en' else "Nhập số ngày hết hạn:",
            'admin_gen_key_step_4',
        )
    elif next_step == 'admin_gen_key_step_4':
        if user_input and not user_input.isdigit():
            await update.message.reply_text(
                "The expiration days must be numeric. Please try again:" if language == 'en' else "Số ngày hết hạn phải là chữ số. Vui lòng nhập lại:",
                reply_markup=ForceReply(selective=True),
            )
            return
        await cleanup_after_input(force=True)
        args = [
            context.user_data.get('admin_key_code'),
            context.user_data.get('admin_key_balance'),
            context.user_data.get('admin_key_uses'),
            user_input if user_input else None
        ]
        context.args = [str(arg) for arg in args if arg is not None]
        logger.info(f"Đang thực hiện tạo key qua luồng phản hồi: Key={args[0]}, Points={args[1]}")
        await genkey_command(update, context, db)
        await show_admin_key_menu_after_delay(update, context, db=db)

    # [ĐOẠN NÀY ĐÃ ĐƯỢC DỌN DẸP - use_key_step_1 đã xử lý ở trên (dòng ~757)]


# --- Netflix Cookie Helper ---
async def _process_netflix_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cookie_text: str):
    """
    Validate cookie Netflix, gọi API lấy nftoken và gửi URL kết quả.
    Dùng chung cho cả luồng text và file.
    """
    # Kiểm tra bảo trì
    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'convert_url_login_app_netflix'):
        return

    user_id = update.effective_user.id
    cost = VERIFY_COST  # Sử dụng VERIFY_COST từ config
    language = get_current_language(context, db, user_id)

    # Hàm xử lý reply dựa trên update.message có tồn tại hay không
    async def reply_func(text, **kwargs):
        if update.message:
            return await update.message.reply_text(text, **kwargs)
        else:
            return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)

    # Kiểm tra số dư trước
    user_balance = db.get_user(user_id)['balance']
    if user_balance < cost:
        await reply_func(
            (
                f"❌ You do not have enough points for this feature. Need {cost}, current balance: {user_balance}."
                if language == 'en'
                else f"❌ Bạn không đủ {cost} điểm để thực hiện chức năng này. 💰 Số dư hiện tại: {user_balance} điểm."
            )
        )
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu_after_delay(
            update,
            context,
            db,
            "Insufficient balance for this feature." if language == 'en' else "Số dư không đủ để thực hiện chức năng này.",
        )
        return

    # Trừ điểm trước khi xử lý
    if not db.deduct_balance(user_id, cost):
        await reply_func("Failed to deduct points. Please try again later." if language == 'en' else "Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu_after_delay(update, context, db, "Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        return
    await reply_func(
        (
            f"Deducted {cost} points. 💰 Current balance: {db.get_user(user_id)['balance']} points. Processing your request..."
            if language == 'en'
            else f"Đã trừ {cost} điểm. 💰 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm. Đang xử lý yêu cầu..."
        )
    )

    import requests as _requests

    from netflix.cookie_utils import validate_netflix_cookie
    from netflix.nf_token_generator import generate_nftoken

    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu cookie không hợp lệ
        await reply_func(
            (
                f"{error_msg}\nRefunded {cost} points. 💰 Current balance: {db.get_user(user_id)['balance']} points."
                if language == 'en'
                else f"{error_msg}\nĐã hoàn lại {cost} điểm. 💰 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm."
            ),
            parse_mode='HTML')
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu_after_delay(update, context, db, "Invalid cookie." if language == 'en' else "Cookie không hợp lệ.")
        return

    processing_msg = await reply_func("⏳ Generating your Netflix login link..." if language == 'en' else "⏳ Đang tạo link đăng nhập Netflix...")

    try:
        result_url = generate_nftoken(cookie_text)
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception:
                pass

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_back_main_button_label(language), callback_data='back_to_main')]
        ])

        await processing_msg.edit_text(
            (
                f"✅ <b>CONVERSION SUCCESSFUL!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎬 <b>Your Netflix app login link:</b>\n"
                f"<code>{result_url}</code>\n\n"
                f"⏳ <i>This link will expire in <b>60 minutes</b>. Use it as soon as possible!</i>\n"
                f"💡 <i>Tip: Open this link on a phone that already has the Netflix app installed for automatic sign-in.</i>"
                if language == 'en'
                else f"✅ <b>CHUYỂN ĐỔI THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎬 <b>Link đăng nhập App Netflix của bạn:</b>\n"
                f"<code>{result_url}</code>\n\n"
                f"⏳ <i>Link này sẽ hết hạn sau <b>60 phút</b>. Hãy sử dụng ngay!</i>\n"
                f"💡 <i>Mẹo: Hãy nhấn vào link trên điện thoại đã cài sẵn App Netflix để đăng nhập tự động.</i>"
            ),
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except _requests.RequestException as e:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu API request thất bại
        logger.warning(f"Netflix API request failed: {e}")
        await processing_msg.edit_text(
            (
                f"❌ Could not connect to Netflix. Please try again later.\nRefunded {cost} points. 💰 Current balance: {db.get_user(user_id)['balance']} points."
                if language == 'en'
                else f"❌ Không thể kết nối tới Netflix. Vui lòng thử lại sau.\nĐã hoàn lại {cost} điểm. 💰 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm."
            )
        )
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu_after_delay(update, context, db, "Could not connect to Netflix." if language == 'en' else "Không thể kết nối tới Netflix.")
    except ValueError as e:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu có lỗi giá trị
        await processing_msg.edit_text(
            (
                f"{str(e)}\nRefunded {cost} points. 💰 Current balance: {db.get_user(user_id)['balance']} points."
                if language == 'en'
                else f"{str(e)}\nĐã hoàn lại {cost} điểm. 💰 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm."
            ),
            parse_mode='HTML')
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu_after_delay(update, context, db, "Error while generating the link." if language == 'en' else "Lỗi trong quá trình tạo link.")


# --- File Input Handler ---
@is_not_blocked
async def handle_file_input(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tin nhắn có đính kèm file khi người dùng đang ở luồng nhập liệu."""
    next_step = context.user_data.get('action_next_step')
    service_type = context.user_data.get('action_service_type')
    language = get_current_language(context, db, update.effective_user.id)

    # Cho phép xử lý file cho Netflix Checker, Check CC và Admin Proxy
    valid_steps = [
        'verify_step_1',
        'check_cc_step_1',
        'check_cookie_netflix_step_1',
        'admin_add_proxies_step_1',
        'admin_upload_netflix_cookies_step_1',
    ]
    if next_step not in valid_steps:
        return

    if next_step == 'verify_step_1' and service_type != 'convert_url_login_app_netflix':
        # Các dịch vụ verify SheerID khác không nhận file
        return

    # Nếu là callback, thêm tin nhắn hiện tại (menu) vào danh sách dọn dẹp
    query = update.callback_query
    if query:
        # Xóa ID menu cũ khỏi bộ nhớ vì nó sắp bị xóa/đè
        context.user_data['last_main_menu_id'] = None

        if 'messages_to_cleanup' not in context.user_data:
            context.user_data['messages_to_cleanup'] = []
        context.user_data['messages_to_cleanup'].append(query.message.message_id)

    document = update.message.document
    file_name = document.file_name or ""
    mime_type = document.mime_type or ""
    supports_json = (
        next_step == 'check_cookie_netflix_step_1'
        or (next_step == 'verify_step_1' and service_type == 'convert_url_login_app_netflix')
    )
    supports_zip = next_step == 'admin_upload_netflix_cookies_step_1'
    is_txt = file_name.lower().endswith('.txt') or mime_type == 'text/plain'
    is_json = file_name.lower().endswith('.json') or mime_type == 'application/json'
    is_zip = file_name.lower().endswith('.zip') or mime_type in ['application/zip', 'application/x-zip-compressed']

    if supports_zip:
        if not is_txt and not is_zip:
            await update.message.reply_text(
                "❌ Invalid file format! Only <b>.txt</b> or <b>.zip</b> files are accepted." if language == 'en' else "❌ Sai định dạng file! Chỉ chấp nhận file <b>.txt</b> hoặc <b>.zip</b>.",
                parse_mode='HTML'
            )
            return
    elif not is_txt and not (supports_json and is_json):
        await update.message.reply_text(
            (
                "❌ Invalid file format! Only <b>.txt</b>" + (" or <b>.json</b> files are accepted." if supports_json else " files are accepted.")
                if language == 'en'
                else "❌ Sai định dạng file! Chỉ chấp nhận file <b>.txt</b>" + (" hoặc <b>.json</b>." if supports_json else ".")
            ),
            parse_mode='HTML'
        )
        return

    # Đọc nội dung file .txt
    try:
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.warning(f"Không thể đọc file: {e}")
        await update.message.reply_text("❌ Unable to read the file. Please try again." if language == 'en' else "❌ Không thể đọc file, vui lòng thử lại.")
        return

    content = ""
    if not supports_zip:
        try:
            content = file_bytes.decode('utf-8').strip()
        except Exception as e:
            logger.warning(f"Khong the giai ma file: {e}")
            await update.message.reply_text("❌ Unable to read the file content. Please try again." if language == 'en' else "❌ Khong the doc noi dung file, vui long thu lai.")
            return

    if not supports_zip and not content:
        await update.message.reply_text("❌ The file is empty. Please check it again." if language == 'en' else "❌ File trống, vui lòng kiểm tra lại.")
        return

    # Dọn dẹp tin nhắn prompt và cancel
    await cleanup_input_messages(update, context, keep_data=True)
    prompt_message_id = None
    user_id = update.effective_user.id
    if prompt_message_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prompt_message_id + 1)
            await context.bot.delete_message(chat_id=user_id, message_id=prompt_message_id)
        except Exception as e:
            logger.warning(f"Lỗi khi dọn dẹp tin nhắn sau nhập file: {e}")
    await clear_user_state(context, keep_data=True)

    if next_step == 'check_cc_step_1':
        from handlers.cc_handlers import handle_cc_file_input
        await handle_cc_file_input(update, context, db, content)
    elif next_step == 'admin_add_proxies_step_1':
        from handlers.admin_commands import handle_proxy_file_upload
        await handle_proxy_file_upload(update, context, db, content)
    elif next_step == 'admin_upload_netflix_cookies_step_1':
        from handlers.netflix_handlers import process_admin_netflix_cookie_upload
        await process_admin_netflix_cookie_upload(update, context, db, file_name, bytes(file_bytes))
    elif next_step == 'check_cookie_netflix_step_1':
        from handlers.netflix_handlers import process_netflix_cookie
        await process_netflix_cookie(update, context, db, content)
    else:
        # Mặc định cũ cho convert Netflix URL
        await _process_netflix_cookie(update, context, db, content)


async def handle_admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE, user_info: dict, db: Optional[Database] = None):
    """Hiển thị thông tin chi tiết và bảng điều khiển cho tìm kiếm Admin."""
    chat_id = update.effective_chat.id
    target_id = user_info['user_id']
    language = get_current_language(context, db, update.effective_user.id if update.effective_user else None)
    username = f"@{user_info['username']}" if user_info['username'] else ("None" if language == 'en' else "Không có")
    status = "🚫 Blocked" if user_info['is_blocked'] and language == 'en' else "🚫 Đang bị chặn" if user_info['is_blocked'] else "✅ Normal" if language == 'en' else "✅ Bình thường"
    language_label = {
        'en': 'English',
        'vi': 'Tiếng Việt',
    }.get((user_info.get('language') or '').lower(), "Not set" if language == 'en' else "Chưa chọn")

    text = (
        f"👤 <b>{'User information' if language == 'en' else 'Thông tin người dùng'}:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"👤 {'Name' if language == 'en' else 'Tên'}: {user_info['full_name']}\n"
        f"🔗 Username: {username}\n"
        f"🌐 {'Language' if language == 'en' else 'Ngôn ngữ'}: {language_label}\n"
        f"💰 {'Balance' if language == 'en' else 'Số dư'}: <b>{user_info['balance']} {'points' if language == 'en' else 'điểm'}</b>\n"
        f"🚩 {'Status' if language == 'en' else 'Trạng thái'}: {status}\n"
        f"📅 {'Joined' if language == 'en' else 'Tham gia'}: {user_info['created_at'][:10]}\n"
    )

    # Tạo bàn phím điều khiển nhanh
    keyboard = []

    # Hàng 1: Chặn/Bỏ chặn
    if user_info['is_blocked']:
        keyboard.append([InlineKeyboardButton("✅ Unblock" if language == 'en' else "✅ Bỏ chặn", callback_data=f"admin_q_unblock:{target_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Block user" if language == 'en' else "🚫 Chặn người dùng", callback_data=f"admin_q_block:{target_id}")])

    # Hàng 2: Cộng điểm nhanh
    keyboard.append([
        InlineKeyboardButton("+10 💰", callback_data=f"admin_q_add:{target_id}:10"),
        InlineKeyboardButton("+50 💰", callback_data=f"admin_q_add:{target_id}:50"),
        InlineKeyboardButton("+100 💰", callback_data=f"admin_q_add:{target_id}:100")
    ])

    # Hàng 3: Quay lại
    keyboard.append([InlineKeyboardButton(get_back_admin_button_label(language), callback_data="admin_menu")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
