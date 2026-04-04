"""Mẫu tin nhắn"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import VERIFY_COST, DISCORD_QUEST_COST

# System template mapping signature
_TMPL_SIG = "aHV5Y29uZ2RldjA1"

UI_LABELS = {
    'verify_menu': "🎓 Xác thực SheerID",
    'check_cookie_netflix': "🎬 Check Cookie Netflix",
    'convert_url_login_app_netflix': "🔗 App Link Netflix",
    'check_cc': "💳 Check CC",
    'discord_quest_auto': "🚀 Discord Quest Auto",
    'invite': "👥 Mời bạn bè",
    'checkin': "📅 Điểm danh",
    'to_up': "💰 Nạp điểm",
    'help': "💡 Trợ giúp",
    'admin_menu': "🛠 Quản trị viên",
    'verify_chatgpt_k12': "🎓 ChatGPT Teacher K12",
    'verify_spotify_student': "🎵 Spotify Student",
    'verify_bolt_teacher': "⚡ Bolt.new Teacher",
    'verify_youtube_student': "▶️ YouTube Premium",
    'verify_gemini_pro': "🤖 Gemini One Pro",
    'admin_add_balance': "💰 Cộng điểm",
    'admin_block': "🔒 Khóa User",
    'admin_unblock': "🔓 Mở khóa",
    'admin_blacklist': "🚫 Danh sách chặn",
    'admin_search_user': "🔍 Tìm người dùng",
    'admin_maintenance': "🛠 Bảo trì",
    'admin_list_keys': "📋 Lịch sử Key",
    'admin_broadcast': "📣 Gửi thông báo",
    'admin_gen_key': "🗝 Tạo mã Key",
    'admin_list_live_cc': "💳 DS CC Live",
    'admin_proxy_mgmt': "🌐 Quản lý Proxy",
    'admin_add_proxies': "📥 Nạp Proxy (.txt)",
    'admin_list_proxies': "📋 Danh sách Proxy",
}

BACK_BUTTON_LABEL = "🔙 Quay lại"
BACK_MAIN_BUTTON_LABEL = "🔙 Quay lại Menu chính"
BACK_ADMIN_BUTTON_LABEL = "🔙 Quay lại Menu Admin"


def get_ui_label(key: str) -> str:
    """Lấy label UI dùng chung để icon đồng nhất giữa các file."""
    return UI_LABELS.get(key, key)


def get_service_display_name(service_id: str) -> str:
    """Lấy tên hiển thị của dịch vụ theo cùng một hệ icon."""
    return get_ui_label(service_id)


def get_welcome_message(full_name: str, invited_by: bool = False) -> str:
    """Xử lý lệnh /start"""
    msg = (
        f"🙋‍♂️ <b>Chào mừng, {full_name}！</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    if invited_by:
        msg += "🎁 <i>Cảm ơn bạn đã tham gia qua link mời, người mời đã được tặng <b>2 điểm</b>.</i>\n"

    msg += (
        "\n⚡ <b>Hệ thống xác thực tự động 24/7</b>\n"
        "Vui lòng chọn một hành động bên dưới để bắt đầu:"
    )
    return msg


def get_welcome_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Lấy bàn phím cho tin nhắn chào mừng"""
    keyboard = [
        [
            InlineKeyboardButton(get_ui_label('verify_menu'), callback_data='verify_menu'),
        ],
        [
            InlineKeyboardButton(get_ui_label('check_cookie_netflix'), callback_data='netflix_check'),
            InlineKeyboardButton(get_ui_label('convert_url_login_app_netflix'),
                                 callback_data='convert_url_login_app_netflix')
        ],
        [
            InlineKeyboardButton(get_ui_label('check_cc'), callback_data='check_cc_menu'),
        ],
        [
            InlineKeyboardButton(get_ui_label('discord_quest_auto'), callback_data='discord_quest'),
        ],
        [
            InlineKeyboardButton(get_ui_label('invite'), callback_data='invite'),
            InlineKeyboardButton(get_ui_label('checkin'), callback_data='checkin')

        ],
        [
            InlineKeyboardButton(get_ui_label('to_up'), callback_data='to_up'),
            InlineKeyboardButton(get_ui_label('help'), callback_data='help')
        ]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(get_ui_label('admin_menu'), callback_data='admin_menu')])

    return InlineKeyboardMarkup(keyboard)


def get_verify_menu_message() -> str:
    """Lấy tin nhắn cho menu xác thực"""
    return (
        "Chọn một dịch vụ bạn muốn xác thực bên dưới.\n\n"
        f"Lưu ý: Mỗi lần xác thực thành công sẽ tốn 💰 {VERIFY_COST} điểm."
    )


