import asyncio
import logging

import httpx

from config import ADMIN_USER_ID, WEBSHARE_TOKEN
from database_mysql import Database
from utils.proxy_helper import check_proxy_health

logger = logging.getLogger(__name__)

async def fetch_webshare_proxies(db: Database):
    """
    Gọi Webshare API để lấy danh sách proxy mới và lưu vào database.
    Không gửi tin nhắn cho Admin ở đây để tránh spam.
    """
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100&plan_id=13162825"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Token {WEBSHARE_TOKEN.strip()}"
    }
    
    logger.info("📡 Đang gửi yêu cầu lấy proxy từ Webshare...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Webshare API returned {response.status_code}: {response.text}")
                return False

            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning("⚠️ Webshare API trả về danh sách trống.")
                return False

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
            return added_count > 0

    except Exception as e:
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
        
        logger.info(f"✅ Hoàn tất dọn dẹp proxy. Tổng cộng: {total_count}, Đã xóa: {dead_count}, Còn lại: {total_count - dead_count}")
        
    except Exception as e:
        logger.error(f"⚠️ Lỗi xảy ra trong quá trình chạy proxy cleanup job: {e}")

async def start_proxy_management_loop(app, db: Database, interval: int = 3600):
    """
    Vòng lặp quản lý proxy định kỳ.
    1. Xóa proxy chết.
    2. Thử nạp proxy mới (thử lại 3 lần).
    """
    logger.info(f"🕒 Bắt đầu khởi chạy vòng lặp quản lý proxy ({interval}s/lần)")
    
    while True:
        # 1. Xóa sạch các proxy chết trong database trước
        await run_proxy_cleanup_job(app, db)
        
        # 2. Thử nạp thêm proxy mới từ Webshare
        success = False
        for attempt in range(1, 4):
            logger.info(f"🔄 Đang thử nạp proxy từ Webshare (Lần {attempt}/3)...")
            if await fetch_webshare_proxies(db):
                success = True
                break
            
            if attempt < 3:
                # Nếu thất bại, đợi 10 giây trước khi thử lại
                await asyncio.sleep(10)
        
        # 3. Chỉ cảnh báo Admin nếu THỰC SỰ hết sạch proxy sau khi đã thử 3 lần
        try:
            remaining_proxies = db.get_all_proxies()
            if not remaining_proxies:
                alert_msg = (
                    "⚠️ <b>CẢNH BÁO HỆ THỐNG</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "Đã thử nạp proxy 3 lần nhưng <b>KHÔNG THÀNH CÔNG</b> và database đang trống sạch.\n\n"
                    "🚀 Vui lòng kiểm tra lại tài khoản Webshare hoặc nạp thủ công!"
                )
                await app.bot.send_message(chat_id=ADMIN_USER_ID, text=alert_msg, parse_mode='HTML')
                logger.warning("📢 Đã gửi thông báo HẾT SẠCH PROXY tới Admin sau 3 lần thử thất bại.")
        except Exception as ae:
            logger.error(f"Lỗi khi gửi cảnh báo cuối chu kỳ: {ae}")

        await asyncio.sleep(interval)
