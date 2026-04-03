"""Trình xử lý lệnh người dùng"""
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from config import VERIFY_COST
from database_mysql import Database
from utils.checks import is_not_blocked
from utils.messages import (
    get_welcome_message,
    get_welcome_keyboard,
    get_help_message,
    get_verify_menu_message,
    get_verify_keyboard,
    get_admin_menu_message,
    get_admin_keyboard,
)

logger = logging.getLogger(__name__)


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


async def cleanup_input_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xóa tất cả tin nhắn trong luồng nhập liệu hiện tại."""
    chat_id = update.effective_chat.id
    messages = context.user_data.get('messages_to_cleanup', [])
    for mid in messages:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            pass
    context.user_data['messages_to_cleanup'] = []
    await clear_user_state(context)


def get_active_service_name(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Lấy tên tiếng Việt của dịch vụ đang thực hiện."""
    service_type = context.user_data.get('action_service_type')
    next_step = context.user_data.get('action_next_step')

    mapping = {
        'verify_chatgpt_k12': 'Xác thực ChatGPT Teacher K12',
        'verify_spotify_student': 'Xác thực Spotify Student',
        'verify_bolt_teacher': 'Xác thực Bolt.new Teacher',
        'verify_youtube_student': 'Xác thực YouTube Student',
        'verify_gemini_pro': 'Xác thực Gemini One Pro',
        'convert_url_login_app_netflix': 'Chuyển đổi Netflix',
        'check_cc_step_1': 'Check CC',
        'use_key_step_1': 'Nạp mã Key (Nạp điểm)',
        'admin_add_balance_step_1': 'Admin: Cộng điểm',
        'admin_block_user_step_1': 'Admin: Chặn người dùng',
        'admin_gen_key_step_1': 'Admin: Tạo mã Key',
    }

    # Ưu tiên service_type, sau đó đến next_step
    if service_type in mapping:
        return mapping[service_type]
    if next_step in mapping:
        return mapping[next_step]

    return "một chức năng khác"


