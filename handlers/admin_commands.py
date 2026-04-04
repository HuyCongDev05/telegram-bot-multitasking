import asyncio
import io
import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command
from utils.messages import BACK_ADMIN_BUTTON_LABEL, BACK_BUTTON_LABEL
from utils.proxy_helper import get_proxy_geoip

logger = logging.getLogger(__name__)

# Internal build sign ID
_BUILD_SIG = "687579636f6e676465763035"


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /addbalance - Admin cộng điểm."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or len(context.args) < 2:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Cách sử dụng: /addbalance <User ID> <Số lượng điểm>\n\nVí dụ: /addbalance 123456789 10"
            )
        return

    try:
        if context.args[0] is None or context.args[1] is None:
            raise ValueError("Tham số không được để trống")

        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text("Người dùng không tồn tại.")
            return

        if db.add_balance(target_user_id, amount):
            user = db.get_user(target_user_id)
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"✅ Thành công cộng {amount} điểm cho người dùng {target_user_id}.\n"
                    f"💰 Số điểm hiện tại: {user['balance']}"
                )
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text(
                "Định dạng tham số sai hoặc thiếu thông tin, vui lòng nhập số hợp lệ."
            )
    except Exception as e:
        logger.exception("Add balance thất bại: %s", e)
        if update.effective_message:
            await update.effective_message.reply_text("Có lỗi xảy ra khi cộng điểm. Vui lòng thử lại sau.")
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context)


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /block - Admin chặn người dùng."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or context.args[0] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Cách sử dụng: /block <User ID>\n\nVí dụ: /block 123456789"
            )
        return

    try:
        target_user_id = int(context.args[0])
        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text("Người dùng không tồn tại.")
            return

        if db.block_user(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(f"✅ Đã chặn người dùng {target_user_id}.")

            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        "❌ <b>Thông báo:</b> Tài khoản của bạn đã bị quản trị viên khóa. "
                        "Liên hệ @hcongdev để biết thêm chi tiết."
                    ),
                    parse_mode='HTML',
                )
            except Exception as e:
                logger.warning("Không thể gửi thông báo chặn cho người dùng %s: %s", target_user_id, e)
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập User ID hợp lệ.")
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context)


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /white - Admin hủy chặn người dùng."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or context.args[0] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Cách sử dụng: /white <User ID>\n\nVí dụ: /white 123456789"
            )
        return

    try:
        target_user_id = int(context.args[0])
        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text("Người dùng không tồn tại.")
            return

        if db.unblock_user(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"✅ Đã đưa người dùng {target_user_id} ra khỏi danh sách đen."
                )

            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        "✅ <b>Thông báo:</b> Tài khoản của bạn đã được quản trị viên bỏ chặn. "
                        "Bạn đã có thể sử dụng lại hệ thống."
                    ),
                    parse_mode='HTML',
                )
            except Exception as e:
                logger.warning("Không thể gửi thông báo bỏ chặn cho người dùng %s: %s", target_user_id, e)
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập User ID hợp lệ.")
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context)


async def blacklist_command(update: Update, db: Database):
    """Xử lý lệnh /blacklist - Xem danh sách đen."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    blacklist = db.get_blacklist()
    if not blacklist:
        if update.effective_message:
            await update.effective_message.reply_text("Danh sách đen hiện đang trống.")
        return

    msg = "📋 Danh sách người dùng bị chặn:\n\n"
    for user in blacklist:
        username = f"@{user['username']}" if user.get('username') else "Không có"
        msg += f"User ID: <code>{user['user_id']}</code>\n"
        msg += f"Username: {username}\n"
        msg += f"Tên: {user['full_name']}\n"
        msg += "---\n"

    if update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML')


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /genkey - Admin tạo mã thẻ."""
    if await reject_group_command(update):
        return False

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return False

    if not context.args or len(context.args) < 2 or context.args[0] is None or context.args[1] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Thiếu tham số. Vui lòng sử dụng qua Menu Admin để được hướng dẫn."
            )
        return False

    try:
        key_code = str(context.args[0]).strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 and context.args[2] is not None else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 and context.args[3] is not None else None

        if balance <= 0:
            if update.effective_message:
                await update.effective_message.reply_text("Số điểm phải lớn hơn 0.")
            return False

        if max_uses <= 0:
            if update.effective_message:
                await update.effective_message.reply_text("Số lần sử dụng phải lớn hơn 0.")
            return False

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ Tạo mã thẻ thành công!\n\n"
                f"Mã thẻ: <code>{key_code}</code>\n"
                f"💰 Số điểm: {balance}\n"
                f"Số lần dùng: {max_uses} lần\n"
            )
            if expire_days:
                msg += f"Thời hạn: {expire_days} ngày\n"
            else:
                msg += "Thời hạn: Vĩnh viễn\n"

            if update.effective_message:
                await update.effective_message.reply_text(msg, parse_mode='HTML')
            return True

        if update.effective_message:
            await update.effective_message.reply_text(
                "Mã thẻ đã tồn tại hoặc tạo thất bại, vui lòng đổi tên mã thẻ."
            )
        return False
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập số hợp lệ.")
        return False


