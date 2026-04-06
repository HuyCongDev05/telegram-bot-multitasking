import logging
import zipfile
from html import escape
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID, VERIFY_COST
from database_mysql import Database
from netflix.cookie_utils import validate_netflix_cookie
from netflix.netflix_checker import NetflixChecker, NetscapeConverter
from utils.i18n import DEFAULT_LANGUAGE, get_user_language
from utils.messages import get_back_admin_button_label, get_ui_label
from utils.proxy_helper import format_proxy_url

# Trang Trợ giúp của Netflix cho biết dịch vụ này có sẵn tại hơn 190 quốc gia và nêu rõ
# không khả dụng tại Trung Quốc, Crimea, Triều Tiên, Nga và Syria. Để đảm bảo hiển thị
# ổn định, hãy giữ bản đồ quốc gia ISO alpha-2 toàn diện tại đây.
COUNTRY_MAP_EN = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua and Barbuda",
    "AI": "Anguilla",
    "AL": "Albania",
    "AM": "Armenia",
    "AO": "Angola",
    "AQ": "Antarctica",
    "AR": "Argentina",
    "AS": "American Samoa",
    "AT": "Austria",
    "AU": "Australia",
    "AW": "Aruba",
    "AX": "Aland Islands",
    "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina",
    "BB": "Barbados",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BL": "Saint Barthelemy",
    "BM": "Bermuda",
    "BN": "Brunei",
    "BO": "Bolivia",
    "BQ": "Caribbean Netherlands",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BV": "Bouvet Island",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CA": "Canada",
    "CC": "Cocos (Keeling) Islands",
    "CD": "Democratic Republic of the Congo",
    "CF": "Central African Republic",
    "CG": "Republic of the Congo",
    "CH": "Switzerland",
    "CI": "Cote d'Ivoire",
    "CK": "Cook Islands",
    "CL": "Chile",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CV": "Cabo Verde",
    "CW": "Curacao",
    "CX": "Christmas Island",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "EH": "Western Sahara",
    "ER": "Eritrea",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FK": "Falkland Islands",
    "FM": "Micronesia",
    "FO": "Faroe Islands",
    "FR": "France",
    "GA": "Gabon",
    "GB": "United Kingdom",
    "GD": "Grenada",
    "GE": "Georgia",
    "GF": "French Guiana",
    "GG": "Guernsey",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GL": "Greenland",
    "GM": "Gambia",
    "GN": "Guinea",
    "GP": "Guadeloupe",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GS": "South Georgia and the South Sandwich Islands",
    "GT": "Guatemala",
    "GU": "Guam",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HK": "Hong Kong",
    "HM": "Heard Island and McDonald Islands",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IM": "Isle of Man",
    "IN": "India",
    "IO": "British Indian Ocean Territory",
    "IQ": "Iraq",
    "IR": "Iran",
    "IS": "Iceland",
    "IT": "Italy",
    "JE": "Jersey",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "Saint Kitts and Nevis",
    "KP": "North Korea",
    "KR": "South Korea",
    "KW": "Kuwait",
    "KY": "Cayman Islands",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LB": "Lebanon",
    "LC": "Saint Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "LY": "Libya",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MF": "Saint Martin",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MN": "Mongolia",
    "MO": "Macao",
    "MP": "Northern Mariana Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MS": "Montserrat",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MX": "Mexico",
    "MY": "Malaysia",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NU": "Niue",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PA": "Panama",
    "PE": "Peru",
    "PF": "French Polynesia",
    "PG": "Papua New Guinea",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PM": "Saint Pierre and Miquelon",
    "PN": "Pitcairn Islands",
    "PR": "Puerto Rico",
    "PS": "Palestine",
    "PT": "Portugal",
    "PW": "Palau",
    "PY": "Paraguay",
    "QA": "Qatar",
    "RE": "Reunion",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russia",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SE": "Sweden",
    "SG": "Singapore",
    "SH": "Saint Helena",
    "SI": "Slovenia",
    "SJ": "Svalbard and Jan Mayen",
    "SK": "Slovakia",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SN": "Senegal",
    "SO": "Somalia",
    "SR": "Suriname",
    "SS": "South Sudan",
    "ST": "Sao Tome and Principe",
    "SV": "El Salvador",
    "SX": "Sint Maarten",
    "SY": "Syria",
    "SZ": "Eswatini",
    "TC": "Turks and Caicos Islands",
    "TD": "Chad",
    "TF": "French Southern Territories",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TR": "Turkey",
    "TT": "Trinidad and Tobago",
    "TV": "Tuvalu",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UG": "Uganda",
    "UM": "United States Minor Outlying Islands",
    "US": "United States",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VA": "Vatican City",
    "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela",
    "VG": "British Virgin Islands",
    "VI": "U.S. Virgin Islands",
    "VN": "Vietnam",
    "VU": "Vanuatu",
    "WF": "Wallis and Futuna",
    "WS": "Samoa",
    "YE": "Yemen",
    "YT": "Mayotte",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

