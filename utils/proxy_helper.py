import requests
import httpx
import logging

logger = logging.getLogger(__name__)

def get_proxy_geoip(address, port, username=None, password=None, timeout=10):
    # Sử dụng proxy để gọi API GeoIP và lấy thông tin vị trí.
    # Đồng thời kiểm tra xem proxy có hoạt động không.
    proxy_url = f"http://{address}:{port}"
    if username and password:
        proxy_url = f"http://{username}:{password}@{address}:{port}"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    try:
        # Sử dụng dịch vụ ip-api.com (miễn phí, không cần key cho HTTP)
        response = requests.get("http://ip-api.com/json", proxies=proxies, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            return {
                "success": True,
                "city": data.get("city"),
                "country": data.get("country"),
                "countryCode": data.get("countryCode"),
                "ip": data.get("query")
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
            
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra GeoIP cho proxy {address}:{port}: {e}")
        return {"success": False, "error": str(e)}

def format_proxy_url(proxy_dict):
    # Chuyển đổi dict proxy từ DB sang chuỗi URL cho requests
    if not proxy_dict:
        return None
        
    address = proxy_dict.get('address')
    port = proxy_dict.get('port')
    user = proxy_dict.get('username')
    passwd = proxy_dict.get('password')
    
    if user and passwd:
        return f"http://{user}:{passwd}@{address}:{port}"
    return f"http://{address}:{port}"

async def check_proxy_health(proxy_dict: dict, timeout: int = 5) -> bool:
    # Kiểm tra xem proxy còn hoạt động hay không (async).
    # Thử kết nối tới một dịch vụ nhẹ để xác minh.
    proxy_url = format_proxy_url(proxy_dict)
    
    # httpx require proxy URL to be specified per-protocol in a dict or as a string for all
    proxies = {
        "http://": proxy_url,
        "https://": proxy_url,
    }
    
    try:
        async with httpx.AsyncClient(proxies=proxies, timeout=timeout) as client:
            # Kiểm tra tới một URL tin cậy và nhẹ
            response = await client.get("http://www.google.com", follow_redirects=True)
            return response.status_code == 200
    except Exception:
        return False
