import asyncio
import logging
from config import ADMIN_USER_ID
from database_mysql import Database
from utils.proxy_helper import check_proxy_health

logger = logging.getLogger(__name__)

async def run_proxy_cleanup_job(app, db: Database):
    """
    Quét toàn bộ database và loại bỏ các proxy không hoạt động.
    """
    logger.info("🚀 Đang khởi động tiến trình quét sạch proxy chết...")
    
    try:
        proxies = db.get_all_proxies()
        if not proxies:
            logger.info("ℹ️ Không có proxy nào trong database để kiểm tra.")
            return

        dead_count = 0
        total_count = len(proxies)
        
        # Chúng ta sẽ kiểm tra tuần tự để không làm quá tải hệ thống nếu có quá nhiều proxy
        # Hoặc dùng asyncio.Semaphore nếu muốn nhanh hơn
        
        for idx, proxy in enumerate(proxies):
            address = proxy.get('address')
            port = proxy.get('port')
            
            logger.debug(f"[{idx+1}/{total_count}] Đang kiểm tra proxy {address}:{port}...")
            
            is_alive = await check_proxy_health(proxy)
            
            if not is_alive:
                logger.info(f"❌ Proxy {address}:{port} đã chết. Đang xóa khỏi database...")
                db.delete_proxy(proxy['id'])
                dead_count += 1
        
        logger.info(f"✅ Hoàn tất dọn dẹp proxy. Tổng cộng: {total_count}, Đã xóa: {dead_count}, Còn lại: {total_count - dead_count}")
        
        # Thông báo cho Admin nếu hết sạch proxy
        if total_count > 0 and (total_count - dead_count) == 0:
            try:
                alert_msg = (
                    "⚠️ <b>CẢNH BÁO HỆ THỐNG</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "Tất cả proxy trong database đã dừng hoạt động và bị xóa.\n\n"
                    "🚀 Vui lòng nạp thêm proxy mới để các dịch vụ (Netflix, v.v.) hoạt động bình thường!"
                )
                await app.bot.send_message(chat_id=ADMIN_USER_ID, text=alert_msg, parse_mode='HTML')
                logger.warning("📢 Đã gửi thông báo hết sạch proxy tới Admin.")
            except Exception as se:
                logger.error(f"Không thể gửi thông báo tới Admin: {se}")
        
    except Exception as e:
        logger.error(f"⚠️ Lỗi xảy ra trong quá trình chạy proxy cleanup job: {e}")

async def start_proxy_cleanup_loop(app, db: Database, interval: int = 3600):
    """
    Vòng lặp vô hạn chạy ngầm để dọn dẹp proxy định kỳ.
    Mặc định: 1 giờ (3600 giây)
    """
    logger.info(f"🕒 Bắt đầu khởi chạy vòng lặp kiểm tra proxy định kỳ ({interval}s/lần)")
    
    while True:
        await run_proxy_cleanup_job(app, db)
        await asyncio.sleep(interval)