COUNTRY_MAP = {
    "en": COUNTRY_MAP_EN,
    "vi": {
        **COUNTRY_MAP_EN,
        "AE": "Các Tiểu Vương quốc Ả Rập Thống nhất",
        "AF": "Afghanistan",
        "AL": "Albania",
        "AM": "Armenia",
        "AR": "Argentina",
        "AT": "Áo",
        "AU": "Australia",
        "AZ": "Azerbaijan",
        "BD": "Bangladesh",
        "BE": "Bỉ",
        "BG": "Bulgaria",
        "BH": "Bahrain",
        "BN": "Brunei",
        "BO": "Bolivia",
        "BR": "Brazil",
        "BY": "Belarus",
        "CA": "Canada",
        "CH": "Thụy Sĩ",
        "CL": "Chile",
        "CN": "Trung Quốc",
        "CO": "Colombia",
        "CZ": "Séc",
        "DE": "Đức",
        "DK": "Đan Mạch",
        "DZ": "Algeria",
        "EC": "Ecuador",
        "EE": "Estonia",
        "EG": "Ai Cập",
        "ES": "Tây Ban Nha",
        "FI": "Phần Lan",
        "FR": "Pháp",
        "GB": "Vương quốc Anh",
        "GE": "Georgia",
        "GR": "Hy Lạp",
        "HK": "Hồng Kông",
        "HR": "Croatia",
        "HU": "Hungary",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IN": "Ấn Độ",
        "IQ": "Iraq",
        "IR": "Iran",
        "IS": "Iceland",
        "IT": "Ý",
        "JO": "Jordan",
        "JP": "Nhật Bản",
        "KE": "Kenya",
        "KG": "Kyrgyzstan",
        "KH": "Campuchia",
        "KR": "Hàn Quốc",
        "KW": "Kuwait",
        "KZ": "Kazakhstan",
        "LA": "Lào",
        "LB": "Liban",
        "LK": "Sri Lanka",
        "LT": "Litva",
        "LU": "Luxembourg",
        "LV": "Latvia",
        "MA": "Ma Rốc",
        "MD": "Moldova",
        "MK": "Bắc Macedonia",
        "MM": "Myanmar",
        "MN": "Mông Cổ",
        "MO": "Ma Cao",
        "MX": "Mexico",
        "MY": "Malaysia",
        "NG": "Nigeria",
        "NL": "Hà Lan",
        "NO": "Na Uy",
        "NP": "Nepal",
        "NZ": "New Zealand",
        "OM": "Oman",
        "PA": "Panama",
        "PE": "Peru",
        "PH": "Philippines",
        "PK": "Pakistan",
        "PL": "Ba Lan",
        "PT": "Bồ Đào Nha",
        "QA": "Qatar",
        "RO": "Romania",
        "RS": "Serbia",
        "RU": "Nga",
        "SA": "Ả Rập Xê Út",
        "SE": "Thụy Điển",
        "SG": "Singapore",
        "SI": "Slovenia",
        "SK": "Slovakia",
        "SY": "Syria",
        "TH": "Thái Lan",
        "TJ": "Tajikistan",
        "TM": "Turkmenistan",
        "TR": "Thổ Nhĩ Kỳ",
        "TW": "Đài Loan",
        "TZ": "Tanzania",
        "UA": "Ukraine",
        "US": "Hoa Kỳ",
        "UY": "Uruguay",
        "UZ": "Uzbekistan",
        "VE": "Venezuela",
        "VN": "Việt Nam",
        "ZA": "Nam Phi",
    },
}

MAX_UPLOAD_COOKIES = 20
MAX_FETCH_RECHECKS = 20
FETCH_BATCH_SIZE = 5

logger = logging.getLogger(__name__)

