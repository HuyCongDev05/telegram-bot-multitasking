"""Mẫu tin nhắn dùng chung cho Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import DISCORD_QUEST_COST, VERIFY_COST
from utils.i18n import DEFAULT_LANGUAGE, LANGUAGE_BUTTONS, tr

# System template mapping signature
_TMPL_SIG = "aHV5Y29uZ2RldjA1"

SERVICE_NAME_KEYS = {
    'verify_chatgpt_k12': 'service.verify_chatgpt_k12',
    'verify_spotify_student': 'service.verify_spotify_student',
    'verify_bolt_teacher': 'service.verify_bolt_teacher',
    'verify_youtube_student': 'service.verify_youtube_student',
    'verify_gemini_pro': 'service.verify_gemini_pro',
    'convert_url_login_app_netflix': 'service.convert_url_login_app_netflix',
    'get_cookie_netflix': 'service.get_cookie_netflix',
    'check_cookie_netflix_step_1': 'service.check_cookie_netflix_step_1',
    'discord_quest': 'service.discord_quest',
    'check_cc_step_1': 'service.check_cc_step_1',
    'use_key_step_1': 'service.use_key_step_1',
    'admin_add_balance_step_1': 'service.admin_add_balance_step_1',
    'admin_block_step_1': 'service.admin_block_step_1',
    'admin_unblock_step_1': 'service.admin_unblock_step_1',
    'admin_gen_key_step_1': 'service.admin_gen_key_step_1',
    'admin_upload_netflix_cookies_step_1': 'service.admin_upload_netflix_cookies_step_1',
}


def get_ui_label(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Lấy label UI dùng chung để icon đồng nhất giữa các file."""
    return tr(language, f"ui.{key}")


def get_back_button_label(language: str = DEFAULT_LANGUAGE) -> str:
    return tr(language, "nav.back")


def get_back_main_button_label(language: str = DEFAULT_LANGUAGE) -> str:
    return tr(language, "nav.back_main")


def get_back_admin_button_label(language: str = DEFAULT_LANGUAGE) -> str:
    return tr(language, "nav.back_admin")


BACK_BUTTON_LABEL = get_back_button_label()
BACK_MAIN_BUTTON_LABEL = get_back_main_button_label()
BACK_ADMIN_BUTTON_LABEL = get_back_admin_button_label()


def get_service_display_name(service_id: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Lấy tên hiển thị của dịch vụ theo ngôn ngữ hiện tại."""
    key = SERVICE_NAME_KEYS.get(service_id)
    if key:
        return tr(language, key)
    return get_ui_label(service_id, language)


def get_language_selection_message() -> str:
    """Tin nhắn chọn ngôn ngữ, luôn hiển thị bằng tiếng Anh theo yêu cầu."""
    return (
        f"{tr('en', 'language.select.title')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{tr('en', 'language.select.body')}\n\n"
        "You can continue after selecting one option below."
    )


def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Bàn phím chọn ngôn ngữ."""
    keyboard = [[
        InlineKeyboardButton(LANGUAGE_BUTTONS["en"], callback_data="select_language:en"),
        InlineKeyboardButton(LANGUAGE_BUTTONS["vi"], callback_data="select_language:vi"),
    ]]
    return InlineKeyboardMarkup(keyboard)


def get_welcome_message(full_name: str, invited_by: bool = False, language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn chào mừng khi người dùng dùng /start."""
    msg = tr(language, "welcome.header", full_name=full_name)
    if invited_by:
        msg += tr(language, "welcome.invited")
    msg += tr(language, "welcome.footer")
    return msg


def get_welcome_keyboard(is_admin: bool = False, language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím chính của bot."""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('verify_menu', language), callback_data='verify_menu')],
        [InlineKeyboardButton(get_ui_label('netflix_menu', language), callback_data='netflix_menu')],
        [InlineKeyboardButton(get_ui_label('check_cc', language), callback_data='check_cc_menu')],
        [InlineKeyboardButton(get_ui_label('discord_quest_auto', language), callback_data='discord_quest')],
        [
            InlineKeyboardButton(get_ui_label('invite', language), callback_data='invite'),
            InlineKeyboardButton(get_ui_label('checkin', language), callback_data='checkin'),
        ],
        [
            InlineKeyboardButton(get_ui_label('to_up', language), callback_data='to_up'),
            InlineKeyboardButton(get_ui_label('help', language), callback_data='help'),
        ],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(get_ui_label('admin_menu', language), callback_data='admin_menu')])

    return InlineKeyboardMarkup(keyboard)


