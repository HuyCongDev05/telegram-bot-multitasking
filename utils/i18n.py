# Helpers cho đa ngôn ngữ của bot.

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
        "ui.login_tv_netflix": "📺 Đăng nhập Netflix TV",
        "ui.check_cc": "💳 Check CC",
        "ui.discord_quest_auto": "🚀 Discord Quest Auto",
        "ui.invite": "👥 Mời bạn bè",
        "ui.checkin": "📅 Điểm danh",
        "ui.to_up": "🔑 Nhập Key",
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
        "ui.admin_export_users": "📥 Xuất FILE User",
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
        "service.login_tv_netflix_step_1": "Đăng nhập Netflix TV",
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
        "netflix.tv_login.prompt": (
            "📺 <b>ĐĂNG NHẬP NETFLIX TRÊN TV / SMART TV</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Hướng dẫn:\n"
            "1️⃣ Mở ứng dụng <b>Netflix</b> trên TV/Smart TV của bạn.\n"
            "2️⃣ Chọn <b>Đăng nhập</b> → <b>Đăng nhập bằng mã TV</b>.\n"
            "3️⃣ Màn hình sẽ hiển thị một <b>mã TV</b> (thường là 6–8 ký tự).\n\n"
            "📝 <i>Vui lòng nhập mã TV bạn thấy trên màn hình bên dưới:</i>"
        ),
        "netflix.tv_login.processing": "⏳ Đang đăng nhập Netflix TV của bạn, vui lòng chờ...",
        "netflix.tv_login.invalid_code": (
            "❌ <b>Mã TV không hợp lệ!</b>\n"
            "Mã TV chỉ được chứa chữ cái và chữ số.\n"
            "Vui lòng kiểm tra lại và nhập đúng mã hiển thị trên TV."
        ),
        "netflix.tv_login.not_implemented": (
            "🛠 <b>Chức năng đang được phát triển</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tính năng Đăng nhập Netflix TV hiện đang trong quá trình hoàn thiện.\n"
            "Vui lòng quay lại sau!"
        ),
        "netflix.tv_login.success": (
            "✅ <b>ĐĂNG NHẬP NETFLIX TV THÀNH CÔNG!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📺 Mã TV: <code>{tv_code}</code>\n\n"
            "🎉 TV của bạn đã được kết nối với tài khoản Netflix.\n"
            "Quay lại TV và tận hưởng Netflix ngay!"
        ),
        "netflix.tv_login.failed": (
            "❌ <b>ĐĂNG NHẬP THẤT BẠI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Không thể đăng nhập với mã TV: <code>{tv_code}</code>\n"
            "Lý do: {reason}\n\n"
            "💡 Thử lại hoặc lấy mã TV mới trên màn hình."
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
            "💰 <b>LINK MỜI BẠN BÈ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Nhấn vào link bên dưới để tự động sao chép:\n"
            "<code>{invite_link}</code>\n\n"
            "🎁 <i>Mỗi người bạn tham gia qua link này, bạn sẽ nhận được 1 điểm!</i>"
        ),
        "checkin.success": "✅ Điểm danh thành công! +1 điểm\n💰 Số dư hiện tại: {balance} điểm.",
        "checkin.already": "❌ Hôm nay bạn đã điểm danh rồi.",
        "balance.current": "💰 Số dư hiện tại của bạn: {balance} điểm.",
        "topup.prompt": "Vui lòng nhập Key:",
        "key.not_found": "Key không tồn tại.",
        "key.used_up": "Mã đã hết lượt sử dụng.",
        "key.expired": "Mã đã hết hạn.",
        "key.already_used": "Bạn đã dùng mã này rồi.",
        "common.unknown_error": "Lỗi không xác định.",
        "key.success": "Sử dụng Key thành công! +{amount} điểm.\n💰 Số dư hiện tại: {balance} điểm.",
        "key.one_use_per_user_hint": "Lưu ý: Mỗi người dùng chỉ có thể sử dụng mã này một lần duy nhất.",
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
        "discord.balance.insufficient": (
            "Số dư không đủ! Cần 💰 <b>{cost} điểm</b> để sử dụng Discord Quest Auto.\n\n"
            "Hiện có: 💰 <b>{current_balance} điểm</b>\n\n"
            "Cách nhận thêm điểm:\n"
            "- Điểm danh hằng ngày\n"
            "- Mời bạn bè\n"
            "- Nạp thêm điểm"
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
        "netflix.no_cookies_available": "❌ Hiện tại không có cookie Netflix nào khả dụng trong hệ thống. Vui lòng quay lại sau!",
        "netflix.random_login.processing": "⏳ Đang lấy cookie ngẫu nhiên và tạo link đăng nhập Netflix cho bạn...",
        "netflix.maintenance.check_cookie": "❌ <b>Thông báo:</b> Dịch vụ Check Cookie Netflix hiện đang bảo trì. Vui lòng quay lại sau!",
        "netflix.maintenance.get_cookie": "❌ <b>Thông báo:</b> Dịch vụ Lấy Cookie Netflix hiện đang bảo trì. Vui lòng quay lại sau!",
        "netflix.maintenance.login_tv": "❌ <b>Thông báo:</b> Dịch vụ Đăng nhập Netflix TV hiện đang bảo trì. Vui lòng quay lại sau!",
        "netflix.balance.insufficient": "❌ Số dư không đủ! Mỗi lần thực hiện tốn <b>{verify_cost} điểm</b>. Hiện có: {current_balance} điểm.",
        "admin.no_permission": "Bạn không có quyền sử dụng lệnh này.",
        "admin.user.block_notified": "❌ <b>Thông báo:</b> Tài khoản của bạn đã bị quản trị viên khóa. Liên hệ @hcongdev để biết thêm chi tiết.",
        "admin.user.unblock_notified": "✅ <b>Thông báo:</b> Tài khoản của bạn đã được quản trị viên bỏ chặn. Bạn đã có thể sử dụng lại hệ thống.",
        "cc.prompt.text": "Vui lòng nhập danh sách CC vào tin nhắn trả lời bên dưới (hoặc gửi file .txt).\nĐịnh dạng: <code>Số thẻ|Tháng|Năm|CVV</code>\nLưu ý: Phí mỗi lần check là 💰 {verify_cost} điểm (tối đa {max_cc} CC).",
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
        "ui.login_tv_netflix": "📺 Netflix TV Login",
        "ui.check_cc": "💳 Check CC",
        "ui.discord_quest_auto": "🚀 Discord Quest Auto",
        "ui.invite": "👥 Invite Friends",
        "ui.checkin": "📅 Daily Check-in",
        "ui.to_up": "🔑 Enter Key",
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
        "ui.admin_export_users": "📥 Export USER File",
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
        "service.login_tv_netflix_step_1": "Netflix TV Login",
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
        "netflix.tv_login.prompt": (
            "📺 <b>NETFLIX TV / SMART TV SIGN IN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "How to use:\n"
            "1️⃣ Open the <b>Netflix</b> app on your TV or Smart TV.\n"
            "2️⃣ Select <b>Sign In</b> → <b>Sign in with a TV code</b>.\n"
            "3️⃣ A <b>TV code</b> will appear on screen (usually 6–8 characters).\n\n"
            "📝 <i>Please type the TV code shown on your screen below:</i>"
        ),
        "netflix.tv_login.processing": "⏳ Signing in to your Netflix TV, please wait...",
        "netflix.tv_login.invalid_code": (
            "❌ <b>Invalid TV code!</b>\n"
            "The TV code must only contain letters and numbers.\n"
            "Please check the code displayed on your TV and try again."
        ),
        "netflix.tv_login.not_implemented": (
            "🛠 <b>Feature under development</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The Netflix TV Login feature is currently being developed.\n"
            "Please check back later!"
        ),
        "netflix.tv_login.success": (
            "✅ <b>NETFLIX TV LOGIN SUCCESSFUL!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📺 TV Code: <code>{tv_code}</code>\n\n"
            "🎉 Your TV is now connected to the Netflix account.\n"
            "Go back to your TV and enjoy Netflix!"
        ),
        "netflix.tv_login.failed": (
            "❌ <b>LOGIN FAILED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Could not sign in with TV code: <code>{tv_code}</code>\n"
            "Reason: {reason}\n\n"
            "💡 Please try again or get a new TV code from your screen."
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
            "💰 <b>REFERRAL LINK</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tap the link below to auto-copy:\n"
            "<code>{invite_link}</code>\n\n"
            "🎁 <i>For each friend who joins via this link, you will receive 1 point!</i>"
        ),
        "checkin.success": "✅ Check-in successful! +1 point\n💰 Current balance: {balance} points.",
        "checkin.already": "❌ You have already checked in today.",
        "balance.current": "💰 Your current balance: {balance} points.",
        "topup.prompt": "Please enter your Key:",
        "key.not_found": "Key not found.",
        "key.used_up": "This key has no remaining uses.",
        "key.expired": "This key has expired.",
        "key.already_used": "You have already used this key.",
        "common.unknown_error": "Unknown error.",
        "key.success": "Key used successfully! +{amount} points.\n💰 Current balance: {balance} points.",
        "key.one_use_per_user_hint": "Note: Each user can only use this key once.",
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
        "discord.balance.insufficient": (
            "Insufficient balance! Need 💰 <b>{cost} points</b> to use Discord Quest Auto.\n\n"
            "Current balance: 💰 <b>{current_balance} points</b>\n\n"
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
        "netflix.no_cookies_available": "❌ No Netflix cookies are currently available in the system. Please check back later!",
        "netflix.random_login.processing": "⏳ Picking a random cookie and generating your Netflix login link...",
        "netflix.maintenance.check_cookie": "❌ <b>Notice:</b> The Netflix Cookie Check service is currently under maintenance. Please try again later!",
        "netflix.maintenance.get_cookie": "❌ <b>Notice:</b> The Get Netflix Cookie service is currently under maintenance. Please try again later!",
        "netflix.maintenance.login_tv": "❌ <b>Notice:</b> The Netflix TV Login service is currently under maintenance. Please try again later!",
        "netflix.balance.insufficient": "❌ Insufficient balance! Each request costs <b>{verify_cost} points</b>. Current balance: {current_balance} points.",
        "admin.no_permission": "You are not allowed to use this command.",
        "admin.user.block_notified": "❌ <b>Notice:</b> Your account has been blocked by the admin. Contact @hcongdev for more details.",
        "admin.user.unblock_notified": "✅ <b>Notice:</b> Your account has been unblocked by the admin. You can use the system again.",
        "cc.prompt.text": "Please enter the CC list in the reply message below (or upload a .txt file).\nFormat: <code>Card Number|Month|Year|CVV</code>\nNote: Each check costs 💰 {verify_cost} points (up to {max_cc} CCs).",
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
    # Chuẩn hóa mã ngôn ngữ.
    if not language:
        return default

    normalized = language.lower().strip()
    if normalized in SUPPORTED_LANGUAGE_SET:
        return normalized
    return default


def has_selected_language(language: Optional[str]) -> bool:
    # Kiểm tra user đã chọn ngôn ngữ hợp lệ hay chưa.
    if not language:
        return False
    return language.lower().strip() in SUPPORTED_LANGUAGE_SET


def tr(language: Optional[str], key: str, **kwargs) -> str:
    # Lấy chuỗi theo ngôn ngữ, fallback về vi nếu không tìm thấy.
    normalized = normalize_language(language, default=DEFAULT_LANGUAGE)
    text = TRANSLATIONS.get(normalized, {}).get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs)


def get_user_language(db, user_id: int, default: Optional[str] = DEFAULT_LANGUAGE) -> Optional[str]:
    # Lấy ngôn ngữ user từ database.
    language = None
    if hasattr(db, "get_user_language"):
        language = db.get_user_language(user_id)
    elif hasattr(db, "get_user"):
        user = db.get_user(user_id)
        language = user.get("language") if user else None
    return normalize_language(language, default=default)