def get_verify_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho các lệnh xác thực"""
    keyboard = [
        [InlineKeyboardButton(get_ui_label('verify_chatgpt_k12'), callback_data='verify_chatgpt_k12')],
        [InlineKeyboardButton(get_ui_label('verify_spotify_student'), callback_data='verify_spotify_student')],
        [InlineKeyboardButton(get_ui_label('verify_bolt_teacher'), callback_data='verify_bolt_teacher')],
        [InlineKeyboardButton(get_ui_label('verify_youtube_student'), callback_data='verify_youtube_student')],
        [InlineKeyboardButton(get_ui_label('verify_gemini_pro'), callback_data='verify_gemini_pro')],
        [InlineKeyboardButton(BACK_BUTTON_LABEL, callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_message() -> str:
    """Lấy tin nhắn cho menu quản trị"""
    return "Chào mừng quản trị viên. Vui lòng chọn một hành động:"


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho menu quản trị"""
    keyboard = [
        [
            InlineKeyboardButton(get_ui_label('admin_add_balance'), callback_data='admin_add_balance'),
            InlineKeyboardButton(get_ui_label('admin_block'), callback_data='admin_block')
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_unblock'), callback_data='admin_unblock'),
            InlineKeyboardButton(get_ui_label('admin_blacklist'), callback_data='admin_blacklist')
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_search_user'), callback_data='admin_search_user'),
            InlineKeyboardButton(get_ui_label('admin_maintenance'), callback_data='admin_maintenance')
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_list_keys'), callback_data='admin_list_keys'),
            InlineKeyboardButton(get_ui_label('admin_broadcast'), callback_data='admin_broadcast')
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_gen_key'), callback_data='admin_gen_key'),
            InlineKeyboardButton(get_ui_label('admin_list_live_cc'), callback_data='admin_list_live_cc')
        ],
        [
            InlineKeyboardButton(get_ui_label('admin_proxy_mgmt'), callback_data='admin_proxy_mgmt')
        ],
        [
            InlineKeyboardButton(BACK_BUTTON_LABEL, callback_data='back_to_main')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_proxy_mgmt_keyboard() -> InlineKeyboardMarkup:
    """Bàn phím quản lý Proxy cho Admin"""
    keyboard = [
        [
            InlineKeyboardButton(get_ui_label('admin_add_proxies'), callback_data='admin_add_proxies'),
            InlineKeyboardButton(get_ui_label('admin_list_proxies'), callback_data='admin_list_proxies')
        ],
        [
            InlineKeyboardButton(BACK_ADMIN_BUTTON_LABEL, callback_data='admin_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_maintenance_keyboard(services_status: dict) -> InlineKeyboardMarkup:
    """Lấy bàn phím quản lý bảo trì cho Admin"""
    keyboard = []

    # Mapping ID nội bộ sang tên hiển thị
    for svc_id, is_maintenance in services_status.items():
        name = get_service_display_name(svc_id)
        status_icon = "🛠 BẢO TRÌ" if is_maintenance else "✅ HOẠT ĐỘNG"

        # Một hàng gồm 2 cột: Tên dịch vụ và Nút đảo trạng thái
        keyboard.append([
            InlineKeyboardButton(f"{name}", callback_data="noop"),
            InlineKeyboardButton(f"{status_icon}", callback_data=f"toggle_m:{svc_id}")
        ])

    keyboard.append([InlineKeyboardButton(BACK_ADMIN_BUTTON_LABEL, callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_help_message() -> str:
    """Lấy tin nhắn trợ giúp"""
    verify_label = get_ui_label('verify_menu')
    check_cc_label = get_ui_label('check_cc')
    netflix_check_label = get_ui_label('check_cookie_netflix')
    netflix_link_label = get_ui_label('convert_url_login_app_netflix')
    discord_label = get_ui_label('discord_quest_auto')

    return (
        "💡 HƯỚNG DẪN SỬ DỤNG\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{verify_label}:\n"
        f"Nhấn nút '{verify_label}' và gửi link:\n"
        f"• ChatGPT Teacher K12 (-💰 {VERIFY_COST})\n"
        f"• Spotify Student (-💰 {VERIFY_COST})\n"
        f"• Bolt new Teacher (-💰 {VERIFY_COST})\n"
        f"• YouTube Premium (-💰 {VERIFY_COST})\n"
        f"• Gemini One Pro (-💰 {VERIFY_COST})\n\n"
        f"{check_cc_label}:\n"
        f"Sử dụng lệnh <code>/check_cc</code> hoặc nút '{check_cc_label}':\n"
        f"• Gửi: <code>số thẻ|tháng|năm|cvv</code> (-💰 {VERIFY_COST})\n\n"
        f"{netflix_check_label}:\n"
        f"Nhấn nút '{netflix_check_label}' hoặc dùng lệnh <code>/check_cookie_netflix</code>:\n"
        f"• Gửi file .txt hoặc .json chứa cookie để kiểm tra (-💰 {VERIFY_COST}).\n\n"
        f"{netflix_link_label}:\n"
        f"Nhấn nút '{netflix_link_label}' hoặc dùng lệnh <code>/convert_netflix_url</code>:\n"
        "• Lấy link đăng nhập App Netflix từ cookie.\n\n"
        f"{discord_label}:\n"
        f"Sử dụng nút '{discord_label}':\n"
        f"• Nhập Discord Token để tự động hoàn thành Quest (-💰 {DISCORD_QUEST_COST}).\n\n"
        "💬 <i>Hỗ trợ trực tiếp: @hcongdev</i>"
    )


def get_insufficient_balance_message(current_balance: int) -> str:
    """Lấy tin nhắn số dư không đủ"""
    return (
        f"Số dư không đủ! Cần 💰 {VERIFY_COST} điểm, hiện có 💰 {current_balance} điểm.\n\n"
        "Cách nhận điểm:\n"
        "- Điểm danh hằng ngày\n"
        "- Mời bạn bè\n"
        "- Nạp điểm"
    )


def get_verify_usage_message(service_name: str) -> str:
    """Lấy thông tin hướng dẫn sử dụng lệnh xác thực cho ForceReply"""
    return (
        f"Bạn đã chọn xác thực: {service_name}\n\n"
        "Vui lòng nhập hoặc dán liên kết SheerID vào tin nhắn trả lời bên dưới:"
    )
