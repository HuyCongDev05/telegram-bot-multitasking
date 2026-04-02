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

    final_message_parts.append(f"🪙 Số dư của bạn: {balance} điểm.")
    final_message_parts.append("Vui lòng chọn một chức năng:")

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


async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database,
                               message_text: str = ""):
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


# --- Command Handlers ---
@is_not_blocked
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /start, hiển thị menu chính."""
    user = update.effective_user
    user_id = user.id

    if not db.user_exists(user_id):
        username = user.username or ""
        full_name = user.full_name or ""
        invited_by: Optional[int] = None
        if context.args:
            try:
                invited_by_id = int(context.args[0])
                if db.user_exists(invited_by_id):
                    invited_by = invited_by_id
            except (IndexError, ValueError):
                pass

        db.create_user(user_id, username, full_name, invited_by)
        greeting_message = get_welcome_message(full_name, bool(invited_by))
    else:
        greeting_message = f"Chào mừng {user.full_name} quay trở lại!"

    await show_main_menu(update, context, db, message_text=greeting_message)


@is_not_blocked
async def help_command(update: Update):
    """Xử lý lệnh /help"""
    await update.message.reply_text(get_help_message())


@is_not_blocked
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý tất cả các sự kiện bấm nút."""
    query = update.callback_query
    await query.answer()

    action = query.data
    user_id = query.from_user.id
    is_admin = user_id == ADMIN_USER_ID

    async def cleanup_input_messages():
        """Xóa tất cả tin nhắn trong luồng nhập liệu hiện tại."""
        messages = context.user_data.get('messages_to_cleanup', [])
        for mid in messages:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=mid)
            except Exception:
                pass
        context.user_data['messages_to_cleanup'] = []
        await clear_user_state(context)

    # --- Điều hướng Menu ---
    if action == 'back_to_main':
        await show_main_menu(update, context, db)
        return

    if action == 'cancel_to_main':
        await cleanup_input_messages()
        await show_main_menu(update, context, db)  # Không truyền message_text
        return

    if action == 'cancel_to_verify_menu':
        await cleanup_input_messages()
        await clear_user_state(context)
        await context.bot.send_message(chat_id=user_id, text=get_verify_menu_message(),
                                       reply_markup=get_verify_keyboard())
        return

    if action == 'cancel_to_admin_menu':
        await cleanup_input_messages()
        await clear_user_state(context)
        await context.bot.send_message(chat_id=user_id, text=get_admin_menu_message(),
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
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"
        await query.message.reply_text(
            f"🎁 Link mời của bạn:\n{invite_link}\n\nMời thành công 1 người bạn sẽ nhận được 1 điểm.")
    elif action == 'checkin':
        if db.checkin(user_id):
            user = db.get_user(user_id)
            await query.message.reply_text(f"✅ Điểm danh thành công! +1 điểm\n🪙 Số dư hiện tại: {user['balance']} điểm.")
        else:
            await query.message.reply_text("❌ Hôm nay bạn đã điểm danh rồi.")

    # --- Bắt đầu các luồng nhập liệu ---
    async def start_input_flow(prompt_text: str, next_step: str, cancel_callback: str):
        """Hàm helper để bắt đầu một luồng nhập liệu."""
        context.user_data['action_next_step'] = next_step

        # Khởi tạo danh sách tin nhắn cần dọn dẹp
        if 'messages_to_cleanup' not in context.user_data:
            context.user_data['messages_to_cleanup'] = []

        # Thêm tin nhắn hiện tại (menu) vào danh sách dọn dẹp (nếu là bướt đầu tiên)
        if query.message.message_id not in context.user_data['messages_to_cleanup']:
            context.user_data['messages_to_cleanup'].append(query.message.message_id)

        prompt_msg = await context.bot.send_message(chat_id=user_id, text=prompt_text,
                                                    reply_markup=ForceReply(selective=True))
        context.user_data['prompt_message_id'] = prompt_msg.message_id
        context.user_data['messages_to_cleanup'].append(prompt_msg.message_id)

        cancel_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Hủy", callback_data=cancel_callback)]])
        cancel_msg = await context.bot.send_message(chat_id=user_id, text="Hoặc nhấn nút bên dưới để hủy:",
                                                    reply_markup=cancel_keyboard)
        context.user_data['messages_to_cleanup'].append(cancel_msg.message_id)

    if action == 'to_up':
        await start_input_flow("Vui lòng nhập mã thẻ:", 'use_key_step_1', 'cancel_to_main')

    elif action == 'convert_url_login_app_netflix':
        context.user_data['action_service_type'] = action
        await start_input_flow(
            f"Bạn đã chọn: 📺 Chuyển đổi url login app netflix.\nVui lòng nhập cookie netflix vào tin nhắn trả lời bên dưới hoặc gửi file .txt\n Lưu ý: Mỗi lần xác thực thành công sẽ tốn {VERIFY_COST} điểm.",
            'verify_step_1', 'cancel_to_main')

    elif action.startswith('verify_'):
        service_map = {
            'verify_chatgpt_k12': "ChatGPT Teacher K12", 'verify_spotify_student': "Spotify Student",
            'verify_bolt_teacher': "Bolt.new Teacher", 'verify_youtube_student': "YouTube Student",
            'verify_gemini_pro': "Gemini One Pro"
        }
        service_name = service_map.get(action)
        if service_name:
            context.user_data['action_service_type'] = action
            await start_input_flow(f"Bạn đã chọn: {service_name}.\nVui lòng gửi liên kết xác thực:", 'verify_step_1',
                                   'cancel_to_verify_menu')

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
            await start_input_flow(prompt, next_step, 'cancel_to_admin_menu')

        elif action == 'admin_blacklist':
            from handlers.admin_commands import blacklist_command
            await blacklist_command(update, context, db)
        elif action == 'admin_list_keys':
            from handlers.admin_commands import listkeys_command
            await listkeys_command(update, context, db)


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
    if 'messages_to_cleanup' not in context.user_data:
        context.user_data['messages_to_cleanup'] = []
    context.user_data['messages_to_cleanup'].append(update.message.message_id)

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
            await update.message.reply_text("Link không hợp lệ, vui lòng thử lại.",
                                            reply_markup=ForceReply(selective=True))
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
                                       reply_markup=get_welcome_keyboard(is_admin))
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
        await show_admin_dashboard(update, context, db, "Thao tác hoàn tất.")

    elif next_step in ['admin_block_step_1', 'admin_unblock_step_1']:
        if not user_input.isdigit():
            await update.message.reply_text("User ID phải là chữ số. Vui lòng nhập lại:",
                                            reply_markup=ForceReply(selective=True))
            return
        await cleanup_after_input(force=True)
        context.args = [user_input]
        handler = block_command if next_step == 'admin_block_step_1' else white_command
        await handler(update, context, db)
        await show_admin_dashboard(update, context, db, "Thao tác hoàn tất.")

    elif next_step == 'admin_broadcast_step_1':
        await cleanup_after_input(force=True)
        context.args = [user_input]
        await broadcast_command(update, context, db)
        await show_admin_dashboard(update, context, db, "Thao tác hoàn tất.")

    elif next_step == 'admin_gen_key_step_1':
        if db.get_card_key_info(user_input):
            await cleanup_after_input(force=True)
            # Quay về dashboard (admin menu) và hiện thông báo lỗi
            await show_admin_dashboard(update, context, db, f"❌ Mã thẻ <b>{user_input}</b> đã tồn tại trên hệ thống!")
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
            await show_admin_dashboard(update, context, db, "✅ Đã tạo mã thẻ thành công.")
        else:
            await show_admin_dashboard(update, context, db, "❌ Tạo mã thẻ thất bại. Vui lòng kiểm tra lại thông tin.")


