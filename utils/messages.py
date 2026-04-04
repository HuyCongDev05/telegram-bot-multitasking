"""Mẫu tin nhắn"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import VERIFY_COST, DISCORD_QUEST_COST


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
            InlineKeyboardButton("✨ Xác thực SheerID", callback_data='verify_menu'),
        ],
        [
            InlineKeyboardButton("🎬 Chuyển đổi Netflix Cookie", callback_data='convert_url_login_app_netflix'),
        ],
        [
            InlineKeyboardButton("💳 Check CC", callback_data='check_cc_menu'),
        ],
        [
            InlineKeyboardButton("🚀 Discord Quest Auto", callback_data='discord_quest'),
        ],
        [
            InlineKeyboardButton("🧧 Mời bạn bè", callback_data='invite'),
            InlineKeyboardButton("💎 Điểm danh", callback_data='checkin')

        ],
        [
            InlineKeyboardButton("💳 Nạp điểm", callback_data='to_up'),
            InlineKeyboardButton("💡 Trợ giúp", callback_data='help')
        ]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("🛠 Quản trị viên", callback_data='admin_menu')])

    return InlineKeyboardMarkup(keyboard)


def get_verify_menu_message() -> str:
    """Lấy tin nhắn cho menu xác thực"""
    return (
        "Chọn một dịch vụ bạn muốn xác thực bên dưới.\n\n"
        f"Lưu ý: Mỗi lần xác thực thành công sẽ tốn 💎 {VERIFY_COST} điểm."
    )


def get_verify_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho các lệnh xác thực"""
    keyboard = [
        [InlineKeyboardButton("🎓 ChatGPT Teacher K12", callback_data='verify_chatgpt_k12')],
        [InlineKeyboardButton("🎵 Spotify Student", callback_data='verify_spotify_student')],
        [InlineKeyboardButton("⚡ Bolt.new Teacher", callback_data='verify_bolt_teacher')],
        [InlineKeyboardButton("🎥 YouTube Premium", callback_data='verify_youtube_student')],
        [InlineKeyboardButton("🤖 Gemini One Pro", callback_data='verify_gemini_pro')],
        [InlineKeyboardButton("🔙 Quay lại", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_message() -> str:
    """Lấy tin nhắn cho menu quản trị"""
    return "Chào mừng quản trị viên. Vui lòng chọn một hành động:"


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho menu quản trị"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Cộng tiền", callback_data='admin_add_balance'),
            InlineKeyboardButton("🔒 Khóa User", callback_data='admin_block')
        ],
        [
            InlineKeyboardButton("🔓 Mở khóa", callback_data='admin_unblock'),
            InlineKeyboardButton("💀 Danh sách đen", callback_data='admin_blacklist')
        ],
        [
            InlineKeyboardButton("🔍 Tìm người dùng", callback_data='admin_search_user'),
            InlineKeyboardButton("🛠 Bảo trì", callback_data='admin_maintenance')
        ],
        [
            InlineKeyboardButton("📊 Lịch sử Key", callback_data='admin_list_keys'),
            InlineKeyboardButton("📣 Gửi thông báo", callback_data='admin_broadcast')
        ],
        [
            InlineKeyboardButton("🗝 Tạo mã Key", callback_data='admin_gen_key'),
            InlineKeyboardButton("💳 DS CC Live", callback_data='admin_list_live_cc')
        ],
        [
            InlineKeyboardButton("🔙 Quay lại", callback_data='back_to_main')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_maintenance_keyboard(services_status: dict) -> InlineKeyboardMarkup:
    """Lấy bàn phím quản lý bảo trì cho Admin"""
    keyboard = []

    # Mapping ID nội bộ sang tên hiển thị
    service_names = {
        'verify_chatgpt_k12': '🎓 ChatGPT K12',
        'verify_spotify_student': '🎵 Spotify Student',
        'verify_bolt_teacher': '⚡ Bolt.new Teacher',
        'verify_youtube_student': '🎥 YouTube Premium Student',
        'verify_gemini_pro': '🤖 Gemini One Pro',
        'convert_url_login_app_netflix': '🎬 Netflix',
        'check_cc': '💳 Check CC',
        'discord_quest_auto': '🚀 Discord Quest Auto'
    }

    for svc_id, is_maintenance in services_status.items():
        name = service_names.get(svc_id, svc_id)
        status_icon = "🛠 BẢO TRÌ" if is_maintenance else "✅ HOẠT ĐỘNG"

        # Một hàng gồm 2 cột: Tên dịch vụ và Nút đảo trạng thái
        keyboard.append([
            InlineKeyboardButton(f"{name}", callback_data="noop"),
            InlineKeyboardButton(f"{status_icon}", callback_data=f"toggle_m:{svc_id}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 Quay lại menu Admin", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_help_message() -> str:
    """Lấy tin nhắn trợ giúp"""
    return (
        "💡 HƯỚNG DẪN SỬ DỤNG\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ Xác thực SheerID:\n"
        "Nhấn nút '✨ Xác thực SheerID' và gửi link:\n"
        f"• ChatGPT Teacher K12 (-💎 {VERIFY_COST})\n"
        f"• Spotify Student (-💎 {VERIFY_COST})\n"
        f"• Bolt new Teacher (-💎 {VERIFY_COST})\n"
        f"• YouTube Premium (-💎 {VERIFY_COST})\n"
        f"• Gemini One Pro (-💎 {VERIFY_COST})\n\n"
        "💳 Check CC:\n"
        "Sử dụng lệnh <code>/check_cc</code> hoặc nút '💳 Check CC':\n"
        f"• Gửi: <code>số thẻ|tháng|năm|cvv</code> (-💎 {VERIFY_COST})\n\n"
        "🎬 Chuyển đổi Netflix Cookie:\n"
        "Nhấn nút '🎬 Chuyển đổi Netflix Cookie':\n"
        f"• Nhập Cookie Netflix để lấy Link đăng nhập App.\n\n"
        "🚀 Discord Quest Auto:\n"
        "Sử dụng nút '🚀 Discord Quest Auto':\n"
        f"• Nhập Discord Token để tự động hoàn thành Quest (-💎 {DISCORD_QUEST_COST}).\n\n"
        "💬 <i>Hỗ trợ trực tiếp: @hcongdev</i>"
    )


def get_insufficient_balance_message(current_balance: int) -> str:
    """Lấy tin nhắn số dư không đủ"""
    return (
        f"Số dư không đủ! Cần 💎 {VERIFY_COST} điểm, hiện có 💎 {current_balance} điểm.\n\n"
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
