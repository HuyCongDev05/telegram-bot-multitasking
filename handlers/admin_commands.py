import asyncio
import io
import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database import Database
from utils.checks import reject_group_command
from utils.i18n import DEFAULT_LANGUAGE, get_user_language
from utils.messages import get_back_admin_button_label, get_back_button_label
from utils.proxy_helper import get_proxy_geoip

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"


def pick_text(language: str, vi_text: str, en_text: str) -> str:
    return en_text if language == 'en' else vi_text


def build_broadcast_wrapper(language: str, text: str) -> str:
    prefix = "🔊 Notice:" if language == 'en' else "🔊 Thông báo:"
    return f"<b>{prefix}</b>\n\n{text}"


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /addbalance - Admin cộng điểm."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    if not context.args or len(context.args) < 2:
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Cách sử dụng: /addbalance <User ID> <Số lượng điểm>\n\nVí dụ: /addbalance 123456789 10", "Usage: /addbalance <User ID> <Amount>\n\nExample: /addbalance 123456789 10")
            )
        return

    try:
        if context.args[0] is None or context.args[1] is None:
            raise ValueError("Tham số không được để trống")

        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Người dùng không tồn tại.", "User does not exist."))
            return

        if db.add_balance(target_user_id, amount):
            user = db.get_user(target_user_id)
            if update.effective_message:
                await update.effective_message.reply_text(
                    pick_text(
                        language,
                        f"✅ Thành công cộng {amount} điểm cho người dùng {target_user_id}.\n💰 Số điểm hiện tại: {user['balance']}",
                        f"✅ Successfully added {amount} points to user {target_user_id}.\n💰 Current balance: {user['balance']}",
                    )
                )
        else:
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Thao tác thất bại, vui lòng thử lại sau.", "The operation failed. Please try again later."))
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Định dạng tham số sai hoặc thiếu thông tin, vui lòng nhập số hợp lệ.", "Invalid or missing parameters. Please enter valid numbers.")
            )
    except Exception as e:
        logger.exception("Add balance thất bại: %s", e)
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Có lỗi xảy ra khi cộng điểm. Vui lòng thử lại sau.", "An error occurred while adding balance. Please try again later."))
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context, db=db)


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /block - Admin chặn người dùng."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    if not context.args or context.args[0] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Cách sử dụng: /block <User ID>\n\nVí dụ: /block 123456789", "Usage: /block <User ID>\n\nExample: /block 123456789")
            )
        return

    try:
        target_user_id = int(context.args[0])
        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Người dùng không tồn tại.", "User does not exist."))
            return

        if db.block_user(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, f"✅ Đã chặn người dùng {target_user_id}.", f"✅ User {target_user_id} has been blocked."))

            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=pick_text(
                        get_user_language(db, target_user_id, default=DEFAULT_LANGUAGE),
                        "❌ <b>Thông báo:</b> Tài khoản của bạn đã bị quản trị viên khóa. Liên hệ @hcongdev để biết thêm chi tiết.",
                        "❌ <b>Notice:</b> Your account has been blocked by the admin. Contact @hcongdev for more details.",
                    ),
                    parse_mode='HTML',
                )
            except Exception as e:
                logger.warning("Không thể gửi thông báo chặn cho người dùng %s: %s", target_user_id, e)
        else:
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Thao tác thất bại, vui lòng thử lại sau.", "The operation failed. Please try again later."))
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Định dạng tham số sai, vui lòng nhập User ID hợp lệ.", "Invalid parameter format. Please enter a valid user ID."))
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context, db=db)


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /white - Admin hủy chặn người dùng."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    if not context.args or context.args[0] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Cách sử dụng: /white <User ID>\n\nVí dụ: /white 123456789", "Usage: /white <User ID>\n\nExample: /white 123456789")
            )
        return

    try:
        target_user_id = int(context.args[0])
        if not db.user_exists(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Người dùng không tồn tại.", "User does not exist."))
            return

        if db.unblock_user(target_user_id):
            if update.effective_message:
                await update.effective_message.reply_text(
                    pick_text(language, f"✅ Đã đưa người dùng {target_user_id} ra khỏi danh sách đen.", f"✅ User {target_user_id} has been removed from the blacklist.")
                )

            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=pick_text(
                        get_user_language(db, target_user_id, default=DEFAULT_LANGUAGE),
                        "✅ <b>Thông báo:</b> Tài khoản của bạn đã được quản trị viên bỏ chặn. Bạn đã có thể sử dụng lại hệ thống.",
                        "✅ <b>Notice:</b> Your account has been unblocked by the admin. You can use the system again.",
                    ),
                    parse_mode='HTML',
                )
            except Exception as e:
                logger.warning("Không thể gửi thông báo bỏ chặn cho người dùng %s: %s", target_user_id, e)
        else:
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Thao tác thất bại, vui lòng thử lại sau.", "The operation failed. Please try again later."))
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Định dạng tham số sai, vui lòng nhập User ID hợp lệ.", "Invalid parameter format. Please enter a valid user ID."))
    finally:
        from handlers.user_commands import show_admin_dashboard_after_delay

        await show_admin_dashboard_after_delay(update, context, db=db)