WATCHABILITY_ERROR_CODES = {
    "no_active_plan",
    "membership_setup_required",
    "membership_restart_required",
    "membership_on_hold",
    "payment_issue",
}
COOKIE_ERROR_MESSAGES = {
    "cookie_expired_or_invalid": {
        "en": "Cookie expired or invalid.",
        "vi": "Cookie đã hết hạn hoặc không hợp lệ.",
    },
    "no_active_plan": {
        "en": "Logged in successfully but no active Netflix plan was found, so this cookie cannot watch right now.",
        "vi": "Cookie vẫn đăng nhập được nhưng không có gói Netflix đang hoạt động nên hiện không xem được.",
    },
    "membership_setup_required": {
        "en": "The account setup is incomplete, so this cookie cannot watch right now.",
        "vi": "Tài khoản chưa hoàn tất kích hoạt hoặc gói cước nên cookie này hiện không xem được.",
    },
    "membership_restart_required": {
        "en": "The membership must be restarted before this cookie can watch.",
        "vi": "Tài khoản cần khởi động lại membership trước khi có thể xem.",
    },
    "membership_on_hold": {
        "en": "The membership is on hold, so this cookie cannot watch right now.",
        "vi": "Gói Netflix đang bị tạm giữ nên cookie này hiện không xem được.",
    },
    "payment_issue": {
        "en": "The account has a payment issue, so this cookie cannot watch right now.",
        "vi": "Tài khoản đang có lỗi thanh toán nên cookie này hiện không xem được.",
    },
}


def get_country_name(code, language: str = DEFAULT_LANGUAGE):
    if not code:
        return "Unknown" if language == 'en' else "Không rõ"

    normalized_code = code.upper()
    language_map = COUNTRY_MAP.get(language, COUNTRY_MAP["vi"])
    return language_map.get(normalized_code, COUNTRY_MAP["en"].get(normalized_code, code))


def _is_watchability_failure(result: dict) -> bool:
    return isinstance(result, dict) and result.get("error_code") in WATCHABILITY_ERROR_CODES


def _get_cookie_error_message(result: dict, language: str = DEFAULT_LANGUAGE) -> str:
    if isinstance(result, dict):
        error_code = result.get("error_code")
        localized = COOKIE_ERROR_MESSAGES.get(error_code)
        if localized:
            return localized.get(language, localized["en"])

        error_text = result.get("error")
        if error_text:
            return error_text

    return "Unknown" if language == 'en' else "Không xác định"


def _normalize_cookie_content(cookie_content: str):
    storage_cookie_text = cookie_content.strip()
    is_valid, error_message = validate_netflix_cookie(cookie_content)
    if not is_valid:
        return None, None, error_message

    cookies = NetscapeConverter.convert_to_json(cookie_content)
    if not cookies:
        return None, None, "❌ Không đọc được cookie Netflix từ nội dung đã gửi."

    return cookies, storage_cookie_text, ""


def _check_cookie_content(db: Database, cookie_content: str):
    cookies, storage_cookie_text, error_message = _normalize_cookie_content(cookie_content)
    if not cookies:
        return False, {"error": error_message}, None, None

    proxy = db.get_random_proxy()
    proxy_url = format_proxy_url(proxy) if proxy else None

    checker = NetflixChecker(proxy_url=proxy_url)
    success, result = checker.check(cookies)
    if not success:
        return False, result, None, None

    return True, result, storage_cookie_text, storage_cookie_text


def _build_cookie_result_text(result: dict, language: str = DEFAULT_LANGUAGE) -> str:
    if language == 'en':
        return (
            "✅ <b>LIVE NETFLIX COOKIE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📧 Email: <code>{result['email']}</code>\n"
            f"📦 Plan: {result['plan']}\n"
            f"🌍 Country: {get_country_name(result['country'], language)}\n"
            f"👥 Extra Member: {'Yes' if result['extra_member'] else 'No'}"
        )
    return (
        "✅ <b>COOKIE NETFLIX LIVE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 Email: <code>{result['email']}</code>\n"
        f"📦 Gói cước: {result['plan']}\n"
        f"🌍 Quốc gia: {get_country_name(result['country'], language)}\n"
        f"👥 Thành viên bổ sung: {'Có' if result['extra_member'] else 'Không'}"
    )


async def _delete_source_message(update: Update):
    message = update.effective_message
    if not message:
        return

    try:
        await message.delete()
    except Exception:
        pass