def get_verify_menu_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn cho menu xác thực."""
    return tr(language, "menu.verify.message", verify_cost=VERIFY_COST)


def get_verify_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím cho các lệnh xác thực."""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('verify_chatgpt_k12', language), callback_data='verify_chatgpt_k12')],
        [InlineKeyboardButton(get_ui_label('verify_spotify_student', language), callback_data='verify_spotify_student')],
        [InlineKeyboardButton(get_ui_label('verify_bolt_teacher', language), callback_data='verify_bolt_teacher')],
        [InlineKeyboardButton(get_ui_label('verify_youtube_student', language), callback_data='verify_youtube_student')],
        [InlineKeyboardButton(get_ui_label('verify_gemini_pro', language), callback_data='verify_gemini_pro')],
        [InlineKeyboardButton(get_back_button_label(language), callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_netflix_menu_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn cho menu Netflix."""
    return tr(language, "menu.netflix.message")


def get_netflix_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím cho các chức năng Netflix."""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('get_cookie_netflix', language), callback_data='get_cookie_netflix')],
        [InlineKeyboardButton(get_ui_label('convert_url_login_app_netflix', language), callback_data='login_app_netflix')],
        [InlineKeyboardButton(get_ui_label('check_cookie_netflix', language), callback_data='netflix_check')],
        [InlineKeyboardButton(get_back_button_label(language), callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn cho menu quản trị."""
    return tr(language, "menu.admin.message")


def get_admin_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím cho menu quản trị."""
    keyboard = [
        [
            InlineKeyboardButton(get_ui_label('admin_add_balance', language), callback_data='admin_add_balance'),
            InlineKeyboardButton(get_ui_label('admin_users', language), callback_data='admin_users_menu'),
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_maintenance', language), callback_data='admin_maintenance'),
            InlineKeyboardButton(get_ui_label('admin_proxy_mgmt', language), callback_data='admin_proxy_mgmt'),
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_key_menu', language), callback_data='admin_key_menu'),
            InlineKeyboardButton(get_ui_label('admin_broadcast', language), callback_data='admin_broadcast'),
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_list_live_cc', language), callback_data='admin_list_live_cc'),
        ],
        [
            InlineKeyboardButton(
                get_ui_label('admin_upload_netflix_cookies', language),
                callback_data='admin_upload_netflix_cookies',
            ),
        ],
        [InlineKeyboardButton(get_back_button_label(language), callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_users_menu_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn cho submenu quản lý users của admin."""
    return tr(language, "menu.admin_users.message")


def get_admin_users_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím cho submenu quản lý users của admin."""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('admin_search_user', language), callback_data='admin_search_user')],
        [
            InlineKeyboardButton(get_ui_label('admin_block', language), callback_data='admin_block'),
            InlineKeyboardButton(get_ui_label('admin_unblock', language), callback_data='admin_unblock'),
        ],
        [InlineKeyboardButton(get_ui_label('admin_blacklist', language), callback_data='admin_blacklist')],
        [InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_key_menu_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn cho submenu key của admin."""
    return tr(language, "menu.admin_keys.message")


def get_admin_key_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím cho submenu key của admin."""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('admin_gen_key', language), callback_data='admin_gen_key')],
        [InlineKeyboardButton(get_ui_label('admin_list_keys', language), callback_data='admin_list_keys')],
        [InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_proxy_mgmt_keyboard(language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím quản lý Proxy cho Admin."""
    keyboard = [
        [
            InlineKeyboardButton(get_ui_label('admin_add_proxies', language), callback_data='admin_add_proxies'),
            InlineKeyboardButton(get_ui_label('admin_list_proxies', language), callback_data='admin_list_proxies'),
        ],
        [InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_maintenance_keyboard(services_status: dict, language: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Bàn phím quản lý bảo trì cho Admin."""
    keyboard = []

    for svc_id, is_maintenance in services_status.items():
        name = get_service_display_name(svc_id, language)
        status_icon = tr(language, "maintenance.status.on" if is_maintenance else "maintenance.status.off")
        keyboard.append([
            InlineKeyboardButton(f"{name}", callback_data="noop"),
            InlineKeyboardButton(f"{status_icon}", callback_data=f"toggle_m:{svc_id}"),
        ])

    keyboard.append([InlineKeyboardButton(get_back_admin_button_label(language), callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_help_message(language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn trợ giúp."""
    verify_label = get_ui_label('verify_menu', language)
    netflix_label = get_ui_label('netflix_menu', language)
    check_cc_label = get_ui_label('check_cc', language)
    discord_label = get_ui_label('discord_quest_auto', language)

    if language == "en":
        return (
            f"{tr(language, 'help.title')}"
            f"{verify_label}:\n"
            f"Tap '{verify_label}' and send a link:\n"
            f"• ChatGPT Teacher K12 (-💰 {VERIFY_COST})\n"
            f"• Spotify Student (-💰 {VERIFY_COST})\n"
            f"• Bolt.new Teacher (-💰 {VERIFY_COST})\n"
            f"• YouTube Premium (-💰 {VERIFY_COST})\n"
            f"• Gemini One Pro (-💰 {VERIFY_COST})\n\n"
            f"{netflix_label}:\n"
            f"Tap '{netflix_label}' to open 3 features:\n"
            f"• {get_ui_label('get_cookie_netflix', language)} (-💰 {VERIFY_COST})\n"
            f"• {get_ui_label('convert_url_login_app_netflix', language)} (-💰 {VERIFY_COST})\n"
            f"• {get_ui_label('check_cookie_netflix', language)} (-💰 {VERIFY_COST})\n\n"
            f"{check_cc_label}:\n"
            f"Use the <code>/check_cc</code> command or the '{check_cc_label}' button:\n"
            f"• Send: <code>card|month|year|cvv</code> (-💰 {VERIFY_COST})\n\n"
            f"{discord_label}:\n"
            f"Use the '{discord_label}' button:\n"
            f"• Enter your Discord token to automatically finish quests (-💰 {DISCORD_QUEST_COST}).\n\n"
            f"{tr(language, 'help.support')}"
        )

    return (
        f"{tr(language, 'help.title')}"
        f"{verify_label}:\n"
        f"Nhấn nút '{verify_label}' và gửi link:\n"
        f"• ChatGPT Teacher K12 (-💰 {VERIFY_COST})\n"
        f"• Spotify Student (-💰 {VERIFY_COST})\n"
        f"• Bolt.new Teacher (-💰 {VERIFY_COST})\n"
        f"• YouTube Premium (-💰 {VERIFY_COST})\n"
        f"• Gemini One Pro (-💰 {VERIFY_COST})\n\n"
        f"{netflix_label}:\n"
        f"Nhấn nút '{netflix_label}' để mở 3 chức năng:\n"
        f"• {get_ui_label('get_cookie_netflix', language)} (-💰 {VERIFY_COST})\n"
        f"• {get_ui_label('convert_url_login_app_netflix', language)} (-💰 {VERIFY_COST})\n"
        f"• {get_ui_label('check_cookie_netflix', language)} (-💰 {VERIFY_COST})\n\n"
        f"{check_cc_label}:\n"
        f"Sử dụng lệnh <code>/check_cc</code> hoặc nút '{check_cc_label}':\n"
        f"• Gửi: <code>số thẻ|tháng|năm|cvv</code> (-💰 {VERIFY_COST})\n\n"
        f"{discord_label}:\n"
        f"Sử dụng nút '{discord_label}':\n"
        f"• Nhập Discord Token để tự động hoàn thành Quest (-💰 {DISCORD_QUEST_COST}).\n\n"
        f"{tr(language, 'help.support')}"
    )


def get_insufficient_balance_message(current_balance: int, language: str = DEFAULT_LANGUAGE) -> str:
    """Tin nhắn số dư không đủ."""
    return tr(
        language,
        "balance.insufficient",
        verify_cost=VERIFY_COST,
        current_balance=current_balance,
    )


def get_verify_usage_message(service_name: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Hướng dẫn dùng ForceReply cho các luồng xác thực."""
    return tr(language, "verify.usage", service_name=service_name)