async def blacklist_command(update: Update, db: Database):
    """Xử lý lệnh /blacklist - Xem danh sách đen."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    blacklist = db.get_blacklist()
    if not blacklist:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Danh sách đen hiện đang trống.", "The blacklist is currently empty."))
        return

    msg = "📋 Blocked users:\n\n" if language == 'en' else "📋 Danh sách người dùng bị chặn:\n\n"
    for user in blacklist:
        username = f"@{user['username']}" if user.get('username') else ("None" if language == 'en' else "Không có")
        msg += f"User ID: <code>{user['user_id']}</code>\n"
        msg += f"Username: {username}\n"
        msg += f"{'Name' if language == 'en' else 'Tên'}: {user['full_name']}\n"
        msg += "---\n"

    if update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML')


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /genkey - Admin tạo mã thẻ."""
    if await reject_group_command(update, db):
        return False

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return False

    if not context.args or len(context.args) < 2 or context.args[0] is None or context.args[1] is None:
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Thiếu tham số. Vui lòng sử dụng qua Menu Admin để được hướng dẫn.", "Missing parameters. Please use the Admin Menu flow for guidance.")
            )
        return False

    try:
        key_code = str(context.args[0]).strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 and context.args[2] is not None else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 and context.args[3] is not None else None

        if balance <= 0:
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Số điểm phải lớn hơn 0.", "Points must be greater than 0."))
            return False

        if max_uses <= 0:
            if update.effective_message:
                await update.effective_message.reply_text(pick_text(language, "Số lần sử dụng phải lớn hơn 0.", "Number of uses must be greater than 0."))
            return False

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ Key created successfully!\n\n"
                f"Mã thẻ: <code>{key_code}</code>\n"
                f"💰 Số điểm: {balance}\n"
                f"Số lần dùng: {max_uses} lần\n"
                f"ℹ️ <i>Lưu ý: Mỗi người dùng chỉ có thể sử dụng mã này 1 lần.</i>\n"
            )
            if language == 'en':
                msg = (
                    "✅ Key created successfully!\n\n"
                    f"Key code: <code>{key_code}</code>\n"
                    f"💰 Points: {balance}\n"
                    f"Total Uses: {max_uses}\n"
                    f"ℹ️ <i>Note: Each user can only use this key once.</i>\n"
                )
            if expire_days:
                msg += f"Expiration: {expire_days} days\n" if language == 'en' else f"Thời hạn: {expire_days} ngày\n"
            else:
                msg += "Expiration: Never\n" if language == 'en' else "Thời hạn: Vĩnh viễn\n"

            if update.effective_message:
                await update.effective_message.reply_text(msg, parse_mode='HTML')
            return True

        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Mã thẻ đã tồn tại hoặc tạo thất bại, vui lòng đổi tên mã thẻ.", "The key already exists or creation failed. Please use a different key name.")
            )
        return False
    except (TypeError, ValueError):
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Định dạng tham số sai, vui lòng nhập số hợp lệ.", "Invalid parameter format. Please enter valid numbers."))
        return False