def _extract_cookie_entries(file_name: str, file_bytes: bytes):
    lower_name = (file_name or "").lower()

    if lower_name.endswith(".zip"):
        try:
            archive = zipfile.ZipFile(BytesIO(file_bytes))
        except zipfile.BadZipFile:
            return None, 0, "❌ File nén không hợp lệ. Vui lòng gửi lại file .zip chứa các file .txt."

        txt_entries = [
            item for item in archive.infolist()
            if not item.is_dir() and item.filename.lower().endswith(".txt")
        ]
        txt_entries.sort(key=lambda item: item.filename)

        if not txt_entries:
            return None, 0, "❌ Không tìm thấy file .txt nào trong file .zip đã gửi."

        ignored_count = max(len(txt_entries) - MAX_UPLOAD_COOKIES, 0)
        entries = []

        for item in txt_entries[:MAX_UPLOAD_COOKIES]:
            try:
                content = archive.read(item).decode("utf-8", errors="ignore").strip()
            except Exception:
                content = ""
            entries.append((item.filename, content))

        return entries, ignored_count, ""

    content = file_bytes.decode("utf-8", errors="ignore").strip()
    if not content:
        return None, 0, "❌ File cookie trống, vui lòng kiểm tra lại."

    return [(file_name or "netflix.txt", content)], 0, ""


async def check_cookie_netflix_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Bắt đầu luồng kiểm tra cookie Netflix."""
    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

    if db.is_service_maintenance('check_cookie_netflix') and user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(
                (
                    "❌ <b>Notice:</b> The Netflix Cookie Check service is currently under maintenance. Please try again later!"
                    if language == 'en'
                    else "❌ <b>Thông báo:</b> Dịch vụ Check Cookie Netflix hiện đang bảo trì. Vui lòng quay lại sau!"
                ),
                parse_mode='HTML',
            )
        return

    user = db.get_user(user_id)
    if user['balance'] < VERIFY_COST:
        if update.effective_message:
            await update.effective_message.reply_text(
                (
                    f"❌ Insufficient balance! Each check costs <b>{VERIFY_COST} points</b>. Current balance: {user['balance']} points."
                    if language == 'en'
                    else f"❌ Số dư không đủ! Mỗi lượt check tốn <b>{VERIFY_COST} điểm</b>. Hiện có: {user['balance']} điểm."
                ),
                parse_mode='HTML',
            )
        return

    from handlers.user_commands import start_input_flow

    service_label = get_ui_label('check_cookie_netflix', language)
    prompt_text = (
        f"<b>{service_label}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + (
            "Please <b>upload a .txt/.json file</b> or <b>paste the cookie content</b> to start checking.\n"
            f"💰 Cost: {VERIFY_COST} points per successful check."
            if language == 'en'
            else "Vui lòng <b>gửi file .txt/.json</b> hoặc <b>dán nội dung cookie</b> để bắt đầu kiểm tra.\n"
            f"💰 Chi phí: {VERIFY_COST} điểm cho mỗi lượt thành công."
        )
    )
    await start_input_flow(update, context, prompt_text, 'check_cookie_netflix_step_1', 'cancel_to_netflix_menu')


async def upload_netflix_cookies_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Bắt đầu luồng admin nạp cookie Netflix vào kho."""
    if update.effective_user.id != ADMIN_USER_ID:
        return

    from handlers.user_commands import start_input_flow

    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    prompt_text = (
        "📥 <b>UPLOAD NETFLIX COOKIES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Send <b>1 .txt file</b> or <b>1 .zip file</b> containing multiple .txt files.\n"
        "Each .txt file should contain 1 cookie.\n"
        f"The system only reads and checks up to <b>{MAX_UPLOAD_COOKIES}</b> cookies per upload.\n"
        "Only cookies that can actually watch Netflix will be stored."
        if language == 'en' else
        "📥 <b>NẠP COOKIE NETFLIX</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Gửi <b>1 file .txt</b> hoặc <b>1 file .zip</b> chứa nhiều file .txt.\n"
        "Mỗi file .txt tương ứng 1 cookie.\n"
        f"Hệ thống chỉ đọc và check tối đa <b>{MAX_UPLOAD_COOKIES}</b> cookie mỗi lần nạp.\n"
        "Chỉ cookie nào xem được Netflix thật sự mới được lưu vào kho."
    )
    await start_input_flow(
        update,
        context,
        prompt_text,
        'admin_upload_netflix_cookies_step_1',
        'cancel_to_admin_menu',
    )