async def is_user_busy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Kiểm tra xem người dùng có đang trong một luồng thực hiện nào không."""
    next_step = context.user_data.get('action_next_step')
    if not next_step:
        return False

    # Nếu là lệnh /start, cho phép bỏ qua để reset
    if update.message and update.message.text == '/start':
        await cleanup_input_messages(update, context)
        return False

    service_name = get_active_service_name(context)
    message_text = (
        f"⚠️ <b>Bạn đang thực hiện chức năng: {service_name}</b>\n\n"
        f"Vui lòng hoàn thành hoặc nhấn nút <b>❌ Hủy</b> của chức năng đó trước khi bắt đầu hành động mới."
    )

    if update.callback_query:
        await update.callback_query.answer(text=f"Vui lòng Hủy chức năng {service_name} trước!", show_alert=True)
    else:
        await update.message.reply_text(message_text, parse_mode='HTML')

    return True


@is_not_blocked
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, message_text: str = ""):
    """Hiển thị menu chính và xóa trạng thái."""
    await clear_user_state(context)

    query = update.callback_query
    user = update.effective_user
    is_admin = user.id == ADMIN_USER_ID

    user_data = db.get_user(user.id)
    balance = user_data['balance'] if user_data else 0

    final_message_parts = []
    if message_text:
        final_message_parts.append(message_text)

    final_message_parts.append(f"<b>🤖 HỆ THỐNG BOT VERIFY</b>")
    final_message_parts.append(f"🪙 Số dư: <b>{balance} điểm</b>")
    final_message_parts.append("━━━━━━━━━━━━━━━━━━━━\n"
                               "✨ <i>Vui lòng chọn chức năng:</i>")

    final_message_text = "\n\n".join(final_message_parts)

    keyboard = get_welcome_keyboard(is_admin)

    if query:
        try:
            await query.edit_message_text(text=final_message_text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=user.id, text=final_message_text, reply_markup=keyboard,
                                               parse_mode='HTML')
            except Exception as e:
                logger.warning(f"Không thể gửi menu chính: {e}")
    else:
        await update.message.reply_text(text=final_message_text, reply_markup=keyboard, parse_mode='HTML')


async def start_input_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt_text: str, next_step: str,
                           cancel_callback: str):
    """Hàm helper để bắt đầu một luồng nhập liệu, hỗ trợ cả Message và CallbackQuery."""
    chat_id = update.effective_chat.id
    query = update.callback_query

    context.user_data['action_next_step'] = next_step

    # Nếu là callback, thêm tin nhắn hiện tại (menu) vào danh sách dọn dẹp
    if query:
        register_cleanup_message(context, query.message.message_id)

    prompt_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=prompt_text,
        reply_markup=ForceReply(selective=True),
        parse_mode='HTML'
    )
    register_cleanup_message(context, prompt_msg.message_id)

    cancel_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Hủy", callback_data=cancel_callback)]])
    cancel_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="Hoặc nhấn nút bên dưới để hủy:",
        reply_markup=cancel_keyboard
    )
    register_cleanup_message(context, cancel_msg.message_id)


async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = ""):
    """Hiển thị menu quản trị (dashboard) và xóa trạng thái."""
    await clear_user_state(context)
    user_id = update.effective_user.id

    final_text = get_admin_menu_message()
    if message_text:
        final_text = f"{message_text}\n\n{final_text}"

    await context.bot.send_message(
        chat_id=user_id,
        text=final_text,
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )


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
    if await is_user_busy(update, context):
        return

    user = update.effective_user
    user_id = user.id

    # BẮT BUỘC CÓ USERNAME
    if not user.username:
        await send_or_reply(update, context,
                            "⚠️ <b>Lỗi: Không có Username</b>\n\n"
                            "Tài khoản Telegram của bạn chưa thiết lập <b>Username</b>. "
                            "Để sử dụng Bot này, bạn cần vào mục Settings (Cài đặt) của Telegram để đặt Username, "
                            "sau đó quay lại đây bấm /start.\n\n"
                            "<i>(Lưu ý: Username giúp Bot định danh và bảo vệ tài khoản của bạn tốt hơn)</i>",
                            parse_mode='HTML'
                            )
        return

    username = user.username
    full_name = user.full_name or ""

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
        greeting_message = get_welcome_message(full_name, bool(invited_by))
    else:
        # Cập nhật thông tin mới nhất (đề phòng đổi username/fullname)
        # Chỗ này database_mysql.py chưa có hàm update_user, nhưng có thể bỏ qua hoặc bổ sung sau.
        greeting_message = f"Chào mừng {user.full_name} quay trở lại!"

    await show_main_menu(update, context, db, message_text=greeting_message)


@is_not_blocked
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /invite"""
    user_id = update.effective_user.id
    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"
    await send_or_reply(update, context,
                        f"🪙 Link mời của bạn:\n{invite_link}\n\nMời thành công 1 người bạn sẽ nhận được 1 điểm.")


@is_not_blocked
async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /checkin"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id
    if db.checkin(user_id):
        user = db.get_user(user_id)
        await send_or_reply(update, context,
                            f"✅ Điểm danh thành công! +1 điểm\n🪙 Số dư hiện tại: {user['balance']} điểm.")
    else:
        await send_or_reply(update, context, "❌ Hôm nay bạn đã điểm danh rồi.")


@is_not_blocked
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /balance"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    balance = user_data['balance'] if user_data else 0
    await send_or_reply(update, context, f"🪙 Số dư hiện tại của bạn: {balance} điểm.")