async def listkeys_command(update: Update, db: Database):
    """Xử lý lệnh /listkeys - Admin xem danh sách mã thẻ."""
    if await reject_group_command(update, db):
        return

    query = update.callback_query
    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    keys = db.get_all_card_keys()
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(get_back_button_label(language), callback_data='admin_key_menu')]]
    )

    if not keys:
        if query:
            await query.edit_message_text(pick_text(language, "Hiện chưa có mã thẻ nào.", "There are no keys yet."), reply_markup=reply_markup)
        elif update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Hiện chưa có mã thẻ nào.", "There are no keys yet."), reply_markup=reply_markup)
        return

    msg = "📋 Key list:\n\n" if language == 'en' else "📋 Danh sách mã thẻ:\n\n"
    for key in keys[:20]:
        msg += f"{'Key code' if language == 'en' else 'Mã thẻ'}: <code>{key['key_code']}</code>\n"
        msg += f"💰 {'Points' if language == 'en' else 'Số điểm'}: {key['balance']}\n"
        msg += f"{'Uses' if language == 'en' else 'Số lần dùng'}: {key['current_uses']}/{key['max_uses']}\n"

        expire_at = key.get("expire_at")
        if expire_at:
            expire_time = datetime.fromisoformat(expire_at) if isinstance(expire_at, str) else expire_at
            if datetime.now() > expire_time:
                msg += "Status: Expired\n" if language == 'en' else "Trạng thái: Đã hết hạn\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Status: Active ({days_left} days left)\n" if language == 'en' else f"Trạng thái: Còn hiệu lực (Còn {days_left} ngày)\n"
        else:
            msg += "Status: Never expires\n" if language == 'en' else "Trạng thái: Vĩnh viễn\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n(Showing only the first 20 keys, total {len(keys)} keys)" if language == 'en' else f"\n(Chỉ hiển thị 20 mã đầu tiên, tổng cộng có {len(keys)} mã)"

    if query:
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=reply_markup)
    elif update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)


