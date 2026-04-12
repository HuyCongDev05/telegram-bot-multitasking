import asyncio
import logging
import httpx
from config import ADMIN_USER_ID, WEBSHARE_TOKEN
from database_mysql import Database
from utils.proxy_helper import check_proxy_health

logger = logging.getLogger(__name__)

async def fetch_webshare_proxies(app, db: Database):
    """
    Gọi Webshare API để lấy danh sách proxy mới và lưu vào database.
    Nếu có lỗi sẽ báo ngay cho Admin.
    """
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=10&plan_id=13162825"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Token {WEBSHARE_TOKEN}"
    }
    
    logger.info("📡 Đang gửi yêu cầu lấy proxy từ Webshare...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"❌ <b>LỖI WEBSHARE API</b>\nStatus code: {response.status_code}\nResponse: {response.text[:200]}"
                await app.bot.send_message(chat_id=ADMIN_USER_ID, text=error_msg, parse_mode='HTML')
                logger.error(f"Webshare API returned {response.status_code}: {response.text}")
                return False

            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning("⚠️ Webshare API trả về danh sách trống.")
                return True

            added_count = 0
            for p in results:
                address = p.get("proxy_address")
                port = p.get("port")
                username = p.get("username")
                password = p.get("password")
                city = p.get("city_name")
                country = p.get("country_code")
                
                if db.add_proxy(address, port, username, password, city, country):
                    added_count += 1
            
            logger.info(f"✅ Đã nạp thành công {added_count}/{len(results)} proxy từ Webshare.")
            return True

    except Exception as e:
        error_msg = f"⚠️ <b>LỖI HỆ THỐNG (PROXY UPDATE)</b>\n━━━━━━━━━━━━━━━━━━━━\nChi tiết: <code>{str(e)}</code>"
        try:
            await app.bot.send_message(chat_id=ADMIN_USER_ID, text=error_msg, parse_mode='HTML')
        except Exception as se:
            logger.error(f"Không thể gửi thông báo lỗi tới Admin: {se}")
        
        logger.error(f"Lỗi khi fetch proxy từ Webshare: {e}")
        return False

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
        
        for idx, proxy in enumerate(proxies):
            address = proxy.get('address')
            port = proxy.get('port')
            
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
            except Exception as se:
                logger.error(f"Không thể gửi thông báo tới Admin: {se}")
        
    except Exception as e:
        logger.error(f"⚠️ Lỗi xảy ra trong quá trình chạy proxy cleanup job: {e}")

async def start_proxy_management_loop(app, db: Database, interval: int = 3600):
    """
    Vòng lặp quản lý proxy:
    1. Lấy proxy mới từ Webshare
    2. Dọn dẹp proxy chết
    Mặc định: 1 giờ (3600 giây)
    """
    logger.info(f"🕒 Bắt đầu khởi chạy vòng lặp quản lý proxy định kỳ ({interval}s/lần)")
    
    while True:
        # 1. Dọn dẹp các proxy chết hiện có trong database trước
        await run_proxy_cleanup_job(app, db)
        
        # 2. Sau đó mới nạp thêm proxy mới từ Webshare
        await fetch_webshare_proxies(app, db)
        
        await asyncio.sleep(interval)
