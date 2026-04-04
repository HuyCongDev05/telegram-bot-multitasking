"""Công cụ kiểm tra và xác thực quyền hạn"""
import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import CHANNEL_USERNAME

logger = logging.getLogger(__name__)


def is_group_chat(update: Update) -> bool:
    """Kiểm tra xem có phải là trò chuyện nhóm không"""
    chat = update.effective_chat
    return chat and chat.type in ("group", "supergroup")


async def reject_group_command(update: Update) -> bool:
    """Hạn chế nhóm: Yêu cầu người dùng nhắn tin riêng cho Bot"""
    if is_group_chat(update):
        if update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ <b>Bot không hỗ trợ xử lý trong Nhóm.</b>\n\n"
                "Vui lòng nhấn vào @{bot_username} để nhắn tin riêng (Inbox) và sử dụng đầy đủ các tính năng xác thực, nạp điểm, v.v.".format(
                    bot_username=update.get_bot().username
                ),
                parse_mode='HTML'
            )
        return True
    return False


async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Kiểm tra xem người dùng đã tham gia kênh chưa"""
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError as e:
        logger.error("Kiểm tra thành viên kênh thất bại: %s", e)
        return False


def is_not_blocked(func):
    """Decorator để kiểm tra xem người dùng có bị chặn không"""
    from functools import wraps

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Lấy db từ kwargs hoặc args
        db = kwargs.get('db')
        if not db:
            for arg in args:
                if hasattr(arg, 'get_user'):  # Giả định đây là đối tượng Database
                    db = arg
                    break

        if not db:
            # Nếu không tìm thấy db trong args/kwargs, thử lấy từ context nếu có (tùy cách thiết kế)
            return await func(update, context, *args, **kwargs)

        user_id = update.effective_user.id
        if db.is_user_blocked(user_id):
            if update.effective_message:
                # Trả lời tin nhắn hoặc sửa tin nhắn callback
                if update.callback_query:
                    await update.callback_query.answer("Tài khoản của bạn đã bị khóa.", show_alert=True)
                    await update.effective_message.edit_text(
                        "🚫 Tài khoản của bạn đã bị khóa. Liên hệ @hcongdev để biết thêm.")
                else:
                    await update.effective_message.reply_text(
                        "🚫 Tài khoản của bạn đã bị khóa. Liên hệ @hcongdev để biết thêm.")
            return None

        return await func(update, context, *args, **kwargs)
    return wrapper


async def check_maintenance(update: Update, db, service_id: str) -> bool:
    """Kiểm tra dịch vụ có đang bảo trì không và thông báo cho người dùng"""
    if db.is_service_maintenance(service_id):
        msg = "🛠 <b>DỊCH VỤ ĐANG BẢO TRÌ</b>\n━━━━━━━━━━━━━━━━━━━━\nHiện tại tính năng này đang được bảo trì để nâng cấp. Vui lòng quay lại sau ít phút!"
        if update.callback_query:
            await update.callback_query.answer()  # Phản hồi nhẹ để tắt biểu tượng load trên nút
            await update.effective_message.reply_text(msg, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(msg, parse_mode='HTML')
        return True
    return False