async def list_live_cc_command(update: Update, db: Database):
    """Xử lý lệnh xem danh sách CC live."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    live_ccs = db.get_live_ccs(limit=1000)
    if not live_ccs:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Hiện chưa có thẻ Live nào.", "There are no live cards yet."))
        return

    output_content = ""
    for cc in live_ccs:
        bin_num = cc.get('bin', 'N/A')
        month = cc.get('month', 'xx')
        year = cc.get('year', 'xxxx')
        cvv = cc.get('cvv', 'xxx')
        bank = cc.get('bank') or 'N/A'
        country = cc.get('country') or 'N/A'
        brand = cc.get('brand') or 'N/A'
        card_type = cc.get('card_type') or 'N/A'
        level = cc.get('level') or 'N/A'
        status = cc.get('status', 'Unknown')
        check_at = cc.get('checkAt', '')

        if isinstance(check_at, datetime):
            check_at = check_at.strftime('%Y-%m-%d %H:%M:%S')

        output_content += f"{bin_num}|{month}|{year}|{cvv} - [{status.upper()}] - {brand} {card_type} {level} - {bank} ({country}) - {check_at}\n"

    if len(live_ccs) <= 20:
        if update.effective_message:
            await update.effective_message.reply_text(
                f"{'Live CC list' if language == 'en' else 'Danh sách CC Live'}:\n<code>{output_content}</code>",
                parse_mode='HTML',
            )
        return

    file_stream = io.BytesIO(output_content.encode('utf-8'))
    file_stream.name = "live_cc.txt"
    if update.effective_message:
        await update.effective_message.reply_document(
            document=file_stream,
            caption=f"Latest {len(live_ccs)} live CCs." if language == 'en' else f"Danh sách {len(live_ccs)} CC Live mới nhất.",
        )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /broadcast - Admin gửi thông báo hàng loạt."""
    if await reject_group_command(update, db):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and update.message and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""

    if not text:
        if update.effective_message:
            await update.effective_message.reply_text(
                pick_text(language, "Cách sử dụng: /broadcast <Nội dung>, hoặc trả lời một tin nhắn rồi gửi /broadcast", "Usage: /broadcast <message>, or reply to a message and send /broadcast")
            )
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = None
    if update.effective_message:
        status_msg = await update.effective_message.reply_text(
            f"📢 Starting broadcast to {len(user_ids)} users..." if language == 'en' else f"📢 Bắt đầu phát sóng, tổng cộng {len(user_ids)} người dùng..."
        )

    for uid in user_ids:
        if uid == ADMIN_USER_ID:
            continue

        try:
            recipient_language = get_user_language(db, uid, default=DEFAULT_LANGUAGE)
            final_broadcast_text = build_broadcast_wrapper(recipient_language, text)
            await context.bot.send_message(chat_id=uid, text=final_broadcast_text, parse_mode='HTML')
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning("Gửi tin nhắn đến %s thất bại: %s", uid, e)
            failed += 1

    if status_msg:
        await status_msg.edit_text(
            f"✅ Broadcast completed!\nSuccess: {success}\nFailed: {failed}" if language == 'en' else f"✅ Phát sóng hoàn tất!\nThành công: {success}\nThất bại: {failed}"
        )

    from handlers.user_commands import show_admin_dashboard_after_delay

    await show_admin_dashboard_after_delay(update, context, db=db)


