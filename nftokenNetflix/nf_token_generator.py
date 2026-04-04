import json

# Internal build sign ID
_BUILD_SIG = "687579636f6e676465763035"
import re

import requests

# Điểm cuối GraphQL của Netflix được sử dụng bởi ứng dụng di động để yêu cầu token đăng nhập tự động.
API_URL = "https://android13.prod.ftl.netflix.com/graphql"

HEADERS = {
    "User-Agent": "com.netflix.mediaclient/63884 (Linux; U; Android 13; ro; M2007J3SG; Build/TQ1A.230205.001.A2; Cronet/143.0.7445.0)",
    "Accept": "multipart/mixed;deferSpec=20220824, application/graphql-response+json, application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.netflix.com",
    "Referer": "https://www.netflix.com/",
}
PAYLOAD = {
    "operationName": "CreateAutoLoginToken",
    "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"},
    "extensions": {
        "persistedQuery": {
            "version": 102,
            "id": "76e97129-f4b5-41a0-a73c-12e674896849",
        }
    },
}

# Các giá trị cookie cốt lõi bắt buộc phải có
REQUIRED_COOKIES = ("NetflixId", "SecureNetflixId")


def extract_cookie_dict(text: str) -> dict:
    """
    Chuẩn hóa bất kỳ nội dung nào thành một dict cookie.
    Hỗ trợ: định dạng JSON (list hoặc dict), Netscape, bảng (tab-separated từ devtools), hoặc chuỗi cookie thô.
    """
    cookie_dict = {}

    # 1. Thử định dạng JSON trước (ví dụ: xuất từ EditThisCookie là một list các dict)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    cookie_dict[item['name']] = str(item['value'])
            if cookie_dict:
                return cookie_dict
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    cookie_dict[key] = str(value)
            if cookie_dict:
                return cookie_dict
    except json.JSONDecodeError:
        pass  # Không phải JSON, tiếp tục xử lý dưới dạng văn bản

    # 2. Xử lý chuỗi cookie thô (ví dụ: key1=value1; key2=value2;)
    for match in re.finditer(r'([a-zA-Z0-9_.-]+)=([^;\s]+)', text):
        cookie_dict[match.group(1)] = match.group(2)

    # 3. Xử lý định dạng bảng phân tách bằng khoảng trắng/tab (Netscape hoặc DevTools)
    # Vì Telegram đôi khi biến dấu Tab thành khoảng trắng, nên việc cắt theo cột rất dễ lỗi.
    # Giải pháp: Cắt toàn bộ văn bản bằng khoảng trắng, tìm từ khóa đã biết, giá trị của nó sẽ nằm ngay sát sau!
    tokens = text.split()
    known_keys = {
        "NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent", 
        "OptanonAlertBoxClosed", "gsid", "dsca", "OTSessionTracking", 
        "memclid", "netflix-sans-bold-3-loaded", "netflix-sans-normal-3-loaded"
    }
    
    for i, token in enumerate(tokens):
        if token in known_keys:
            if i + 1 < len(tokens):
                # Đảm bảo giá trị tiếp theo không phải là một từ khóa khác (tránh lỗi lấy nhầm)
                if tokens[i+1] not in known_keys:
                    cookie_dict[token] = tokens[i+1]

    return cookie_dict


def validate_netflix_cookie(text: str) -> tuple:
    """
    Kiểm tra xem text có chứa cookie Netflix hợp lệ không.
    Trả về (True, "") nếu hợp lệ, hoặc (False, thông báo lỗi) nếu không.
    """
    if not text or not text.strip():
        return False, "Nội dung cookie trống."

    cookie_dict = extract_cookie_dict(text.strip())
    missing = [name for name in REQUIRED_COOKIES if not cookie_dict.get(name)]

    if missing:
        return (
            False,
            f"❌ Cookie thiếu các trường cốt lõi bắt buộc: <code>{', '.join(missing)}</code>\n\n"
            f"Đảm bảo bạn đã copy đủ thông tin chứa ít nhất:\n"
            f"• <code>NetflixId</code>\n"
            f"• <code>SecureNetflixId</code>",
        )

    return True, ""


def build_cookie_header(cookie_dict):
    """Chuyển dict cookie thành chuỗi Cookie header."""
    return "; ".join(f"{key}={value}" for key, value in cookie_dict.items())


def build_nftoken_link(token):
    """Tạo URL đăng nhập Netflix từ token."""
    return "https://netflix.com/?nftoken=" + token


def fetch_nftoken(cookie_dict):
    """
    Gửi yêu cầu tới Netflix API để lấy auto-login token.
    Raise ValueError nếu thất bại.
    """
    missing = [name for name in REQUIRED_COOKIES if not cookie_dict.get(name)]
    if missing:
        raise ValueError("Thiếu các cookie bắt buộc: " + ", ".join(missing))

    headers = dict(HEADERS)
    headers["Cookie"] = build_cookie_header(cookie_dict)

    response = requests.post(API_URL, headers=headers, json=PAYLOAD, timeout=30)
    response.raise_for_status()

    data = response.json()
    data_block = data.get("data") or {}
    token = data_block.get("createAutoLoginToken")
    if token:
        return token

    errors = data.get("errors")
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=True))

    raise ValueError("Không tìm thấy token trong phản hồi.")


def generate_nftoken(cookie_text: str) -> str:
    """
    Hàm chính để bot gọi.
    Nhận chuỗi cookie (từ text hoặc file .txt), validate, gọi API và trả về URL đăng nhập.
    Raise ValueError với thông báo lỗi thân thiện nếu thất bại.
    """
    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        raise ValueError(error_msg)

    cookie_dict = extract_cookie_dict(cookie_text.strip())
    token = fetch_nftoken(cookie_dict)
    return build_nftoken_link(token)