async def process_admin_netflix_cookie_upload(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        db: Database,
        file_name: str,
        file_bytes: bytes,
):
    """Xử lý file admin nạp cookie Netflix vào kho."""
    if update.effective_user.id != ADMIN_USER_ID:
        return

    message = update.effective_message
    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    processing_msg = await message.reply_text(
        "⏳ Checking and uploading Netflix cookies to the inventory..." if language == 'en'
        else "⏳ Đang kiểm tra và nạp cookie Netflix vào kho..."
    )

    entries, ignored_count, error_message = _extract_cookie_entries(file_name, file_bytes)
    if error_message:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')]]
        )
        await processing_msg.edit_text(error_message, reply_markup=reply_markup, parse_mode='HTML')
        return

    checked = 0
    stored = 0
    rejected = 0
    errors = 0
    rejected_details = []

    for entry_name, cookie_content in entries:
        checked += 1

        if not cookie_content:
            errors += 1
            continue

        success, result, stored_cookie_text, _ = _check_cookie_content(db, cookie_content)
        if not success:
            rejected += 1
            if len(rejected_details) < 5:
                cookie_name = entry_name or f"cookie_{checked}.txt"
                reason = _get_cookie_error_message(result, language)
                rejected_details.append(f"• <code>{escape(cookie_name)}</code>: {escape(reason)}")
            continue

        if db.add_netflix_cookie(stored_cookie_text):
            stored += 1
        else:
            errors += 1

    inventory = db.count_netflix_cookies()
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')]]
    )
    summary = (
        "✅ <b>NETFLIX COOKIE UPLOAD COMPLETED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Read: <code>{checked}</code>\n"
        f"➕ Stored: <code>{stored}</code>\n"
        f"🚫 Dead/invalid: <code>{rejected}</code>\n"
        f"❌ File errors: <code>{errors}</code>\n"
        f"⏭ Skipped due to limit: <code>{ignored_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Current inventory: <code>{inventory}</code>"
        if language == 'en' else
        "✅ <b>HOÀN TẤT NẠP COOKIE NETFLIX</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Đã đọc: <code>{checked}</code>\n"
        f"➕ Lưu vào kho: <code>{stored}</code>\n"
        f"🚫 Die/không xem được: <code>{rejected}</code>\n"
        f"❌ Lỗi file: <code>{errors}</code>\n"
        f"⏭ Bỏ qua do vượt giới hạn: <code>{ignored_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Tồn kho hiện tại: <code>{inventory}</code>"
    )
    if rejected_details:
        summary += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "📝 Rejected details:\n"
            if language == 'en' else
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "📝 Chi tiết bị từ chối:\n"
        )
        summary += "\n".join(rejected_details)

        remaining_rejected = rejected - len(rejected_details)
        if remaining_rejected > 0:
            summary += (
                f"\n...and <code>{remaining_rejected}</code> more rejected cookies."
                if language == 'en' else
                f"\n...và còn <code>{remaining_rejected}</code> cookie bị từ chối khác."
            )

    await processing_msg.edit_text(summary, parse_mode='HTML', reply_markup=reply_markup)
    await _delete_source_message(update)


