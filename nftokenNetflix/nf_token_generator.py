import json
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

# Các giá trị cookie tối thiểu cần thiết để Netflix chấp nhận yêu cầu tạo token.
REQUIRED_COOKIES = ("NetflixId", "SecureNetflixId", "nfvdid")


def extract_cookie_dict(text: str) -> dict:
    """
    Chuẩn hóa bất kỳ nội dung nào thành một dict cookie.
    Hỗ trợ: định dạng Netscape, JSON, hoặc chuỗi cookie thô.
    """
    cookie_dict = {}

    # Thử định dạng JSON trước
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in (*REQUIRED_COOKIES, "OptanonConsent"):
                if key in data and isinstance(data[key], str):
                    cookie_dict[key] = data[key]
            if any(name in cookie_dict for name in REQUIRED_COOKIES):
                return cookie_dict
    except json.JSONDecodeError:
        pass  # Không phải JSON, tiếp tục thử các định dạng khác

    # Thử định dạng chuỗi cookie (key=value;) hoặc Netscape
    # Sử dụng regex để tìm các cặp key=value hoặc các trường trong định dạng Netscape
    for key in (*REQUIRED_COOKIES, "OptanonConsent"):
        # Regex cho key=value;
        match = re.search(rf'{re.escape(key)}=([^;]+)', text)
        if match:
            cookie_dict[key] = match.group(1).strip()
            continue

        # Regex cho định dạng Netscape (tìm key ở cột 5 và value ở cột 6)
        # Ví dụ: .netflix.com	TRUE	/	TRUE	...	NetflixId	...
        match = re.search(rf'(\s|^){re.escape(key)}\s+([^\s]+)', text)
        if match:
            cookie_dict[key] = match.group(2).strip()

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
            f"❌ Cookie thiếu các trường bắt buộc: <code>{', '.join(missing)}</code>\n\n"
            f"Cookie Netflix hợp lệ phải có đủ:\n"
            f"• <code>NetflixId</code>\n"
            f"• <code>SecureNetflixId</code>\n"
            f"• <code>nfvdid</code>",
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