async def handle_admin_search_result(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_info: dict,
        db: Database | None = None,
):
    """Hiển thị thông tin người dùng cho Admin và cung cấp các nút thao tác nhanh."""
    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE) if db else DEFAULT_LANGUAGE
    uid = user_info['user_id']
    username = user_info.get('username', 'N/A')
    full_name = user_info.get('full_name', 'N/A')
    balance = user_info.get('balance', 0)
    is_blocked = user_info.get('is_blocked', 0)
    created_at = user_info.get('created_at', 'N/A')
    user_language = (user_info.get('language') or '').lower()

    status_text = "🚫 Blocked" if is_blocked and language == 'en' else "🚫 Đang bị chặn" if is_blocked else "✅ Normal" if language == 'en' else "✅ Bình thường"
    text = (
        f"👤 <b>{'USER INFORMATION' if language == 'en' else 'THÔNG TIN NGƯỜI DÙNG'}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Username: @{username}\n"
        f"📝 {'Name' if language == 'en' else 'Tên'}: {full_name}\n"
        f"🌐 {'Language' if language == 'en' else 'Ngôn ngữ'}: {user_language or ('Not set' if language == 'en' else 'Chưa chọn')}\n"
        f"💰 {'Balance' if language == 'en' else 'Số dư'}: <b>{balance} {'points' if language == 'en' else 'điểm'}</b>\n"
        f"🚦 {'Status' if language == 'en' else 'Trạng thái'}: {status_text}\n"
        f"📅 {'Joined at' if language == 'en' else 'Ngày tham gia'}: {created_at}\n"
    )

    keyboard = [[
        InlineKeyboardButton("+10 💰", callback_data=f"admin_q_add:{uid}:10"),
        InlineKeyboardButton("+50 💰", callback_data=f"admin_q_add:{uid}:50"),
        InlineKeyboardButton("+100 💰", callback_data=f"admin_q_add:{uid}:100"),
    ]]

    if is_blocked:
        keyboard.append([InlineKeyboardButton("🔓 Unblock" if language == 'en' else "🔓 Mở khóa", callback_data=f"admin_q_unblock:{uid}")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 Block" if language == 'en' else "🔒 Khóa", callback_data=f"admin_q_block:{uid}")])

    keyboard.append([InlineKeyboardButton(get_back_button_label(language), callback_data='admin_users_menu')])
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

    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    proxies = db.get_all_proxies()
    if not proxies:
        msg = "❌ There are no proxies in the system right now." if language == 'en' else "❌ Hiện tại không có proxy nào trong hệ thống."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    msg = "📋 <b>AVAILABLE PROXY LIST</b>\n━━━━━━━━━━━━━━━━━━━━\n" if language == 'en' else "📋 <b>DANH SÁCH PROXY HIỆN CÓ</b>\n━━━━━━━━━━━━━━━━━━━━\n"

    for proxy in proxies[:15]:
        loc = f"[{proxy['country'] or 'N/A'}] {proxy['city'] or ''}"
        msg += f"• <code>{proxy['address']}:{proxy['port']}</code> - {loc}\n"
        msg += f"  <i>{'Updated' if language == 'en' else 'Cập nhật'}: {proxy['updatedAt']}</i>\n"
        msg += "---\n"

    if len(proxies) > 15:
        msg += f"\n<i>(Showing 15/{len(proxies)} latest proxies)</i>" if language == 'en' else f"\n<i>(Hiển thị 15/{len(proxies)} proxy mới nhất)</i>"

    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(get_back_button_label(language), callback_data='admin_proxy_mgmt')]]
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
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

    processing_msg = await update.message.reply_text("⏳ Processing the proxy list, please wait..." if language == 'en' else "⏳ Đang xử lý danh sách proxy, vui lòng đợi...")

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
        "✅ <b>PROXY UPLOAD COMPLETED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: <code>{total}</code>\n"
        f"➕ Added: <code>{added}</code>\n"
        f"👯 Duplicates: <code>{duplicates}</code>\n"
        f"❌ Errors/Dead: <code>{errors}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "The system automatically filtered duplicates and resolved proxy countries."
        if language == 'en' else
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
        [[InlineKeyboardButton(get_back_admin_button_label(language), callback_data='admin_menu')]]
    )

    await processing_msg.edit_text(res_msg, parse_mode='HTML', reply_markup=reply_markup)


async def export_all_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh in toàn bộ user ra file .txt"""
    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

    if user_id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(pick_text(language, "Bạn không có quyền sử dụng lệnh này.", "You are not allowed to use this command."))
        return

    query = update.callback_query
    if query:
        await query.answer()

    status_msg = None
    if update.effective_message:
        status_msg = await update.effective_message.reply_text(
            pick_text(language, "⏳ Đang trích xuất dữ liệu người dùng...", "⏳ Extracting user data...")
        )

    users = db.get_all_users()
    if not users:
        if status_msg:
            await status_msg.edit_text(pick_text(language, "❌ Không có người dùng nào trong hệ thống.", "❌ No users found in the system."))
        return

    # Header cho file
    fields = ["user_id", "username", "full_name", "language", "balance", "is_blocked", "invited_by", "created_at", "last_checkin"]
    header = "|".join(fields)

    output_lines = [header]
    for user in users:
        line_parts = []
        for field in fields:
            val = user.get(field)
            if val is None:
                val = ""
            line_parts.append(str(val))
        output_lines.append("|".join(line_parts))

    file_content = "\n".join(output_lines)
    file_stream = io.BytesIO(file_content.encode('utf-8'))
    file_stream.name = f"all_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if update.effective_message:
        await update.effective_chat.send_document(
            document=file_stream,
            caption=pick_text(
                language,
                f"📊 Danh sách toàn bộ {len(users)} người dùng.",
                f"📊 List of all {len(users)} users."
            )
        )
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