async def get_cookie_netflix_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Lấy lần lượt một cookie Netflix live từ kho DB."""
    from handlers.user_commands import show_main_menu_after_delay

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if db.is_service_maintenance('get_cookie_netflix') and user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(
                (
                    "❌ <b>Notice:</b> The Get Netflix Cookie service is currently under maintenance. Please try again later!"
                    if language == 'en'
                    else "❌ <b>Thông báo:</b> Dịch vụ Lấy Cookie Netflix hiện đang bảo trì. Vui lòng quay lại sau!"
                ),
                parse_mode='HTML',
            )
        return

    message = update.effective_message
    processing_msg = await message.reply_text(
        "⏳ Finding a live Netflix cookie for you..." if language == 'en'
        else "⏳ Đang tìm cookie Netflix live cho bạn..."
    )

    checked_count = 0
    while checked_count < MAX_FETCH_RECHECKS:
        batch_size = min(FETCH_BATCH_SIZE, MAX_FETCH_RECHECKS - checked_count)
        cookie_rows = db.get_netflix_cookies(limit=batch_size)
        if not cookie_rows:
            break

        for cookie_row in cookie_rows:
            checked_count += 1
            success, result, _, cookie_text = _check_cookie_content(db, cookie_row['cookie_text'])

            if not success:
                db.delete_netflix_cookie(cookie_row['id'])
                continue

            cookie_file = BytesIO(cookie_text.encode('utf-8'))
            cookie_file.name = "netflix.txt"

            await message.reply_document(
                document=InputFile(cookie_file, filename="netflix.txt"),
                caption=_build_cookie_result_text(result, language),
                parse_mode='HTML',
            )
            await processing_msg.edit_text("✅ Sent 1 live Netflix cookie." if language == 'en' else "✅ Đã gửi 1 cookie Netflix live.")
            await show_main_menu_after_delay(update, context, db)
            return

        if len(cookie_rows) < batch_size:
            break

    await processing_msg.edit_text(
        (
            "❌ <b>There is currently no live Netflix cookie available.</b>"
            if language == 'en'
            else "❌ <b>Hiện tại chưa có cookie Netflix live để gửi.</b>"
        ),
        parse_mode='HTML',
    )
    await show_main_menu_after_delay(update, context, db)


async def process_netflix_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cookie_content: str):
    """Logic xử lý và kiểm tra cookie Netflix."""
    from handlers.user_commands import show_main_menu_after_delay

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    message = update.effective_message
    processing_msg = await message.reply_text("⏳ Checking the cookie, please wait..." if language == 'en' else "⏳ Đang kiểm tra cookie, vui lòng đợi...")

    try:
        cookies, _, error_message = _normalize_cookie_content(cookie_content)
        if not cookies:
            await processing_msg.edit_text(error_message, parse_mode='HTML')
            await show_main_menu_after_delay(update, context, db)
            return

        proxy = db.get_random_proxy()
        proxy_url = format_proxy_url(proxy) if proxy else None

        checker = NetflixChecker(proxy_url=proxy_url)
        success, result = checker.check(cookies)

        if success:
            if db.deduct_balance(user_id, VERIFY_COST):
                res_msg = (
                    "✅ <b>COOKIE CHECK RESULT: LIVE</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📧 Email: <code>{result['email']}</code>\n"
                    f"📦 Plan: {result['plan']}\n"
                    f"🌍 Country: {get_country_name(result['country'], language)}\n"
                    f"👥 Extra Member: {'Yes' if result['extra_member'] else 'No'}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Deducted: {VERIFY_COST} points\n"
                    f"💰 Remaining balance: {db.get_user(user_id)['balance']} points"
                    if language == 'en' else
                    "✅ <b>KẾT QUẢ CHECK COOKIE: LIVE</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📧 Email: <code>{result['email']}</code>\n"
                    f"📦 Gói cước: {result['plan']}\n"
                    f"🌍 Quốc gia: {get_country_name(result['country'], language)}\n"
                    f"👥 Thành viên bổ sung: {'Có' if result['extra_member'] else 'Không'}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Đã trừ: {VERIFY_COST} điểm\n"
                    f"💰 Số dư còn lại: {db.get_user(user_id)['balance']} điểm"
                )
                await processing_msg.edit_text(res_msg, parse_mode='HTML')
            else:
                await processing_msg.edit_text("❌ System error while deducting points. Please try again!" if language == 'en' else "❌ Lỗi hệ thống khi trừ điểm. Vui lòng thử lại!")
        else:
            error_text = escape(_get_cookie_error_message(result, language))
            is_watchability_failure = _is_watchability_failure(result)
            await processing_msg.edit_text(
                (
                    f"❌ <b>Cookie cannot watch Netflix right now!</b>\nReason: <code>{error_text}</code>"
                    if language == 'en' and is_watchability_failure
                    else f"❌ <b>Cookie is dead or invalid!</b>\nReason: <code>{error_text}</code>"
                    if language == 'en'
                    else f"❌ <b>Cookie hiện không xem được Netflix!</b>\nLý do: <code>{error_text}</code>"
                    if is_watchability_failure
                    else f"❌ <b>Cookie Die hoặc Không hợp lệ!</b>\nLý do: <code>{error_text}</code>"
                ),
                parse_mode='HTML',
            )

        await _delete_source_message(update)
        await show_main_menu_after_delay(update, context, db)
    except Exception as exc:
        logger.error("Lỗi khi xử lý Netflix Cookie cho user %s: %s", user_id, exc)
        await processing_msg.edit_text("❌ An error occurred while processing your request. Please try again later!" if language == 'en' else "❌ Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau!")
        await show_main_menu_after_delay(update, context, db)
