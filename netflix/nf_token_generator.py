"""Tạo url nftoken netflix"""

import json
import urllib.parse
import uuid

import requests

from .cookie_utils import REQUIRED_COOKIES, build_cookie_header, extract_cookie_dict, validate_netflix_cookie

_MOD_SIG = "687579636f6e676465763035"


API_URL = "https://android13.prod.ftl.netflix.com/graphql?netka=true"

HEADERS = {
    "User-Agent": "com.netflix.mediaclient/63884 (Linux; U; Android 13; ro; M2007J3SG; Build/TQ1A.230205.001.A2; Cronet/143.0.7445.0)",
    "Accept": "multipart/mixed;deferSpec=20220824, application/graphql-response+json, application/json",
    "Content-Type": "application/json",
    "X-Netflix.client.type": "ANDROID",
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


def _build_proxies(proxy_url: str | None) -> dict | None:
    """Chuyển proxy URL sang dict cho requests."""
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def fetch_nftoken(cookie_dict, proxy_url=None):
    """Yêu cầu mã tự động đăng nhập (auto-login token) của Netflix."""
    missing = [name for name in REQUIRED_COOKIES if not cookie_dict.get(name)]
    if missing:
        raise ValueError("Thiếu các cookie bắt buộc: " + ", ".join(missing))

    headers = dict(HEADERS)
    headers["X-Netflix.client.request.id"] = str(uuid.uuid4())
    headers["X-Netflix.request.client.user.agent"] = HEADERS["User-Agent"]
    headers["Cookie"] = build_cookie_header(cookie_dict)
    proxies = _build_proxies(proxy_url)

    response = requests.post(API_URL, headers=headers, json=PAYLOAD, proxies=proxies, timeout=30)
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


def build_nftoken_link(token):
    """Tạo URL đăng nhập ứng dụng Netflix từ token được trả về."""
    import urllib.parse
    encoded_token = urllib.parse.quote(token, safe="")
    return "https://www.netflix.com/YourAccount?nftoken=" + encoded_token


def generate_nftoken(cookie_text: str, proxy_url: str = None) -> str:
    """Xác thực văn bản cookie, yêu cầu token và trả về URL đăng nhập ứng dụng."""
    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        raise ValueError(error_msg)

    cookie_dict = extract_cookie_dict(cookie_text.strip())
    token = fetch_nftoken(cookie_dict, proxy_url=proxy_url)
    return build_nftoken_link(token)