@is_not_blocked
async def to_up_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /to_up"""
    if await is_user_busy(update, context):
        return

    if context.args:
        # Xử lý trực tiếp nếu có đối số
        user_id = update.effective_user.id
        user_input = context.args[0].strip()
        result = db.use_card_key(user_input, user_id)
        if result is None:
            await send_or_reply(update, context, "Mã thẻ không tồn tại.")
        elif isinstance(result, int) and result < 0:
            error_map = {-1: "Mã đã hết lượt sử dụng.", -2: "Mã đã hết hạn.", -3: "Bạn đã dùng mã này rồi."}
            await send_or_reply(update, context, error_map.get(result, "Lỗi không xác định."))
        else:
            user = db.get_user(user_id)
            await send_or_reply(update, context,
                                f"Sử dụng mã thẻ thành công! +{result} điểm.\n🪙 Số dư hiện tại: {user['balance']} điểm.")
        return

    await start_input_flow(update, context, "Vui lòng nhập mã thẻ:", 'use_key_step_1', 'cancel_to_main')


@is_not_blocked
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /help"""
    if await is_user_busy(update, context):
        return

    await send_or_reply(update, context, get_help_message(), parse_mode='HTML')


@is_not_blocked
async def convertNetflixUrl_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /convertNetflixUrl"""
    if await is_user_busy(update, context):
        return

    # KHI NGƯỜI DÙNG GÕ LỆNH KÈM THEO ĐỐI SỐ
    if context.args:
        cookie_text = " ".join(context.args)
        await _process_netflix_cookie(update, context, db, cookie_text)
        return

    context.user_data['action_service_type'] = 'convert_url_login_app_netflix'

    prompt_text = (
        f"🪙 <b>Chuyển đổi Netflix</b>\n\n"
        f"Vui lòng nhập cookie netflix vào tin nhắn trả lời bên dưới hoặc gửi file .txt\n"
        f"Lưu ý: Mỗi lần xác thực thành công sẽ tốn 🪙 {VERIFY_COST} điểm."
    )

    await start_input_flow(update, context, prompt_text, 'verify_step_1', 'cancel_to_main')


@is_not_blocked
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tất cả các sự kiện bấm nút."""
    query = update.callback_query
    await query.answer()

    action = query.data
    user_id = query.from_user.id
    is_admin = user_id == ADMIN_USER_ID

    # Chặn spam: Nếu đang trong luồng nhập liệu, chỉ cho phép các nút Hủy/Quay lại hoạt động
    allowed_actions = ['cancel_to_main', 'cancel_to_verify_menu', 'cancel_to_admin_menu', 'back_to_main']
    if action not in allowed_actions:
        if await is_user_busy(update, context):
            return

    # --- Logic quản trị nhanh (Quick Admin) ---
    if action.startswith('admin_q_'):
        if not is_admin: return
        parts = action.split(':')
        cmd = parts[0]
        target_id = int(parts[1])

        if cmd == 'admin_q_block':
            db.block_user(target_id)
            await query.answer("Đã chặn người dùng!", show_alert=True)
        elif cmd == 'admin_q_unblock':
            db.unblock_user(target_id)
            await query.answer("Đã bỏ chặn người dùng!", show_alert=True)
        elif cmd == 'admin_q_add':
            amount = int(parts[2])
            db.add_balance(target_id, amount)
            await query.answer(f"Đã cộng {amount} điểm!", show_alert=True)

        # Quay lại profile người dùng để cập nhật thông tin
        user_info = db.get_user(target_id)
        if user_info:
            from handlers.admin_commands import handle_admin_search_result
            await handle_admin_search_result(update, context, user_info)
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_verify_menu_message(),
                                       reply_markup=get_verify_keyboard())
        return

    if action == 'cancel_to_admin_menu':
        await cleanup_input_messages(update, context)
        await clear_user_state(context)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_admin_menu_message(),
                                       reply_markup=get_admin_keyboard())
        return

    if action == 'verify_menu':
        await query.edit_message_text(text=get_verify_menu_message(), reply_markup=get_verify_keyboard())
        return

    if action == 'admin_menu':
        if not is_admin: return
        await query.edit_message_text(text=get_admin_menu_message(), reply_markup=get_admin_keyboard())
        return

    # --- Chức năng người dùng ---
    if action == 'help':
        await query.message.reply_text(get_help_message())
    elif action == 'invite':
        await invite_command(update, context)
    elif action == 'checkin':
        await checkin_command(update, context, db)
    elif action == 'check_cc_menu':
        from handlers.cc_handlers import checkCC_command
        await checkCC_command(update, context, db)
        return

    if action == 'to_up':
        await to_up_command(update, context, db)

    elif action == 'convert_url_login_app_netflix':
        await convertNetflixUrl_command(update, context, db)

    elif action.startswith('verify_'):
        service_map = {
            'verify_chatgpt_k12': "ChatGPT Teacher K12", 'verify_spotify_student': "Spotify Student",
            'verify_bolt_teacher': "Bolt.new Teacher", 'verify_youtube_student': "YouTube Student",
            'verify_gemini_pro': "Gemini One Pro"
        }
        service_name = service_map.get(action)
        if service_name:
            context.user_data['action_service_type'] = action
            from utils.messages import get_verify_usage_message
            prompt = get_verify_usage_message(service_name)
            await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')

    elif action.startswith('admin_'):
        if not is_admin: return

        admin_prompts = {
            'admin_add_balance': ("Vui lòng nhập ID người dùng cần cộng điểm:", 'admin_add_balance_step_1'),
            'admin_block': ("Vui lòng nhập ID người dùng cần chặn:", 'admin_block_step_1'),
            'admin_unblock': ("Vui lòng nhập ID người dùng cần bỏ chặn:", 'admin_unblock_step_1'),
            'admin_broadcast': ("Vui lòng nhập nội dung thông báo muốn gửi:", 'admin_broadcast_step_1'),
            'admin_gen_key': ("Vui lòng nhập mã thẻ (ví dụ: VIP2024):", 'admin_gen_key_step_1'),
        }

        if action in admin_prompts:
            prompt, next_step = admin_prompts[action]
            await start_input_flow(update, context, prompt, next_step, 'cancel_to_admin_menu')

        elif action == 'admin_blacklist':
            from handlers.admin_commands import blacklist_command
            await blacklist_command(update, db)
        elif action == 'admin_list_keys':
            from handlers.admin_commands import listkeys_command
            await listkeys_command(update, db)
        elif action == 'admin_list_live_cc':
            from handlers.admin_commands import list_live_cc_command
            await list_live_cc_command(update, db)


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

    # Thêm tin nhắn của người dùng vào danh sách dọn dẹp
    register_cleanup_message(context, update.message.message_id)

    async def cleanup_after_input(force: bool = False):
        """Dọn dẹp các tin nhắn trong luồng nhập liệu."""
        if not force:
            return

        messages = context.user_data.get('messages_to_cleanup', [])
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
            error_msg = await update.message.reply_text("Link không hợp lệ, vui lòng thử lại.",
                                            reply_markup=ForceReply(selective=True))
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

    # --- Luồng Check CC ---
    if next_step == 'check_cc_step_1':
        await cleanup_after_input(force=True)
        from handlers.cc_handlers import _process_cc_request
        await _process_cc_request(update, context, db, user_input)
        return

    # --- Luồng nạp thẻ ---
    if next_step == 'use_key_step_1':
        await cleanup_after_input(force=True)
        result = db.use_card_key(user_input, user_id)
        if result is None:
            await update.message.reply_text("Mã thẻ không tồn tại.")
        elif isinstance(result, int) and result < 0:
            error_map = {-1: "Mã đã hết lượt sử dụng.", -2: "Mã đã hết hạn.", -3: "Bạn đã dùng mã này rồi."}
            await update.message.reply_text(error_map.get(result, "Lỗi không xác định."))
        else:
            user = db.get_user(user_id)
            await update.message.reply_text(
                f"Sử dụng mã thẻ thành công! +{result} điểm.\n🪙 Số dư hiện tại: {user['balance']} điểm.")

        await context.bot.send_message(chat_id=user_id, text="Đã quay về menu chính.",
                                       reply_markup=get_welcome_keyboard())
        return

    # --- Các luồng Admin ---
    from handlers.admin_commands import addbalance_command, block_command, white_command, genkey_command, \
        broadcast_command

    async def continue_admin_flow(prompt: str, next_step_name: str):
        """Hàm helper để tiếp tục luồng admin."""
        # await cleanup_after_input() # Không xóa ngay, để dọn dẹp một lần khi xong
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
            await show_admin_dashboard(update, context, f"❌ Không tìm thấy người dùng: {user_input}")
            return

        await handle_admin_search_result(update, context, user_info)
        return

    if next_step == 'admin_add_balance_step_1':
        if not user_input.isdigit():
            await update.message.reply_text("User ID phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        context.user_data['admin_target_uid'] = user_input
        await continue_admin_flow("Nhập số điểm cần cộng:", 'admin_add_balance_step_2')
    elif next_step == 'admin_add_balance_step_2':
        if not user_input.lstrip('-').isdigit():
            await update.message.reply_text("Số điểm phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        await cleanup_after_input(force=True)
        context.args = [context.user_data.get('admin_target_uid'), user_input]
        await addbalance_command(update, context, db)
        await show_admin_dashboard(update, context, "Thao tác hoàn tất.")

    elif next_step in ['admin_block_step_1', 'admin_unblock_step_1']:
        if not user_input.isdigit():
            await update.message.reply_text("User ID phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        await cleanup_after_input(force=True)
        context.args = [user_input]
        handler = block_command if next_step == 'admin_block_step_1' else white_command
        await handler(update, context, db)
        await show_admin_dashboard(update, context, "Thao tác hoàn tất.")

    elif next_step == 'admin_broadcast_step_1':
        await cleanup_after_input(force=True)
        context.args = [user_input]
        await broadcast_command(update, context, db)
        await show_admin_dashboard(update, context, "Thao tác hoàn tất.")

    elif next_step == 'admin_gen_key_step_1':
        if db.get_card_key_info(user_input):
            await cleanup_after_input(force=True)
            # Quay về dashboard (admin menu) và hiện thông báo lỗi
            await show_admin_dashboard(update, context, f"❌ Mã thẻ <b>{user_input}</b> đã tồn tại trên hệ thống!")
            return
        context.user_data['admin_key_code'] = user_input
        await continue_admin_flow("Nhập số điểm cho mã thẻ:", 'admin_gen_key_step_2')
    elif next_step == 'admin_gen_key_step_2':
        if not user_input.isdigit():
            await update.message.reply_text("Số điểm phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        context.user_data['admin_key_balance'] = user_input
        await continue_admin_flow("Nhập số lần sử dụng:", 'admin_gen_key_step_3')
    elif next_step == 'admin_gen_key_step_3':
        if user_input and not user_input.isdigit():
            await update.message.reply_text("Số lần sử dụng phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        context.user_data['admin_key_uses'] = user_input if user_input else "1"
        await continue_admin_flow("Nhập số ngày hết hạn:", 'admin_gen_key_step_4')
    elif next_step == 'admin_gen_key_step_4':
        if user_input and not user_input.isdigit():
            await update.message.reply_text("Số ngày hết hạn phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
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
        success = await genkey_command(update, context, db)
        if success:
            await show_admin_dashboard(update, context, "✅ Đã tạo mã thẻ thành công.")
        else:
            await show_admin_dashboard(update, context, "❌ Tạo mã thẻ thất bại. Vui lòng kiểm tra lại thông tin.")

    # --- Luồng nạp thẻ ---
    if next_step == 'use_key_step_1':
        await cleanup_after_input(force=True)
        result = db.use_card_key(user_input, user_id)
        if result is None:
            await update.message.reply_text("Mã thẻ không tồn tại.")
        elif isinstance(result, int) and result < 0:
            error_map = {-1: "Mã đã hết lượt sử dụng.", -2: "Mã đã hết hạn.", -3: "Bạn đã dùng mã này rồi."}
            await update.message.reply_text(error_map.get(result, "Lỗi không xác định."))
        else:
            user = db.get_user(user_id)
            await update.message.reply_text(
                f"Sử dụng mã thẻ thành công! +{result} điểm.\n🪙 Số dư hiện tại: {user['balance']} điểm.")

        await context.bot.send_message(chat_id=user_id, text="Đã quay về menu chính.",
                                       reply_markup=get_welcome_keyboard())
        return


# --- Netflix Cookie Helper ---
async def _process_netflix_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cookie_text: str):
    """
    Validate cookie Netflix, gọi API lấy nftoken và gửi URL kết quả.
    Dùng chung cho cả luồng text và file.
    """
    user_id = update.effective_user.id
    cost = VERIFY_COST  # Sử dụng VERIFY_COST từ config

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
            f"❌ Bạn không đủ {cost} điểm để thực hiện chức năng này. 🪙 Số dư hiện tại: {user_balance} điểm.")
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Số dư không đủ để thực hiện chức năng này.")
        return

    # Trừ điểm trước khi xử lý
    if not db.deduct_balance(user_id, cost):
        await reply_func("Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return
    await reply_func(
        f"Đã trừ {cost} điểm. 🪙 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm. Đang xử lý yêu cầu...")

    import requests as _requests
    import importlib.util
    import sys
    from pathlib import Path

    # Phải dùng importlib vì tên file có dấu gạch ngang (nf-token-generator.py)
    module_path = Path("nftokenNetflix/nf_token_generator.py").resolve()
    spec = importlib.util.spec_from_file_location("nf_token_generator", module_path)
    nf_gen = importlib.util.module_from_spec(spec)
    sys.modules["nf_token_generator"] = nf_gen
    spec.loader.exec_module(nf_gen)

    generate_nftoken = nf_gen.generate_nftoken
    validate_netflix_cookie = nf_gen.validate_netflix_cookie

    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu cookie không hợp lệ
        await reply_func(
            f"{error_msg}\nĐã hoàn lại {cost} điểm. 🪙 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm.",
            parse_mode='HTML')
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Cookie không hợp lệ.")
        return

    processing_msg = await reply_func("⏳ Đang tạo link đăng nhập Netflix...")

    try:
        generate_nftoken(cookie_text)
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Quay lại trang chủ", callback_data='back_to_main')]
        ])
        if result["success"]:
            await processing_msg.edit_text(
                f"✅ <b>Xác thực THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 Chúc mừng, dịch vụ ChatGPT K12 của bạn đã được kích hoạt.\n\n"
                f"📩 {result.get('message', 'Vui lòng kiểm tra email của bạn.')}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await processing_msg.edit_text(
                f"❌ <b>Xác thực THẤT BẠI!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🧐 Lý do: {result.get('message', 'Yêu cầu không được phê duyệt.')}\n\n"
                f"💡 <i>Vui lòng kiểm tra lại thông পাশ SheerID và thử lại.</i>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
    except _requests.RequestException as e:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu API request thất bại
        logger.warning(f"Netflix API request failed: {e}")
        await processing_msg.edit_text(
            f"❌ Không thể kết nối tới Netflix. Vui lòng thử lại sau.\nĐã hoàn lại {cost} điểm. 🪙 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm.")
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Không thể kết nối tới Netflix.")
    except ValueError as e:
        db.add_balance(user_id, cost)  # Hoàn lại điểm nếu có lỗi giá trị
        await processing_msg.edit_text(
            f"{str(e)}\nĐã hoàn lại {cost} điểm. 🪙 Số dư hiện tại: {db.get_user(user_id)['balance']} điểm.",
            parse_mode='HTML')
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Lỗi trong quá trình tạo link.")


# --- File Input Handler ---
@is_not_blocked
async def handle_file_input(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tin nhắn có đính kèm file khi người dùng đang ở luồng nhập liệu."""
    next_step = context.user_data.get('action_next_step')
    service_type = context.user_data.get('action_service_type')

    # Chỉ xử lý khi đang ở bước verify và service là netflix, HOẶC đang ở bước check_cc
    if (
            next_step == 'verify_step_1' and service_type == 'convert_url_login_app_netflix') or next_step == 'check_cc_step_1':
        pass
    else:
        return

    # Thêm tin nhắn của người dùng vào danh sách dọn dẹp
    if 'messages_to_cleanup' not in context.user_data:
        context.user_data['messages_to_cleanup'] = []
    context.user_data['messages_to_cleanup'].append(update.message.message_id)

    document = update.message.document
    # Kiểm tra định dạng file: phải là .txt hoặc mime text/plain
    is_txt = (
            (document.file_name and document.file_name.lower().endswith('.txt'))
            or document.mime_type == 'text/plain'
    )

    if not is_txt:
        await update.message.reply_text(
            "❌ Sai định dạng file! Chỉ chấp nhận file <b>.txt</b>.",
            parse_mode='HTML'
        )
        return

    # Đọc nội dung file .txt
    try:
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
        content = file_bytes.decode('utf-8').strip()
    except Exception as e:
        logger.warning(f"Không thể đọc file: {e}")
        await update.message.reply_text("❌ Không thể đọc file, vui lòng thử lại.")
        return

    if not content:
        await update.message.reply_text("❌ File trống, vui lòng kiểm tra lại.")
        return

    # Dọn dẹp tin nhắn prompt và cancel
    prompt_message_id = context.user_data.get('prompt_message_id')
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
    else:
        await _process_netflix_cookie(update, context, db, content)  # Truyền db vào đây


async def handle_admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE, user_info: dict):
    """Hiển thị thông tin chi tiết và bảng điều khiển cho tìm kiếm Admin."""
    chat_id = update.effective_chat.id
    target_id = user_info['user_id']
    username = f"@{user_info['username']}" if user_info['username'] else "Không có"
    status = "🚫 Đang bị chặn" if user_info['is_blocked'] else "✅ Bình thường"

    text = (
        f"👤 <b>Thông tin người dùng:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"👤 Tên: {user_info['full_name']}\n"
        f"🔗 Username: {username}\n"
        f"🪙 Số dư: <b>{user_info['balance']} điểm</b>\n"
        f"🚩 Trạng thái: {status}\n"
        f"📅 Tham gia: {user_info['created_at'][:10]}\n"
    )

    # Tạo bàn phím điều khiển nhanh
    keyboard = []

    # Hàng 1: Chặn/Bỏ chặn
    if user_info['is_blocked']:
        keyboard.append([InlineKeyboardButton("✅ Bỏ chặn", callback_data=f"admin_q_unblock:{target_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Chặn người dùng", callback_data=f"admin_q_block:{target_id}")])

    # Hàng 2: Cộng điểm nhanh
    keyboard.append([
        InlineKeyboardButton("+10 🪙", callback_data=f"admin_q_add:{target_id}:10"),
        InlineKeyboardButton("+50 🪙", callback_data=f"admin_q_add:{target_id}:50"),
        InlineKeyboardButton("+100 🪙", callback_data=f"admin_q_add:{target_id}:100")
    ])

    # Hàng 3: Quay lại
    keyboard.append([InlineKeyboardButton("⬅️ Quay lại Menu Admin", callback_data="admin_menu")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
