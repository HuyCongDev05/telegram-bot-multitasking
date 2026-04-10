"""Công cụ kiểm tra và xác thực quyền hạn"""
import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import CHANNEL_USERNAME
from utils.i18n import DEFAULT_LANGUAGE, get_user_language, has_selected_language, tr

logger = logging.getLogger(__name__)
    return chat and chat.type in ("group", "supergroup")


async def reject_group_command(update: Update, db=None) -> bool:
    """Hạn chế nhóm: Yêu cầu người dùng nhắn tin riêng cho Bot"""
    language = DEFAULT_LANGUAGE
    if db and update.effective_user:
        language = get_user_language(db, update.effective_user.id)

    if is_group_chat(update):
        if update.effective_message:
            await update.effective_message.reply_text(
                tr(language, "checks.group", bot_username=update.get_bot().username),
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

    async def ensure_language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, db, user: dict | None) -> bool:
        """Yêu cầu chọn ngôn ngữ trước khi tiếp tục sử dụng bot."""
        if not update.effective_user:
            return False

        if update.callback_query and (update.callback_query.data or "").startswith("select_language:"):
            return False

        if not user:
            return False

        if has_selected_language(user.get("language")):
            return False

        if update.message and update.message.text == '/start':
            context.user_data['pending_welcome_back_after_language'] = True

        from handlers.user_commands import show_language_selection

        await show_language_selection(update, context, db)
        return True

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
        user = db.get_user(user_id) if hasattr(db, 'get_user') else None
        language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

        if user and user["is_blocked"] == 1:
            if update.effective_message:
                # Trả lời tin nhắn hoặc sửa tin nhắn callback
                if update.callback_query:
                    await update.callback_query.answer(tr(language, "checks.blocked.alert"), show_alert=True)
                    await update.effective_message.edit_text(
                        tr(language, "checks.blocked"),
                    )
                else:
                    await update.effective_message.reply_text(
                        tr(language, "checks.blocked"),
                    )
            return None

        if await ensure_language_selected(update, context, db, user):
            return None

        return await func(update, context, *args, **kwargs)
    return wrapper


async def check_maintenance(update: Update, db, service_id: str) -> bool:
    """Kiểm tra dịch vụ có đang bảo trì không và thông báo cho người dùng"""
    if db.is_service_maintenance(service_id):
        language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
        msg = tr(language, "checks.maintenance")
        if update.callback_query:
            await update.callback_query.answer()  # Phản hồi nhẹ để tắt biểu tượng load trên nút
            await update.effective_message.reply_text(msg, parse_mode='HTML')
        else:
            await update.effective_message.reply_text(msg, parse_mode='HTML')
        return True
    return False