async def listkeys_command(update: Update, db: Database):
    """Xử lý lệnh /listkeys - Admin xem danh sách mã thẻ."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    keys = db.get_all_card_keys()
    if not keys:
        if update.effective_message:
            await update.effective_message.reply_text("Hiện chưa có mã thẻ nào.")
        return

    msg = "📋 Danh sách mã thẻ:\n\n"
    for key in keys[:20]:
        msg += f"Mã thẻ: <code>{key['key_code']}</code>\n"
        msg += f"💰 Số điểm: {key['balance']}\n"
        msg += f"Số lần dùng: {key['current_uses']}/{key['max_uses']}\n"

        expire_at = key.get("expire_at")
        if expire_at:
            expire_time = datetime.fromisoformat(expire_at) if isinstance(expire_at, str) else expire_at
            if datetime.now() > expire_time:
                msg += "Trạng thái: Đã hết hạn\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Trạng thái: Còn hiệu lực (Còn {days_left} ngày)\n"
        else:
            msg += "Trạng thái: Vĩnh viễn\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n(Chỉ hiển thị 20 mã đầu tiên, tổng cộng có {len(keys)} mã)"

    if update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML')


async def list_live_cc_command(update: Update, db: Database):
    """Xử lý lệnh xem danh sách CC live."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    live_ccs = db.get_live_ccs(limit=1000)
    if not live_ccs:
        if update.effective_message:
            await update.effective_message.reply_text("Hiện chưa có thẻ Live nào.")
        return

    output_content = ""
    for cc in live_ccs:
        bin_num = cc.get('bin', 'N/A')
        month = cc.get('month', 'xx')
        year = cc.get('year', 'xxxx')
        cvv = cc.get('cvv', 'xxx')
        status = cc.get('status', 'Unknown')
        check_at = cc.get('checkAt', '')

        if isinstance(check_at, datetime):
            check_at = check_at.strftime('%Y-%m-%d %H:%M:%S')

        output_content += f"{bin_num}|{month}|{year}|{cvv} - [{status.upper()}] - {check_at}\n"

    if len(live_ccs) <= 20:
        if update.effective_message:
            await update.effective_message.reply_text(
                f"Danh sách CC Live:\n<code>{output_content}</code>",
                parse_mode='HTML',
            )
        return

    file_stream = io.BytesIO(output_content.encode('utf-8'))
    file_stream.name = "live_cc.txt"
    if update.effective_message:
        await update.effective_message.reply_document(
            document=file_stream,
            caption=f"Danh sách {len(live_ccs)} CC Live mới nhất.",
        )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /broadcast - Admin gửi thông báo hàng loạt."""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and update.message and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""

    if not text:
        if update.effective_message:
            await update.effective_message.reply_text(
                "Cách sử dụng: /broadcast <Nội dung>, hoặc trả lời một tin nhắn rồi gửi /broadcast"
            )
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = None
    if update.effective_message:
        status_msg = await update.effective_message.reply_text(
            f"📢 Bắt đầu phát sóng, tổng cộng {len(user_ids)} người dùng..."
        )

    final_broadcast_text = f"<b>🔊 Thông báo:</b>\n\n{text}"

    for uid in user_ids:
        if uid == ADMIN_USER_ID:
            continue

        try:
            await context.bot.send_message(chat_id=uid, text=final_broadcast_text, parse_mode='HTML')
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning("Gửi tin nhắn đến %s thất bại: %s", uid, e)
            failed += 1

    if status_msg:
        await status_msg.edit_text(
            f"✅ Phát sóng hoàn tất!\nThành công: {success}\nThất bại: {failed}"
        )

    from handlers.user_commands import show_admin_dashboard_after_delay

    await show_admin_dashboard_after_delay(update, context)


async def handle_admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE, user_info: dict):
    """Hiển thị thông tin người dùng cho Admin và cung cấp các nút thao tác nhanh."""
    uid = user_info['user_id']
    username = user_info.get('username', 'N/A')
    full_name = user_info.get('full_name', 'N/A')
    balance = user_info.get('balance', 0)
    is_blocked = user_info.get('is_blocked', 0)
    created_at = user_info.get('created_at', 'N/A')

    status_text = "🚫 Đang bị chặn" if is_blocked else "✅ Bình thường"
    text = (
        "👤 <b>THÔNG TIN NGƯỜI DÙNG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Username: @{username}\n"
        f"📝 Tên: {full_name}\n"
        f"💰 Số dư: <b>{balance} điểm</b>\n"
        f"🚦 Trạng thái: {status_text}\n"
        f"📅 Ngày tham gia: {created_at}\n"
    )

    keyboard = [[
        InlineKeyboardButton("+10 💰", callback_data=f"admin_q_add:{uid}:10"),
        InlineKeyboardButton("+50 💰", callback_data=f"admin_q_add:{uid}:50"),
        InlineKeyboardButton("+100 💰", callback_data=f"admin_q_add:{uid}:100"),
    ]]

    if is_blocked:
        keyboard.append([InlineKeyboardButton("🔓 Mở khóa", callback_data=f"admin_q_unblock:{uid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 Khóa", callback_data=f"admin_q_block:{uid}")])

    keyboard.append([InlineKeyboardButton(BACK_ADMIN_BUTTON_LABEL, callback_data='cancel_to_admin_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')


async def list_proxies_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Hiển thị danh sách Proxy cho Admin trong giao diện nút bấm."""
    query = update.callback_query
    if query:
        await query.answer()

    proxies = db.get_all_proxies()
    if not proxies:
        msg = "❌ Hiện tại không có proxy nào trong hệ thống."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    msg = "📋 <b>DANH SÁCH PROXY HIỆN CÓ</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"

    for proxy in proxies[:15]:
        loc = f"[{proxy['country'] or 'N/A'}] {proxy['city'] or ''}"
        msg += f"• <code>{proxy['address']}:{proxy['port']}</code> - {loc}\n"
        msg += f"  <i>Cập nhật: {proxy['updatedAt']}</i>\n"
        msg += "---\n"

    if len(proxies) > 15:
        msg += f"\n<i>(Hiển thị 15/{len(proxies)} proxy mới nhất)</i>"

    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(BACK_BUTTON_LABEL, callback_data='admin_proxy_mgmt')]]
    )

    if query:
        await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')


