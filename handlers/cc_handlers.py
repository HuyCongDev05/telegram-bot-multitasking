"""Trình xử lý lệnh Check CC"""
import io
import logging
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from checkCC.api_client import check_card_quick
from checkCC.bin_lookup import format_bin_info, get_clean_country_info
from config import VERIFY_COST
from database import Database
from handlers.user_commands import is_user_busy, show_main_menu_after_delay
from utils.i18n import DEFAULT_LANGUAGE, get_user_language
from utils.messages import get_ui_label

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"

# Giới hạn tối đa 50 CC cho mỗi lần check
MAX_CC_PER_REQUEST = 50

async def checkCC_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /check_cc"""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'check_cc'):
        return
    
    # Nếu có đối số (text sau lệnh /checkCC)
    if context.args:
        cc_input = " ".join(context.args)
        await _process_cc_request(update, context, db, cc_input)
        return

    # Nếu không có đối số, hiển thị thông báo hướng dẫn (có ForceReply)

    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    service_label = get_ui_label('check_cc', language)
    prompt_text = (
        f"<b>{service_label}</b>\n\n"
        + (
            "Please enter the CC list in the reply message below (or upload a .txt file).\n"
            "Format: <code>Card Number|Month|Year|CVV</code>\n"
            f"Note: Each check costs 💰 {VERIFY_COST} points (up to {MAX_CC_PER_REQUEST} CCs)."
            if language == 'en'
            else "Vui lòng nhập danh sách CC vào tin nhắn trả lời bên dưới (hoặc gửi file .txt).\n"
            "Định dạng: <code>Số thẻ|Tháng|Năm|CVV</code>\n"
            f"Lưu ý: Phí mỗi lần check là 💰 {VERIFY_COST} điểm (tối đa {MAX_CC_PER_REQUEST} CC)."
        )
    )

    from handlers.user_commands import start_input_flow
    await start_input_flow(update, context, prompt_text, 'check_cc_step_1', 'cancel_to_main')

async def _process_cc_request(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, cc_text: str):
    """Hàm xử lý chính cho yêu cầu check CC"""
    # Kiểm tra bảo trì
    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'check_cc'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    
    # Hàm để reply message (tùy thuộc vào source)
    async def reply(text, **kwargs):
        if update.message:
            return await update.message.reply_text(text, **kwargs)
        else:
            return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)
            
    async def reply_doc(document, **kwargs):
        if update.message:
            return await update.message.reply_document(document=document, **kwargs)
        else:
            return await context.bot.send_document(chat_id=update.effective_chat.id, document=document, **kwargs)
    
    # Kiểm tra số dư
    user_data = db.get_user(user_id)
    if not user_data or user_data['balance'] < VERIFY_COST:
        from utils.messages import get_insufficient_balance_message
        await reply(get_insufficient_balance_message(user_data['balance'] if user_data else 0, language))
        await show_main_menu_after_delay(
            update,
            context,
            db,
            "Insufficient balance for this feature." if language == 'en' else "Số dư không đủ để thực hiện chức năng này.",
        )
        return

    # Lấy các dòng đầu tiên (giới hạn 50)
    lines = [line.strip() for line in cc_text.split('\n') if line.strip()]
    if len(lines) > MAX_CC_PER_REQUEST:
        await reply(
            f"⚠️ The system only supports up to {MAX_CC_PER_REQUEST} lines per request. Only the first {MAX_CC_PER_REQUEST} lines will be checked."
            if language == 'en'
            else f"⚠️ Hệ thống chỉ hỗ trợ tối đa {MAX_CC_PER_REQUEST} dòng trong 1 lần gửi. Tôi sẽ chỉ check {MAX_CC_PER_REQUEST} dòng đầu tiên."
        )
        lines = lines[:MAX_CC_PER_REQUEST]

    if not lines:
        await reply("❌ The file/message has no content. Please check it again." if language == 'en' else "❌ File/Tin nhắn không có nội dung. Vui lòng kiểm tra lại.")
        return

    total_cards = len(lines)
    total_cost = total_cards * VERIFY_COST

    # Trừ điểm
    if not db.deduct_balance(user_id, total_cost):
        await reply(
            f"❌ <b>Transaction failed!</b>\nYour balance is not enough to check {total_cards} cards (need {total_cost} points)."
            if language == 'en'
            else f"❌ <b>Giao dịch thất bại!</b>\nSố dư của bạn không đủ để check {total_cards} thẻ (Cần {total_cost} điểm)."
        )
        return

    status_msg = await reply(
        f"⏳ Checking {len(lines)} lines... Please do not spam the bot."
        if language == 'en'
        else f"⏳ Đang kiểm tra {len(lines)} dòng... Vui lòng không spam bot."
    )

    cc_pattern = re.compile(r'(\d{15,16})[|/ ](\d{1,2})[|/ ](\d{2,4})[|/ ](\d{3,4})')

    results = []
    lives = []
    real_cards = [] # Thẻ thật mở nhưng không thanh toán được (declined)
    invalid_format = []
    
    matches_count = 0

    # Duyệt qua từng dòng và kiểm tra
    for i, line in enumerate(lines):
        match = cc_pattern.search(line)
        
        # Cập nhật trạng thái định kỳ
        if (i + 1) % 5 == 0:
            await status_msg.edit_text(
                f"⏳ Processing: {i+1}/{len(lines)} lines..."
                if language == 'en'
                else f"⏳ Đang xử lý: {i+1}/{len(lines)} dòng..."
            )
            
        if not match:
            invalid_format.append(f"{line} - [ERROR] Invalid format" if language == 'en' else f"{line} - [ERROR] Sai định dạng")
            results.append(f"{line} - [ERROR] Invalid format" if language == 'en' else f"{line} - [ERROR] Sai định dạng")
            continue

        matches_count += 1
        card_num, month, year, cvv = match.groups()
        
        # Chuẩn hóa format để client nhận vào
        # API Client mong muốn: card_num|month|year|cvv
        # Nếu năm là 2 số, API client sẽ tự thêm 20
        card_str = f"{card_num}|{month.zfill(2)}|{year}|{cvv}"
        
        try:
            check_res = await check_card_quick(card_str)
            status = check_res.get("status")
            message = check_res.get("message", "Unknown error")
            bin_info = check_res.get("bin_info", {}) or {}
            bin_formatted = format_bin_info(bin_info) or "Un-Known BIN"
            
            card_display = f"{card_num}|{month.zfill(2)}|{year}|{cvv}"
            output_line = f"{card_display} - [{status.upper()}] {message} - {bin_formatted}"
            
            results.append(output_line)
            
                # Lưu live hoặc real vào DB (bảng live_cc)
            if status in ["charged", "approved"]:
                lives.append(output_line)
                # Lưu toàn bộ thẻ gốc vào trường bin kèm thông tin chi tiết
                db.add_live_cc(
                    card_num, month.zfill(2), year, cvv, "live",
                    bank=bin_info.get("bank"),
                    country=get_clean_country_info(bin_info),
                    brand=bin_info.get("brand"),
                    card_type=bin_info.get("type"),
                    level=bin_info.get("level")
                )
                
            elif status == "declined" and check_res.get("stripe_card_info"):
                # Có stripe_card_info nghĩa là thẻ thật nhưng bị từ chối bởi cổng/ngân hàng
                real_cards.append(output_line)
                # Lưu toàn bộ thẻ gốc vào trường bin kèm thông tin chi tiết
                db.add_live_cc(
                    card_num, month.zfill(2), year, cvv, "real",
                    bank=bin_info.get("bank"),
                    country=get_clean_country_info(bin_info),
                    brand=bin_info.get("brand"),
                    card_type=bin_info.get("type"),
                    level=bin_info.get("level")
                )
                
        except Exception as e:
            logger.error(f"Error checking CC {card_num}: {e}")
            results.append(
                f"{card_num}|{month}|{year}|{cvv} - [ERROR] System error"
                if language == 'en'
                else f"{card_num}|{month}|{year}|{cvv} - [ERROR] Lỗi hệ thống"
            )

    # Tạo nội dung file
    output_content = "=== CC CHECK RESULT ===\n" if language == 'en' else "=== KẾT QUẢ CHECK CC ===\n"
    output_content += f"{'Time' if language == 'en' else 'Thời gian'}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output_content += f"{'Total' if language == 'en' else 'Tổng cộng'}: {len(lines)} {'lines' if language == 'en' else 'dòng'}\n"
    output_content += f"{'Live' if language == 'en' else 'Thành công (Live)'}: {len(lives)}\n"
    output_content += f"{'Real but declined' if language == 'en' else 'Thẻ thật nhưng declined'}: {len(real_cards)}\n"
    output_content += f"{'Invalid format' if language == 'en' else 'Sai định dạng'}: {len(invalid_format)}\n\n"

    if lives:
        output_content += "--- LIVE LIST ---\n" if language == 'en' else "--- DANH SÁCH LIVE ---\n"
        output_content += "\n".join(lives) + "\n\n"

    if real_cards:
        output_content += "--- REAL CARDS (DECLINED) ---\n" if language == 'en' else "--- THẺ THỰC (DECLINED) ---\n"
        output_content += "\n".join(real_cards) + "\n\n"

    if invalid_format:
        output_content += "--- INVALID FORMAT ---\n" if language == 'en' else "--- SAI ĐỊNH DẠNG ---\n"
        output_content += "\n".join(invalid_format) + "\n\n"

    output_content += "--- FULL RESULT ---\n" if language == 'en' else "--- TOÀN BỘ KẾT QUẢ ---\n"
    output_content += "\n".join(results)

    # Gửi file cc.txt
    file_stream = io.BytesIO(output_content.encode('utf-8'))
    file_stream.name = "cc.txt"
    
    await status_msg.delete()

    text_summary = (
        f"✅ <b>Completed!</b>\n"
        f"📊 Total checked: {len(lines)}\n"
        f"💰 Live: {len(lives)}\n"
        f"💳 Real (Declined): {len(real_cards)}\n"
        f"❌ Invalid format: {len(invalid_format)}\n"
        f"💰 Remaining balance: {db.get_user(user_id)['balance']} points."
        if language == 'en'
        else f"✅ <b>Xử lý hoàn tất!</b>\n"
        f"📊 Tổng check: {len(lines)}\n"
        f"💰 Live: {len(lives)}\n"
        f"💳 Real (Declined): {len(real_cards)}\n"
        f"❌ Sai định dạng: {len(invalid_format)}\n"
        f"💰 Số dư còn lại: {db.get_user(user_id)['balance']} điểm."
    )
    
    # Hiển thị lại Menu kèm nút "Quay lại" bên dưới tài liệu
    await reply_doc(
        document=file_stream, 
        caption=text_summary,
        parse_mode='HTML',
    )

    await show_main_menu_after_delay(update, context, db)
    # Tự động gửi lại menu chính sau khi gửi file (Chờ 2s để người dùng thấy file)

async def handle_cc_file_input(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, content: str):
    """Bọc logic file input cho CC"""
    await _process_cc_request(update, context, db, content)
