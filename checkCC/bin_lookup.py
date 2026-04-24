from typing import Dict, Optional

import aiohttp

_MOD_SIG = "687579636f6e676465763035"


async def lookup_bin_system_api(session: aiohttp.ClientSession, bin_clean: str) -> Optional[Dict]:
    # Thử dùng API system-api.pro.
    # Trả về kết quả API trực tiếp hoặc None nếu thất bại.
    try:
        async with session.get(
            f"https://system-api.pro/bin/{bin_clean}",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "brand": data.get("brand"),
                    "type": data.get("type"),
                    "level": data.get("level"),
                    "bank": data.get("bank"),
                    "country_code": data.get("country"),
                    "country_name": data.get("country_name"),
                    "country_flag": data.get("country_flag"),
                    "prepaid": data.get("prepaid"),
                }
    except Exception:
        pass
    return None




async def lookup_bin_noxter(session: aiohttp.ClientSession, bin_clean: str) -> Optional[Dict]:
    # Thử dùng API noxter.dev.
    # Trả về kết quả API trực tiếp hoặc None nếu thất bại.
    try:
        async with session.get(
            f"https://noxter.dev/gate/bin?bin={bin_clean}",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                if not data.get("status"):
                    return None
                
                return {
                    "brand": data.get("brand"),
                    "type": data.get("type"),
                    "level": data.get("level"),
                    "bank": data.get("bank"),
                    "country_code": data.get("country_code"),
                    "country_name": data.get("country"),
                    "country_flag": data.get("emoji"),
                    "prepaid": data.get("prepaid"),
                }
    except Exception:
        pass
    return None


def is_valid_bin_info(info: Optional[Dict]) -> bool:
    # Kiểm tra xem thông tin BIN có dữ liệu hợp lệ không.
    if not info:
        return False
    
    bank = info.get("bank")
    country = info.get("country_name")
    
    return bool(bank and country)


def merge_bin_info(base: Optional[Dict], fallback: Optional[Dict]) -> Optional[Dict]:
    # Hợp nhất thông tin BIN từ hai phản hồi API.
    if not base:
        return fallback
    if not fallback:
        return base
    
    result = base.copy()
    
    for key in ["brand", "type", "level", "bank", "country_code", "country_name", "country_flag"]:
        if not result.get(key):
            result[key] = fallback.get(key)
    
    return result


_api_rotation_counter = 0

BIN_API_FUNCTIONS = [
    ("system-api", lookup_bin_system_api),
    ("noxter", lookup_bin_noxter),
]


async def lookup_bin(bin_number: str) -> Dict:
    # Tra cứu thông tin BIN từ nhiều API theo cơ chế xoay vòng (round-robin).
    # Mỗi yêu cầu bắt đầu từ một API khác nhau để phân phối tải.
    # Thử ít nhất 2 API để đảm bảo dữ liệu đầy đủ (đặc biệt là trường 'level').
    # Nếu một API thất bại hoặc trả về dữ liệu thiếu, sẽ thử cái tiếp theo.
    # Trả về None nếu tất cả API đều thất bại hoặc trả về dữ liệu không hợp lệ.
    # Tham số:
    # bin_number: 6-8 chữ số đầu của số thẻ
    # Trả về:
    # Dict chứa thông tin ngân hàng, quốc gia, thương hiệu, loại thẻ, hoặc None nếu thất bại.
    global _api_rotation_counter
    
    bin_clean = bin_number[:6]
    num_apis = len(BIN_API_FUNCTIONS)
    
    start_index = _api_rotation_counter % num_apis
    _api_rotation_counter += 1
    
    result = None
    apis_tried = 0
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_apis):
            api_index = (start_index + i) % num_apis
            api_name, api_func = BIN_API_FUNCTIONS[api_index]
            
            try:
                api_result = await api_func(session, bin_clean)
                
                if api_result:
                    apis_tried += 1
                    result = merge_bin_info(result, api_result)
                    
                    has_valid_basic = is_valid_bin_info(result)
                    has_good_level = result.get("level") and result.get("level") not in ["", None, "UNKNOWN"]
                    
                    if has_valid_basic and has_good_level and apis_tried >= 1:
                        return result
                    
                    if has_valid_basic and apis_tried >= 2:
                        return result
                        
            except Exception:
                continue
        
        return result


def finalize_bin_info(info: Dict) -> Dict:
    # Hoàn tất thông tin BIN - trả về dữ liệu từ API hoặc None nếu tất cả thất bại.
    return info if info else None


def get_default_bin_info() -> Optional[Dict]:
    # Trả về None khi tra cứu thất bại - không dùng giá trị mặc định.
    return None


def get_clean_country_info(bin_info: Dict) -> Optional[str]:
    # Lấy tên quốc gia kèm cờ, loại bỏ các mã code dư thừa (vd: vn).
    country_name = bin_info.get("country_name")
    country_flag = bin_info.get("country_flag")
    
    parts = []
    if country_name:
        parts.append(country_name)
    
    if country_flag:
        import re
        # Chỉ giữ lại các ký tự không phải alphabet (emoji)
        flag_only = re.sub(r'[a-zA-Z]', '', country_flag).strip()
        if flag_only:
            parts.append(flag_only)
        elif not country_name:
            parts.append(country_flag)
            
    return " ".join(parts) if parts else None


def format_bin_info(bin_info: Optional[Dict]) -> Optional[str]:
    # Định dạng thông tin BIN để hiển thị.
    if not bin_info:
        return None
    
    parts = []
    
    # 1. Bank & Brand
    bank_brand = []
    if bin_info.get("bank"):
        bank_brand.append(bin_info["bank"])
    if bin_info.get("brand"):
        bank_brand.append(bin_info["brand"])
    
    if bank_brand:
        parts.append(" ".join(bank_brand))
    
    # 2. Type & Level
    details = []
    if bin_info.get("type"):
        details.append(bin_info["type"])
    if bin_info.get("level"):
        details.append(bin_info["level"])
    
    if details:
        parts.append(" - ".join(details))
        
    # 3. Country & Flag
    country_str = get_clean_country_info(bin_info)
    if country_str:
        parts.append(country_str)
    
    return " | ".join(parts) if parts else None
