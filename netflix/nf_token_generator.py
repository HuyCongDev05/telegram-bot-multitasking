"""Tạo url nftoken netflix"""

import json
import urllib.parse

import requests

from .cookie_utils import REQUIRED_COOKIES, build_cookie_header, extract_cookie_dict, validate_netflix_cookie

_MOD_SIG = "687579636f6e676465763035"


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


def build_nftoken_link(token):
    """Tạo URL đăng nhập ứng dụng Netflix từ token được trả về."""
    encoded_token = urllib.parse.quote(token, safe="")
    return "https://www.netflix.com/YourAccount?nftoken=" + encoded_token


def fetch_nftoken(cookie_dict):
    """Yêu cầu mã tự động đăng nhập (auto-login token) của Netflix."""
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
    """Xác thực văn bản cookie, yêu cầu token và trả về URL đăng nhập ứng dụng."""
    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        raise ValueError(error_msg)

    cookie_dict = extract_cookie_dict(cookie_text.strip())
    token = fetch_nftoken(cookie_dict)
    return build_nftoken_link(token)
