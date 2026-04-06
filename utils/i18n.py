"""Helpers cho đa ngôn ngữ của bot."""

from typing import Optional

DEFAULT_LANGUAGE = "vi"
SUPPORTED_LANGUAGES = ("en", "vi")
SUPPORTED_LANGUAGE_SET = set(SUPPORTED_LANGUAGES)

LANGUAGE_BUTTONS = {
    "en": "🇬🇧 English",
    "vi": "🇻🇳 Tiếng Việt",
}

TRANSLATIONS = {
    "vi": {
        "ui.verify_menu": "🎓 Xác thực SheerID",
        "ui.netflix_menu": "🎬 Netflix",
        "ui.get_cookie_netflix": "🍪 Lấy Cookie Netflix",
        "ui.check_cookie_netflix": "🍪 Check Cookie Netflix",
        "ui.convert_url_login_app_netflix": "📱 Login App Netflix",
        "ui.check_cc": "💳 Check CC",
        "ui.discord_quest_auto": "🚀 Discord Quest Auto",
        "ui.invite": "👥 Mời bạn bè",
        "ui.checkin": "📅 Điểm danh",
        "ui.to_up": "💰 Nạp điểm",
        "ui.help": "💡 Trợ giúp",
        "ui.admin_menu": "🛠 Quản trị viên",
        "ui.admin_users": "👤 Users",
        "ui.admin_key_menu": "🗝 Key",
        "ui.verify_chatgpt_k12": "🎓 ChatGPT Teacher K12",
        "ui.verify_spotify_student": "🎵 Spotify Student",
        "ui.verify_bolt_teacher": "⚡ Bolt.new Teacher",
        "ui.verify_youtube_student": "▶️ YouTube Premium",
        "ui.verify_gemini_pro": "🤖 Gemini One Pro",
        "ui.admin_add_balance": "💰 Cộng điểm",
        "ui.admin_block": "🔒 Khóa User",
        "ui.admin_unblock": "🔓 Mở khóa User",
        "ui.admin_blacklist": "🚫 Danh sách chặn",
        "ui.admin_search_user": "🔍 Tìm người dùng",
        "ui.admin_maintenance": "🛠 Bảo trì",
        "ui.admin_list_keys": "📋 Lịch sử Key",
        "ui.admin_broadcast": "📣 Gửi thông báo",
        "ui.admin_gen_key": "🗝 Tạo mã Key",
        "ui.admin_list_live_cc": "💳 DS CC Live",
        "ui.admin_upload_netflix_cookies": "📥 Nạp Cookie Netflix",
        "ui.admin_proxy_mgmt": "🌐 Quản lý Proxy",
        "ui.admin_add_proxies": "📥 Nạp Proxy (.txt)",
        "ui.admin_list_proxies": "📋 Danh sách Proxy",
        "nav.back": "🔙 Quay lại",
        "nav.back_main": "🔙 Quay lại Menu chính",
        "nav.back_admin": "🔙 Quay lại Menu Admin",
        "language.select.title": "🌐 <b>Please choose your language</b>",
        "language.select.body": "Select the language you want to use with this bot.",
        "language.select.required": "Please choose your language first.",
        "language.select.message": "You need to choose a language before continuing.",
        "language.saved": "✅ Đã lưu ngôn ngữ của bạn.",
        "language.saved.current": "Bạn đang dùng: 🇻🇳 Tiếng Việt",
        "language.saved.alert": "Đã lưu ngôn ngữ.",
        "main.title": "<b>🤖 HỆ THỐNG BOT ĐA NHIỆM</b>",
        "main.balance": "💰 Số dư: <b>{balance} điểm</b>",
        "main.prompt": "✨ <i>Vui lòng chọn chức năng:</i>",
        "welcome.header": "🙋‍♂️ <b>Chào mừng, {full_name}!</b>\n━━━━━━━━━━━━━━━━━━━━\n",
        "welcome.invited": "🎁 <i>Cảm ơn bạn đã tham gia qua link mời, người mời đã được tặng <b>2 điểm</b>.</i>\n",
        "welcome.footer": "\n⚡ <b>Hệ thống xác thực tự động 24/7</b>\nVui lòng chọn một hành động bên dưới để bắt đầu:",
        "welcome.back": "Chào mừng {full_name} quay trở lại!",
        "start.no_username": (
            "⚠️ <b>Lỗi: Không có Username</b>\n\n"
            "Tài khoản Telegram của bạn chưa thiết lập <b>Username</b>. "
            "Để sử dụng Bot này, bạn cần vào mục Settings (Cài đặt) của Telegram để đặt Username, "
            "sau đó quay lại đây bấm /start.\n\n"
            "<i>(Lưu ý: Username giúp Bot định danh và bảo vệ tài khoản của bạn tốt hơn)</i>"
        ),
        "prompt.cancel_hint": "Hoặc nhấn nút bên dưới để hủy:",
        "action.cancel": "❌ Hủy",
        "busy.summary": (
            "⚠️ <b>Bạn đang thực hiện chức năng: {service_name}</b>\n\n"
            "Vui lòng hoàn thành hoặc nhấn nút <b>❌ Hủy</b> của chức năng đó trước khi bắt đầu hành động mới."
        ),
        "busy.callback": "Vui lòng Hủy chức năng {service_name} trước!",
        "busy.message": (
            "<b>⚠️ TRẠNG THÁI: BẬN</b>\n\n"
            "Bạn đang thực hiện một thao tác khác. Vui lòng hoàn tất hoặc nhấn nút bên dưới để đóng nhập liệu cũ:"
        ),
        "busy.close_old": "❌ Đóng nhập liệu cũ",
        "service.other": "một chức năng khác",
        "service.verify_chatgpt_k12": "Xác thực ChatGPT Teacher K12",
        "service.verify_spotify_student": "Xác thực Spotify Student",
        "service.verify_bolt_teacher": "Xác thực Bolt.new Teacher",
        "service.verify_youtube_student": "Xác thực YouTube Student",
        "service.verify_gemini_pro": "Xác thực Gemini One Pro",
        "service.convert_url_login_app_netflix": "Login App Netflix",
        "service.get_cookie_netflix": "Lấy Cookie Netflix",
        "service.check_cookie_netflix_step_1": "Check Cookie Netflix",
        "service.discord_quest": "Discord Quest Auto",
        "service.check_cc_step_1": "💳 Check CC",
        "service.use_key_step_1": "Nạp mã Key (Nạp điểm)",
        "service.admin_add_balance_step_1": "Admin: Cộng điểm",
        "service.admin_block_step_1": "Admin: Chặn người dùng",
        "service.admin_unblock_step_1": "Admin: Bỏ chặn người dùng",
        "service.admin_gen_key_step_1": "Admin: Tạo mã Key",
        "service.admin_upload_netflix_cookies_step_1": "Admin: Nạp Cookie Netflix",
        "menu.verify.message": (
            "Chọn một dịch vụ bạn muốn xác thực bên dưới.\n\n"
            "Lưu ý: Mỗi lần xác thực thành công sẽ tốn 💰 {verify_cost} điểm."
        ),
        "menu.netflix.message": (
            "🎬 <b>NETFLIX TOOLKIT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Chọn chức năng Netflix bạn muốn dùng bên dưới."
        ),
        "menu.admin.message": "Chào mừng quản trị viên. Vui lòng chọn một hành động:",
        "menu.admin_users.message": (
            "👤 <b>QUẢN LÝ USERS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Chọn chức năng quản lý người dùng:"
        ),
        "menu.admin_keys.message": (
            "🗝 <b>QUẢN LÝ KEY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Chọn chức năng quản lý key:"
        ),
        "menu.proxy.message": (
            "🌐 <b>QUẢN LÝ PROXY HỆ THỐNG</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Chọn hành động bên dưới:"
        ),
        "help.title": "💡 HƯỚNG DẪN SỬ DỤNG\n━━━━━━━━━━━━━━━━━━━━\n",
        "help.support": "💬 <i>Hỗ trợ trực tiếp: @hcongdev</i>",
        "invite.message": (
            "💰 Link mời của bạn:\n{invite_link}\n\n"
            "Mời thành công 1 người bạn sẽ nhận được 1 điểm."
        ),
        "checkin.success": "✅ Điểm danh thành công! +1 điểm\n💰 Số dư hiện tại: {balance} điểm.",
        "checkin.already": "❌ Hôm nay bạn đã điểm danh rồi.",
        "balance.current": "💰 Số dư hiện tại của bạn: {balance} điểm.",
        "topup.prompt": "Vui lòng nhập mã thẻ:",
        "key.not_found": "Mã thẻ không tồn tại.",
        "key.used_up": "Mã đã hết lượt sử dụng.",
        "key.expired": "Mã đã hết hạn.",
        "key.already_used": "Bạn đã dùng mã này rồi.",
        "common.unknown_error": "Lỗi không xác định.",
        "key.success": "Sử dụng mã thẻ thành công! +{amount} điểm.\n💰 Số dư hiện tại: {balance} điểm.",
        "verify.usage": (
            "Bạn đã chọn xác thực: {service_name}\n\n"
            "Vui lòng nhập hoặc dán liên kết SheerID vào tin nhắn trả lời bên dưới:"
        ),
        "balance.insufficient": (
            "Số dư không đủ! Cần 💰 {verify_cost} điểm, hiện có 💰 {current_balance} điểm.\n\n"
            "Cách nhận điểm:\n"
            "- Điểm danh hằng ngày\n"
            "- Mời bạn bè\n"
            "- Nạp điểm"
        ),
        "checks.group": (
            "⚠️ <b>Bot không hỗ trợ xử lý trong Nhóm.</b>\n\n"
            "Vui lòng nhấn vào @{bot_username} để nhắn tin riêng (Inbox) và sử dụng đầy đủ các tính năng xác thực, nạp điểm, v.v."
        ),
        "checks.blocked.alert": "Tài khoản của bạn đã bị khóa.",
        "checks.blocked": "🚫 Tài khoản của bạn đã bị khóa. Liên hệ @hcongdev để biết thêm.",
        "checks.maintenance": (
            "🛠 <b>DỊCH VỤ ĐANG BẢO TRÌ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Hiện tại tính năng này đang được bảo trì để nâng cấp. Vui lòng quay lại sau ít phút!"
        ),
        "maintenance.menu": (
            "🛠 <b>QUẢN LÝ BẢO TRÌ DỊCH VỤ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Bạn có thể bật hoặc tắt trạng thái bảo trì cho từng dịch vụ bên dưới.\n"
            "<i>Lưu ý: Hệ thống sẽ tự động gửi thông báo cho toàn bộ người dùng khi thay đổi.</i>"
        ),
        "maintenance.status.on": "🛠 BẢO TRÌ",
        "maintenance.status.off": "✅ HOẠT ĐỘNG",
        "maintenance.error_service": "❌ Lỗi: Không biên dịch được dịch vụ.",
        "maintenance.notice.on": (
            "🛠 <b>THÔNG BÁO BẢO TRÌ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Dịch vụ <b>{service_name}</b> hiện đang được tạm dừng để <b>bảo trì hệ thống</b>.\n\n"
            "🕒 Chúng tôi sẽ có thông báo ngay khi dịch vụ hoạt động trở lại. Xin lỗi vì sự bất tiện này!"
        ),
        "maintenance.notice.off": (
            "✅ <b>THÔNG BÁO HOÀN TẤT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Dịch vụ <b>{service_name}</b> đã hoàn tất bảo trì và <b>hoạt động trở lại</b> bình thường.\n\n"
            "🚀 Bạn có thể tiếp tục sử dụng dịch vụ ngay bây giờ. Cảm ơn bạn!"
        ),
    },
    "en": {
        "ui.verify_menu": "🎓 SheerID Verification",
        "ui.netflix_menu": "🎬 Netflix",
        "ui.get_cookie_netflix": "🍪 Get Netflix Cookie",
        "ui.check_cookie_netflix": "🍪 Check Netflix Cookie",
        "ui.convert_url_login_app_netflix": "📱 Netflix App Login",
        "ui.check_cc": "💳 Check CC",
        "ui.discord_quest_auto": "🚀 Discord Quest Auto",
        "ui.invite": "👥 Invite Friends",
        "ui.checkin": "📅 Daily Check-in",
        "ui.to_up": "💰 Top Up",
        "ui.help": "💡 Help",
        "ui.admin_menu": "🛠 Admin",
        "ui.admin_users": "👤 Users",
        "ui.admin_key_menu": "🗝 Keys",
        "ui.verify_chatgpt_k12": "🎓 ChatGPT Teacher K12",
        "ui.verify_spotify_student": "🎵 Spotify Student",
        "ui.verify_bolt_teacher": "⚡ Bolt.new Teacher",
        "ui.verify_youtube_student": "▶️ YouTube Premium",
        "ui.verify_gemini_pro": "🤖 Gemini One Pro",
        "ui.admin_add_balance": "💰 Add Balance",
        "ui.admin_block": "🔒 Block User",
        "ui.admin_unblock": "🔓 Unblock User",
        "ui.admin_blacklist": "🚫 Blacklist",
        "ui.admin_search_user": "🔍 Find User",
        "ui.admin_maintenance": "🛠 Maintenance",
        "ui.admin_list_keys": "📋 Key History",
        "ui.admin_broadcast": "📣 Broadcast",
        "ui.admin_gen_key": "🗝 Create Key",
        "ui.admin_list_live_cc": "💳 Live CC List",
        "ui.admin_upload_netflix_cookies": "📥 Upload Netflix Cookies",
        "ui.admin_proxy_mgmt": "🌐 Proxy Manager",
        "ui.admin_add_proxies": "📥 Upload Proxies (.txt)",
        "ui.admin_list_proxies": "📋 Proxy List",
        "nav.back": "🔙 Back",
        "nav.back_main": "🔙 Back to Main Menu",
        "nav.back_admin": "🔙 Back to Admin Menu",
        "language.select.title": "🌐 <b>Please choose your language</b>",
        "language.select.body": "Select the language you want to use with this bot.",
        "language.select.required": "Please choose your language first.",
        "language.select.message": "You need to choose a language before continuing.",
        "language.saved": "✅ Your language has been saved.",
        "language.saved.current": "You are now using: 🇬🇧 English",
        "language.saved.alert": "Language saved.",
        "main.title": "<b>🤖 MULTI-TASK BOT SYSTEM</b>",
        "main.balance": "💰 Balance: <b>{balance} points</b>",
        "main.prompt": "✨ <i>Please choose a feature:</i>",
        "welcome.header": "🙋‍♂️ <b>Welcome, {full_name}!</b>\n━━━━━━━━━━━━━━━━━━━━\n",
        "welcome.invited": "🎁 <i>Thanks for joining through an invite link. Your inviter has received <b>2 points</b>.</i>\n",
        "welcome.footer": "\n⚡ <b>24/7 automated verification system</b>\nPlease choose an action below to get started:",
        "welcome.back": "Welcome back, {full_name}!",
        "start.no_username": (
            "⚠️ <b>Error: No Username</b>\n\n"
            "Your Telegram account does not have a <b>Username</b> set. "
            "To use this bot, open Telegram Settings and set a username, "
            "then come back here and press /start.\n\n"
            "<i>(Note: A username helps the bot identify and protect your account better.)</i>"
        ),
        "prompt.cancel_hint": "Or tap the button below to cancel:",
        "action.cancel": "❌ Cancel",
        "busy.summary": (
            "⚠️ <b>You are currently using: {service_name}</b>\n\n"
            "Please finish it or tap <b>❌ Cancel</b> for that feature before starting a new action."
        ),
        "busy.callback": "Please cancel {service_name} first!",
        "busy.message": (
            "<b>⚠️ STATUS: BUSY</b>\n\n"
            "You are currently doing something else. Please finish it or tap the button below to close the old input:"
        ),
        "busy.close_old": "❌ Close old input",
        "service.other": "another feature",
        "service.verify_chatgpt_k12": "ChatGPT Teacher K12 Verification",
        "service.verify_spotify_student": "Spotify Student Verification",
        "service.verify_bolt_teacher": "Bolt.new Teacher Verification",
        "service.verify_youtube_student": "YouTube Student Verification",
        "service.verify_gemini_pro": "Gemini One Pro Verification",
        "service.convert_url_login_app_netflix": "Netflix App Login",
        "service.get_cookie_netflix": "Get Netflix Cookie",
        "service.check_cookie_netflix_step_1": "Check Netflix Cookie",
        "service.discord_quest": "Discord Quest Auto",
        "service.check_cc_step_1": "💳 Check CC",
        "service.use_key_step_1": "Top Up by Key",
        "service.admin_add_balance_step_1": "Admin: Add Balance",
        "service.admin_block_step_1": "Admin: Block User",
        "service.admin_unblock_step_1": "Admin: Unblock User",
        "service.admin_gen_key_step_1": "Admin: Create Key",
        "service.admin_upload_netflix_cookies_step_1": "Admin: Upload Netflix Cookies",
        "menu.verify.message": (
            "Choose the service you want to verify below.\n\n"
            "Note: Each successful verification costs 💰 {verify_cost} points."
        ),
        "menu.netflix.message": (
            "🎬 <b>NETFLIX TOOLKIT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose the Netflix feature you want to use below."
        ),
        "menu.admin.message": "Welcome, admin. Please choose an action:",
        "menu.admin_users.message": (
            "👤 <b>USER MANAGEMENT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose a user management action:"
        ),
        "menu.admin_keys.message": (
            "🗝 <b>KEY MANAGEMENT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose a key management action:"
        ),
        "menu.proxy.message": (
            "🌐 <b>SYSTEM PROXY MANAGEMENT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose an action below:"
        ),
        "help.title": "💡 HOW TO USE\n━━━━━━━━━━━━━━━━━━━━\n",
        "help.support": "💬 <i>Direct support: @hcongdev</i>",
        "invite.message": (
            "💰 Your invite link:\n{invite_link}\n\n"
            "You will receive 1 point for each successful invite."
        ),
        "checkin.success": "✅ Check-in successful! +1 point\n💰 Current balance: {balance} points.",
        "checkin.already": "❌ You have already checked in today.",
        "balance.current": "💰 Your current balance: {balance} points.",
        "topup.prompt": "Please enter your card key:",
        "key.not_found": "Card key not found.",
        "key.used_up": "This key has no remaining uses.",
        "key.expired": "This key has expired.",
        "key.already_used": "You have already used this key.",
        "common.unknown_error": "Unknown error.",
        "key.success": "Card key used successfully! +{amount} points.\n💰 Current balance: {balance} points.",
        "verify.usage": (
            "You selected verification: {service_name}\n\n"
            "Please enter or paste the SheerID link in the reply message below:"
        ),
        "balance.insufficient": (
            "Insufficient balance! Need 💰 {verify_cost} points, you currently have 💰 {current_balance} points.\n\n"
            "Ways to get points:\n"
            "- Daily check-in\n"
            "- Invite friends\n"
            "- Top up"
        ),
        "checks.group": (
            "⚠️ <b>This bot does not support group chats.</b>\n\n"
            "Please tap @{bot_username} and message the bot privately to use verification, top-up, and other features."
        ),
        "checks.blocked.alert": "Your account has been blocked.",
        "checks.blocked": "🚫 Your account has been blocked. Contact @hcongdev for more details.",
        "checks.maintenance": (
            "🛠 <b>SERVICE UNDER MAINTENANCE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "This feature is currently under maintenance for upgrades. Please try again in a few minutes."
        ),
        "maintenance.menu": (
            "🛠 <b>SERVICE MAINTENANCE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "You can turn maintenance mode on or off for each service below.\n"
            "<i>Note: The system will automatically broadcast updates to all users when the status changes.</i>"
        ),
        "maintenance.status.on": "🛠 MAINTENANCE",
        "maintenance.status.off": "✅ ACTIVE",
        "maintenance.error_service": "❌ Error: Could not resolve the service.",
        "maintenance.notice.on": (
            "🛠 <b>MAINTENANCE NOTICE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The <b>{service_name}</b> service is temporarily paused for <b>system maintenance</b>.\n\n"
            "🕒 We will notify you as soon as it is available again. Sorry for the inconvenience."
        ),
        "maintenance.notice.off": (
            "✅ <b>MAINTENANCE COMPLETED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The <b>{service_name}</b> service has finished maintenance and is <b>available again</b>.\n\n"
            "🚀 You can continue using it now. Thank you."
        ),
    },
}


def normalize_language(language: Optional[str], default: Optional[str] = DEFAULT_LANGUAGE) -> Optional[str]:
    """Chuẩn hóa mã ngôn ngữ."""
    if not language:
        return default

    normalized = language.lower().strip()
    if normalized in SUPPORTED_LANGUAGE_SET:
        return normalized
    return default


def has_selected_language(language: Optional[str]) -> bool:
    """Kiểm tra user đã chọn ngôn ngữ hợp lệ hay chưa."""
    if not language:
        return False
    return language.lower().strip() in SUPPORTED_LANGUAGE_SET


def tr(language: Optional[str], key: str, **kwargs) -> str:
    """Lấy chuỗi theo ngôn ngữ."""
    normalized = normalize_language(language, default=DEFAULT_LANGUAGE)
    text = TRANSLATIONS.get(normalized, {}).get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs)


def get_user_language(db, user_id: int, default: Optional[str] = DEFAULT_LANGUAGE) -> Optional[str]:
    """Lấy ngôn ngữ user từ database."""
    language = None
    if hasattr(db, "get_user_language"):
        language = db.get_user_language(user_id)
    elif hasattr(db, "get_user"):
        user = db.get_user(user_id)
        language = user.get("language") if user else None
    return normalize_language(language, default=default)
