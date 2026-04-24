# Netflix TV Login – đăng nhập Netflix trên TV/Smart TV bằng mã TV code.

import re

import requests

from .cookie_utils import build_cookie_header, extract_cookie_dict, validate_netflix_cookie

_MOD_SIG = "687579636f6e676465763035"

TV2_URL = "https://www.netflix.com/tv2"

REQUEST_HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "sec-fetch-site": "same-origin",
    "origin": "https://www.netflix.com",
    "sec-fetch-mode": "navigate",
    "referer": "https://www.netflix.com/tv2",
    "sec-fetch-dest": "document",
    "accept-language": "vi-VN,vi;q=0.9",
    "priority": "u=0, i",
}


def _build_proxies(proxy_url: str | None) -> dict | None:
    # Chuyển proxy URL sang dict cho requests.
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _fetch_auth_url(cookie_header: str, proxies: dict | None, timeout: int = 15) -> str:
    # GET trang /tv2 để lấy authURL động từ HTML.
    headers = {**REQUEST_HEADERS_BASE, "Cookie": cookie_header}
    response = requests.get(TV2_URL, headers=headers, proxies=proxies, timeout=timeout, allow_redirects=True)
    response.raise_for_status()

    # authURL nằm trong JSON inline hoặc form input
    match = re.search(
        r'"authURL"\s*:\s*"([^"]+)"'
        r'|authURL=([^&"\'\\s]+)'
        r'|name=["\']authURL["\'][^>]*value=["\']([^"\']+)["\']'
        r'|value=["\']([^"\']+)["\'][^>]*name=["\']authURL["\']',
        response.text,
    )
    if match:
        return next(g for g in match.groups() if g is not None)

    raise ValueError("Không tìm thấy authURL trong trang Netflix TV. Cookie có thể đã hết hạn.")


def login_netflix_tv(tv_code: str, cookie_text: str, proxy_url: str | None = None) -> tuple[bool, str]:
    # Đăng nhập Netflix TV bằng mã TV code và cookie account.
    # Args:
    # tv_code:     Mã TV hiển thị trên màn hình Netflix (ví dụ: "ABCD1234").
    # cookie_text: Nội dung cookie Netflix dạng Netscape hoặc JSON.
    # proxy_url:   (Tuỳ chọn) URL proxy dạng http://user:pass@host:port.
    # Returns:
    # (True, "OK")        nếu đăng nhập thành công.
    # (False, "lý do")    nếu thất bại.
    # 1. Validate và parse cookie
    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        return False, error_msg

    cookie_dict = extract_cookie_dict(cookie_text.strip())
    cookie_header = build_cookie_header(cookie_dict)
    proxies = _build_proxies(proxy_url)

    # 2. Lấy authURL động từ trang /tv2
    try:
        auth_url = _fetch_auth_url(cookie_header, proxies)
    except Exception as exc:
        return False, f"Không lấy được authURL: {exc}"

    # 3. Gửi mã TV
    payload = {
        "flow": "websiteSignUp",
        "authURL": auth_url,
        "flowMode": "enterTvLoginRendezvousCode",
        "withFields": "tvLoginRendezvousCode,isTvUrl2",
        "code": tv_code,
        "tvLoginRendezvousCode": tv_code,
        "isTvUrl2": "true",
        "action": "nextAction",
    }
    headers = {**REQUEST_HEADERS_BASE, "Cookie": cookie_header}

    try:
        response = requests.post(
            TV2_URL, data=payload, headers=headers,
            proxies=proxies, timeout=15, allow_redirects=True,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        return False, f"HTTP {exc.response.status_code}"
    except Exception as exc:
        return False, str(exc)

    # 4. Phán đoán kết quả từ response HTML
    html = response.text
    if _is_login_success(html):
        return True, "OK"

    reason = _extract_error_reason(html)
    return False, reason


def _is_login_success(html: str) -> bool:
    # True nếu HTML cho thấy đăng nhập TV thành công.
    success_signals = [
        "tvLoginSuccess",
        "successIcon",
        "tv-login-success",
        "Your TV is now signed in",
        "TV của bạn đã đăng nhập",
        '"status":"success"',
    ]
    lower = html.lower()
    return any(s.lower() in lower for s in success_signals)


def _extract_error_reason(html: str) -> str:
    # Tìm thông báo lỗi trong HTML response.
    match = re.search(r'"message"\s*:\s*"([^"]{5,200})"', html)
    if match:
        return match.group(1)

    match = re.search(r'class="[^"]*(?:error|alert)[^"]*"[^>]*>([^<]{5,200})<', html, re.I)
    if match:
        return match.group(1).strip()

    return "Mã TV không hợp lệ hoặc đã hết hạn."