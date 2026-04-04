import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.messages import get_maintenance_keyboard

logger = logging.getLogger(__name__)

async def admin_maintenance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Hiển thị menu quản lý bảo trì cho Admin"""
    query = update.callback_query
    await query.answer()
    
    services_status = db.get_all_service_status()
    keyboard = get_maintenance_keyboard(services_status)
    
    await query.edit_message_text(
        "🛠 <b>QUẢN LÝ BẢO TRÌ DỊCH VỤ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Bạn có thể bật hoặc tắt trạng thái bảo trì cho từng dịch vụ bên dưới.\n"
        "<i>Lưu ý: Hệ thống sẽ tự động gửi thông báo cho toàn bộ người dùng khi thay đổi.</i>",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Đảo ngược trạng thái bảo trì và gửi thông báo"""
    query = update.callback_query
    await query.answer()
    
    # Lấy service_id từ callback_data (toggle_m:service_id)
    service_id = query.data.split(':')[-1]
    
    # Mapping tên dịch vụ để thông báo
    mapping = {
        'verify_chatgpt_k12': '🎓 ChatGPT Teacher K12',
        'verify_spotify_student': '🎵 Spotify Student',
        'verify_bolt_teacher': '⚡ Bolt.new Teacher',
        'verify_youtube_student': '🎥 YouTube Premium',
        'verify_gemini_pro': '🤖 Gemini One Pro',
        'convert_url_login_app_netflix': '🎬 Chuyển đổi Netflix',
        'check_cc': '💳 Check CC',
        'discord_quest_auto': '🚀 Discord Quest Auto'
    }
    service_name = mapping.get(service_id, service_id)
    
    # Tên dịch vụ cho thông báo
    new_status = db.toggle_service_maintenance(service_id)
    
    if new_status is None:
        await query.message.reply_text("❌ Lỗi: Không biên dịch được dịch vụ.")
        return

    # Chuẩn bị tin nhắn thông báo
    if new_status:
        # BẬT bảo trì
        broadcast_msg = (
            f"🛠 <b>THÔNG BÁO BẢO TRÌ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Dịch vụ <b>{service_name}</b> hiện đang được tạm dừng để <b>bảo trì hệ thống</b>.\n\n"
            f"🕒 Chúng tôi sẽ có thông báo ngay khi dịch vụ hoạt động trở lại. Xin lỗi vì sự bất tiện này!"
        )
    else:
        # TẮT bảo trì
        broadcast_msg = (
            f"✅ <b>THÔNG BÁO HOÀN TẤT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Dịch vụ <b>{service_name}</b> đã hoàn tất bảo trì và <b>hoạt động trở lại</b> bình thường.\n\n"
            f"🚀 Bạn có thể tiếp tục sử dụng dịch vụ ngay bây giờ. Cảm ơn bạn!"
        )

    # Cập nhật lại giao diện người dùng ngay lập tức
    services_status = db.get_all_service_status()
    keyboard = get_maintenance_keyboard(services_status)
    await query.edit_message_reply_markup(reply_markup=keyboard)

    # Gửi thông báo cho toàn bộ người dùng (Chạy ngầm để không chặn luồng)
    asyncio.create_task(broadcast_maintenance_notice(context, db, broadcast_msg))

async def broadcast_maintenance_notice(context, db, message):
    """Gửi thông báo bảo trì cho toàn bộ user (có delay)"""
    user_ids = db.get_all_user_ids()
    success_count = 0
    
    for user_id in user_ids:
        try:
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
