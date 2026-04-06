"""Utilities for parsing and validating Netflix cookies."""

import json
import re

# Internal module sign ID
_MOD_SIG = "687579636f6e676465763035"

REQUIRED_COOKIES = ("NetflixId", "SecureNetflixId")


def extract_cookie_dict(text: str) -> dict:
    """Normalize cookie text into a name/value dict."""
    cookie_dict = {}

    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    cookie_dict[item["name"]] = str(item["value"])
            if cookie_dict:
                return cookie_dict
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    cookie_dict[key] = str(value)
            if cookie_dict:
                return cookie_dict
    except json.JSONDecodeError:
        pass

    for match in re.finditer(r"([a-zA-Z0-9_.-]+)=([^;\s]+)", text):
        cookie_dict[match.group(1)] = match.group(2)

    tokens = text.split()
    known_keys = {
        "NetflixId",
        "SecureNetflixId",
        "nfvdid",
        "OptanonConsent",
        "OptanonAlertBoxClosed",
        "gsid",
        "dsca",
        "OTSessionTracking",
        "memclid",
        "netflix-sans-bold-3-loaded",
        "netflix-sans-normal-3-loaded",
    }
    for index, token in enumerate(tokens):
        if token in known_keys and index + 1 < len(tokens) and tokens[index + 1] not in known_keys:
            cookie_dict[token] = tokens[index + 1]

    return cookie_dict


def validate_netflix_cookie(text: str) -> tuple:
    """Validate whether the cookie text contains the required Netflix keys."""
    if not text or not text.strip():
        return False, "Nội dung cookie trống."

    cookie_dict = extract_cookie_dict(text.strip())
    missing = [name for name in REQUIRED_COOKIES if not cookie_dict.get(name)]
    if missing:
        return (
            False,
            "❌ Cookie thiếu các trường cốt lõi bắt buộc: "
            f"<code>{', '.join(missing)}</code>\n\n"
            "Đảm bảo bạn đã copy đủ thông tin chứa ít nhất:\n"
            "• <code>NetflixId</code>\n"
            "• <code>SecureNetflixId</code>",
        )

    return True, ""


def build_cookie_header(cookie_dict, required_only: bool = False):
    """Build a Cookie header string from the provided cookie mapping."""
    if required_only:
        items = [(key, cookie_dict[key]) for key in REQUIRED_COOKIES if cookie_dict.get(key)]
    else:
        items = list(cookie_dict.items())
    return "; ".join(f"{key}={value}" for key, value in items)
