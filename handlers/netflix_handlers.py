import logging

from telegram import Update
from telegram.ext import ContextTypes

from checkCookieNetflix.netflix_checker import NetflixChecker, NetscapeConverter
from config import ADMIN_USER_ID, VERIFY_COST
from database_mysql import Database
from utils.messages import get_ui_label
from utils.proxy_helper import format_proxy_url

COUNTRY_MAP = {
    "VN": "Việt Nam",
    "US": "Hoa Kỳ",
    "BR": "Brazil",
    "SG": "Singapore",
    "TH": "Thái Lan",
    "PH": "Philippines",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "JP": "Nhật Bản",
    "KR": "Hàn Quốc",
    "CA": "Canada",
    "GB": "Vương Quốc Anh",
    "AU": "Australia",
    "DE": "Đức",
    "FR": "Pháp",
    "ES": "Tây Ban Nha",
    "IT": "Ý",
    "IN": "Ấn Độ",
    "TR": "Thổ Nhĩ Kỳ",
    "MX": "Mexico",
    "AR": "Argentina",
}

logger = logging.getLogger(__name__)


def get_country_name(code):
    if not code:
        return "Không rõ"

    return COUNTRY_MAP.get(code.upper(), code)


async def check_cookie_netflix_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Bắt đầu luồng nhập cookie Netflix."""
    user_id = update.effective_user.id

    if db.is_service_maintenance('check_cookie_netflix') and user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ <b>Thông báo:</b> Dịch vụ Check Cookie Netflix hiện đang bảo trì. Vui lòng quay lại sau!",
                parse_mode='HTML',
            )
        return

    user = db.get_user(user_id)
    if user['balance'] < VERIFY_COST:
        if update.effective_message:
            await update.effective_message.reply_text(
                f"❌ Số dư không đủ! Mỗi lượt check tốn <b>{VERIFY_COST} điểm</b>. Hiện có: {user['balance']} điểm.",
                parse_mode='HTML',
            )
        return

    from handlers.user_commands import start_input_flow
    service_label = get_ui_label('check_cookie_netflix')

    prompt_text = (
        f"<b>{service_label}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Vui lòng <b>gửi file .txt/.json</b> hoặc <b>dán nội dung cookie</b> để bắt đầu kiểm tra.\n"
        f"💰 Chi phí: {VERIFY_COST} điểm cho mỗi lượt thành công."
    )
    await start_input_flow(update, context, prompt_text, 'check_cookie_netflix_step_1', 'cancel_to_main')


async def process_netflix_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cookie_content: str):
    """Logic xử lý và kiểm tra cookie Netflix."""
    from handlers.user_commands import show_main_menu_after_delay

    user_id = update.effective_user.id
    processing_msg = await update.message.reply_text("⏳ Đang kiểm tra cookie, vui lòng đợi...")

    try:
        cookies = NetscapeConverter.convert_to_json(cookie_content)
        if not cookies:
            await processing_msg.edit_text("❌ Không tìm thấy cookie hợp lệ. Vui lòng kiểm tra lại định dạng!")
            await show_main_menu_after_delay(update, context, db)
            return

        proxy = db.get_random_proxy()
        proxy_url = format_proxy_url(proxy) if proxy else None

        checker = NetflixChecker(proxy_url=proxy_url)
        success, result = checker.check(cookies)

        if success:
            if db.deduct_balance(user_id, VERIFY_COST):
                res_msg = (
                    "✅ <b>KẾT QUẢ CHECK COOKIE: LIVE</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📧 Email: <code>{result['email']}</code>\n"
                    f"📦 Gói cước: {result['plan']}\n"
                    f"🌍 Quốc gia: {get_country_name(result['country'])}\n"
                    f"👥 Thành viên bổ sung: {'Có' if result['extra_member'] else 'Không'}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Đã trừ: {VERIFY_COST} điểm\n"
                    f"💰 Số dư còn lại: {db.get_user(user_id)['balance']} điểm"
                )
                await processing_msg.edit_text(res_msg, parse_mode='HTML')
            else:
                await processing_msg.edit_text("❌ Lỗi hệ thống khi trừ điểm. Vui lòng thử lại!")
        else:
            error_text = result.get('error', 'Không xác định')
            await processing_msg.edit_text(
                f"❌ <b>Cookie Die hoặc Không hợp lệ!</b>\nLý do: <code>{error_text}</code>",
                parse_mode='HTML',
            )

        await show_main_menu_after_delay(update, context, db)
    except Exception as e:
        logger.error("Lỗi khi xử lý Netflix Cookie cho user %s: %s", user_id, e)
        await processing_msg.edit_text("❌ Có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau!")
        await show_main_menu_after_delay(update, context, db)