async def handle_proxy_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, file_content: str):
    """Xử lý file .txt proxy được gửi lên bởi Admin."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        return

    processing_msg = await update.message.reply_text("⏳ Đang xử lý danh sách proxy, vui lòng đợi...")

    lines = file_content.splitlines()
    total = 0
    added = 0
    duplicates = 0
    errors = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        total += 1
        parts = line.split(':')
        address = parts[0]
        port = parts[1] if len(parts) > 1 else ""
        username = parts[2] if len(parts) > 2 else None
        password = parts[3] if len(parts) > 3 else None

        if not address or not port:
            errors += 1
            continue

        if db.proxy_exists(address, port, username, password):
            duplicates += 1
            continue

        geo_info = get_proxy_geoip(address, port, username, password)
        if geo_info["success"]:
            if db.add_proxy(address, port, username, password, geo_info["city"], geo_info["country"]):
                added += 1
            else:
                errors += 1
        else:
            errors += 1

    res_msg = (
        "✅ <b>HOÀN TẤT NẠP PROXY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Tổng số: <code>{total}</code>\n"
        f"➕ Nạp mới: <code>{added}</code>\n"
        f"👯 Trùng lặp: <code>{duplicates}</code>\n"
        f"❌ Lỗi/Die: <code>{errors}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Hệ thống đã tự động lọc trùng và xác định quốc gia cho proxy."
    )
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(BACK_ADMIN_BUTTON_LABEL, callback_data='admin_menu')]]
    )

    await processing_msg.edit_text(res_msg, parse_mode='HTML', reply_markup=reply_markup)