# --- Netflix Cookie Helper ---
async def _process_netflix_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cookie_text: str):
    """
    Validate cookie Netflix, gọi API lấy nftoken và gửi URL kết quả.
    Dùng chung cho cả luồng text và file.
    """
    user_id = update.effective_user.id
    cost = VERIFY_COST  # Sử dụng VERIFY_COST từ config

    # Kiểm tra số dư trước
    user_balance = db.get_user(user_id)['balance']
    if user_balance < cost:
        await update.message.reply_text(
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
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return
    await update.message.reply_text(
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
        await update.message.reply_text(
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

    processing_msg = await update.message.reply_text("⏳ Đang tạo link đăng nhập Netflix...")

    try:
        url = generate_nftoken(cookie_text)
        # Xóa tin nhắn gốc của người dùng chứa cookie
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa cookie (ID: {update.message.message_id}): {e}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Quay lại trang chủ", callback_data='back_to_main')]
        ])
        await processing_msg.edit_text(
            f"✅ Tạo link thành công!\n\n"
            f"Link đăng nhập Netflix của bạn đã được tạo. Vui lòng sử dụng link này để đăng nhập.\n\n"
            f"<code>{url}</code>",  # Vẫn hiển thị URL để người dùng có thể sao chép
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

    # Chỉ xử lý khi đang ở bước verify và service là netflix
    if next_step != 'verify_step_1' or service_type != 'convert_url_login_app_netflix':
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

    await _process_netflix_cookie(update, context, db, content)  # Truyền db vào đây
