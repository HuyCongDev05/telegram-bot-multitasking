"""Các tiện ích để phân tích và xác thực cookie của Netflix."""

import hashlib
import json
import re

_MOD_SIG = "687579636f6e676465763035"

REQUIRED_COOKIES = ("NetflixId", "SecureNetflixId")
KNOWN_COOKIE_KEYS = {
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
COOKIE_ATTRIBUTE_KEYS = {
    "path",
    "domain",
    "expires",
    "max-age",
    "secure",
    "httponly",
    "samesite",
    "priority",
    "partitioned",
}
NOISE_LINE_PATTERNS = (
    re.compile(r"^(?:[-*]\s*)?valid cookies by\b.*$", re.I),
    re.compile(r"^(?:[-*]\s*)?(?:join\s+)?telegram\b.*$", re.I),
    re.compile(r"^(?:[-*]\s*)?@[\w.]+$", re.I),
    re.compile(r"^(?:[-*]\s*)?(?:https?://)?(?:t\.me|telegram\.me)/\S+$", re.I),
)


def normalize_cookie_domain(domain: str) -> str:
    """Chuẩn hóa tên miền cookie Netscape sang định dạng mà requests có thể sử dụng."""
    normalized = (domain or "").strip()
    if normalized.startswith("#HttpOnly_"):
        normalized = normalized[len("#HttpOnly_"):]
    if normalized.startswith(".www."):
        return "." + normalized[5:]
    if normalized.startswith("www."):
        return "." + normalized[4:]
    return normalized


def is_probable_netscape_cookie_line(line: str) -> bool:
    """Trả về True nếu một dòng có vẻ là hàng cookie Netscape."""
    stripped = (line or "").strip()
    if not stripped:
        return False
    if stripped.startswith("#") and not stripped.startswith("#HttpOnly_"):
        return False

    fields = re.split(r"\s+", stripped, maxsplit=6)
    if len(fields) < 7:
        return False

    domain, flag, path, secure, _expiration, name, _value = fields
    normalized_domain = normalize_cookie_domain(domain)
    return (
            "." in normalized_domain
            and flag.upper() in {"TRUE", "FALSE"}
            and secure.upper() in {"TRUE", "FALSE"}
            and path.startswith("/")
            and re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None
    )


def sanitize_cookie_text(text: str) -> str:
    """Loại bỏ nhiễu tiêu đề/quảng cáo phổ biến trong khi vẫn giữ nguyên nội dung cookie."""
    if not text:
        return ""

    cleaned_lines = []
    for raw_line in text.replace("\ufeff", "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") and not line.startswith("#HttpOnly_"):
            continue
        if any(pattern.match(line) for pattern in NOISE_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _is_cookie_attribute(name: str) -> bool:
    return (name or "").strip().lower() in COOKIE_ATTRIBUTE_KEYS


def extract_cookie_dict(text: str) -> dict:
    """Chuẩn hóa văn bản cookie thành từ điển tên/giá trị (name/value dict)."""
    cookie_dict = {}
    normalized_text = sanitize_cookie_text(text)

    try:
        data = json.loads(normalized_text)
        if isinstance(data, list):
            for item in data:
                if (
                        isinstance(item, dict)
                        and "name" in item
                        and "value" in item
                        and not _is_cookie_attribute(item["name"])
                ):
                    cookie_dict[item["name"]] = str(item["value"])
            if cookie_dict:
                return cookie_dict
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)) and not _is_cookie_attribute(key):
                    cookie_dict[key] = str(value)
            if cookie_dict:
                return cookie_dict
    except json.JSONDecodeError:
        pass

    for line in normalized_text.splitlines():
        if not is_probable_netscape_cookie_line(line):
            continue
        fields = re.split(r"\s+", line, maxsplit=6)
        cookie_dict[fields[5]] = fields[6]

    if cookie_dict:
        return cookie_dict

    for match in re.finditer(r"([a-zA-Z0-9_.-]+)=([^;\s]+)", normalized_text):
        key = match.group(1)
        if _is_cookie_attribute(key):
            continue
        cookie_dict[key] = match.group(2)

    tokens = normalized_text.split()
    for index, token in enumerate(tokens):
        if token in KNOWN_COOKIE_KEYS and index + 1 < len(tokens) and tokens[index + 1] not in KNOWN_COOKIE_KEYS:
            cookie_dict[token] = tokens[index + 1]

    return cookie_dict


def validate_netflix_cookie(text: str) -> tuple:
    """Xác thực xem văn bản cookie có chứa các phím Netflix bắt buộc hay không."""
    normalized_text = sanitize_cookie_text(text)
    if not normalized_text:
        return False, "Nội dung cookie trống."

    cookie_dict = extract_cookie_dict(normalized_text)
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
    """Xây dựng chuỗi tiêu đề Cookie từ ánh xạ cookie được cung cấp."""
    if required_only:
        items = [(key, cookie_dict[key]) for key in REQUIRED_COOKIES if cookie_dict.get(key)]
    else:
        items = list(cookie_dict.items())
    return "; ".join(f"{key}={value}" for key, value in items)


def build_cookie_fingerprint(cookie_input) -> str:
    """Xây dựng dấu vân tay ổn định để phát hiện các trường hợp trùng lặp."""
    if isinstance(cookie_input, dict):
        cookie_dict = {
            str(key): str(value)
            for key, value in cookie_input.items()
            if value is not None and not _is_cookie_attribute(str(key))
        }
    else:
        cookie_dict = extract_cookie_dict(cookie_input)

    preferred_items = [(key, cookie_dict.get(key, "")) for key in REQUIRED_COOKIES if cookie_dict.get(key)]
    if preferred_items:
        canonical_items = preferred_items
    else:
        canonical_items = sorted(
            (key, value)
            for key, value in cookie_dict.items()
            if value is not None and not _is_cookie_attribute(key)
        )

    if not canonical_items:
        return ""

    canonical_text = json.dumps(canonical_items, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
