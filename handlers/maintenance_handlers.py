import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.i18n import DEFAULT_LANGUAGE, get_user_language, tr
from utils.messages import get_maintenance_keyboard, get_service_display_name

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"


async def admin_maintenance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    # Hiển thị menu quản lý bảo trì cho Admin
    query = update.callback_query
    await query.answer()
    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    services_status = db.get_all_service_status()
    keyboard = get_maintenance_keyboard(services_status, language)

    await query.edit_message_text(
        tr(language, "maintenance.menu"),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    # Đảo ngược trạng thái bảo trì và gửi thông báo
    query = update.callback_query
    await query.answer()
    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)

    # Lấy service_id từ callback_data (toggle_m:service_id)
    service_id = query.data.split(':')[-1]

    # Mapping tên dịch vụ để thông báo
    service_name = get_service_display_name(service_id, language)

    # Tên dịch vụ cho thông báo
    new_status = db.toggle_service_maintenance(service_id)

    if new_status is None:
        await query.message.reply_text(tr(language, "maintenance.error_service"))
        return

    # Chuẩn bị tin nhắn thông báo
    if new_status:
        broadcast_key = "maintenance.notice.on"
    else:
        broadcast_key = "maintenance.notice.off"

    # Cập nhật lại giao diện người dùng ngay lập tức
    services_status = db.get_all_service_status()
    keyboard = get_maintenance_keyboard(services_status, language)
    await query.edit_message_reply_markup(reply_markup=keyboard)

    await query.message.reply_text(
        tr(language, broadcast_key, service_name=service_name),
        parse_mode='HTML',
    )

    # Gửi thông báo cho toàn bộ người dùng (Chạy ngầm để không chặn luồng)
    asyncio.create_task(broadcast_maintenance_notice(context, db, service_id, new_status))

async def broadcast_maintenance_notice(context, db, service_id: str, is_maintenance: bool):
    # Gửi thông báo bảo trì cho toàn bộ user (có delay)
    user_ids = db.get_all_user_ids()
    success_count = 0

    for user_id in user_ids:
        try:
            language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
            service_name = get_service_display_name(service_id, language)
            message = tr(
                language,
                "maintenance.notice.on" if is_maintenance else "maintenance.notice.off",
                service_name=service_name,
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue

    logger.info(f"Đã gửi thông báo bảo trì tới {success_count}/{len(user_ids)} người dùng.")

# Bỏ qua các callback noop
async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
