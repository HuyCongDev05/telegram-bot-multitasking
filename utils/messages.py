"""Mẫu tin nhắn"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import VERIFY_COST


def get_welcome_message(full_name: str, invited_by: bool = False) -> str:
    """Lấy tin nhắn chào mừng"""
    msg = (
        f"🎉 Chào mừng, {full_name}！\n"
    )
    if invited_by:
        msg += "Cảm ơn bạn đã tham gia qua liên kết mời, người mời đã nhận được 2 điểm.\n"

    msg += (
        "\nVui lòng chọn một hành động từ các nút bên dưới:"
    )
    return msg


def get_welcome_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Lấy bàn phím cho tin nhắn chào mừng"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Xác thực SheerID", callback_data='verify_menu'),
        ],
        [
            InlineKeyboardButton("📺 Chuyển đổi url login app netflix", callback_data='convert_url_login_app_netflix'),
        ],
        [
            InlineKeyboardButton("🎁 Mời bạn bè", callback_data='invite'),
            InlineKeyboardButton("📅 Điểm danh", callback_data='checkin')

        ],
        [
            InlineKeyboardButton("💳 Nạp điểm", callback_data='to_up'),
            InlineKeyboardButton("❓ Trợ giúp", callback_data='help')
        ]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Quản trị", callback_data='admin_menu')])

    return InlineKeyboardMarkup(keyboard)


def get_verify_menu_message() -> str:
    """Lấy tin nhắn cho menu xác thực"""
    return (
        "Chọn một dịch vụ bạn muốn xác thực bên dưới.\n\n"
        f"Lưu ý: Mỗi lần xác thực thành công sẽ tốn 🪙 {VERIFY_COST} điểm."
    )


def get_verify_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho các lệnh xác thực"""
    keyboard = [
        [InlineKeyboardButton("🎓 ChatGPT Teacher K12", callback_data='verify_chatgpt_k12')],
        [InlineKeyboardButton("🎵 Spotify Student", callback_data='verify_spotify_student')],
        [InlineKeyboardButton("⚡ Bolt.new Teacher", callback_data='verify_bolt_teacher')],
        [InlineKeyboardButton("📺 YouTube Student", callback_data='verify_youtube_student')],
        [InlineKeyboardButton("🧠 Gemini One Pro", callback_data='verify_gemini_pro')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_message() -> str:
    """Lấy tin nhắn cho menu quản trị"""
    return "Chào mừng quản trị viên. Vui lòng chọn một hành động:"


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Lấy bàn phím cho menu quản trị"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Thêm điểm", callback_data='admin_add_balance'),
            InlineKeyboardButton("🚫 Chặn", callback_data='admin_block')
        ],
        [
            InlineKeyboardButton("✅ Bỏ chặn", callback_data='admin_unblock'),
            InlineKeyboardButton("📋 DS Đen", callback_data='admin_blacklist')
        ],
        [
            InlineKeyboardButton("🔑 Tạo key", callback_data='admin_gen_key'),
            InlineKeyboardButton("📜 DS Key", callback_data='admin_list_keys')
        ],
        [
            InlineKeyboardButton("📢 Thông báo", callback_data='admin_broadcast'),
            InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_help_message() -> str:
    """Lấy tin nhắn trợ giúp"""
    return (
        "📖 Hướng dẫn xác thực:\n\n"
        "Nhấn nút '🔍 Xác thực SheerID' ở menu chính, chọn dịch vụ và gửi liên kết:\n"
        f"• ChatGPT Teacher K12 - <liên kết> (-🪙 {VERIFY_COST} điểm)\n"
        f"• Spotify Student - <liên kết> (-🪙 {VERIFY_COST} điểm)\n"
        f"• Bolt new Teacher - <liên kết> (-🪙 {VERIFY_COST} điểm)\n"
        f"• YouTube Premium Student - <liên kết> (-🪙 {VERIFY_COST} điểm)\n"
        f"• Gemini One Pro - <liên kết> (-🪙 {VERIFY_COST} điểm)\n\n"
        "📖 Hướng dẫn lấy url đăng nhập app netflix:\n\n"
        "Nhấn nút '📺 Chuyển đổi url login app netflix' ở menu chính:\n"
        f"• Nhập cookie netflix vào để chuyển đổi (-🪙 {VERIFY_COST} điểm)\n\n"
        "💬 Mọi thắc mắc liên hệ @hcongdev"
    )


def get_insufficient_balance_message(current_balance: int) -> str:
    """Lấy tin nhắn số dư không đủ"""
    return (
        f"Số dư không đủ! Cần 🪙 {VERIFY_COST} điểm, hiện có 🪙 {current_balance} điểm.\n\n"
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
