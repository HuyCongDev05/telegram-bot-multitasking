"""Trình xử lý lệnh quản trị (admin)"""
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command

logger = logging.getLogger(__name__)


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /addbalance - Admin cộng điểm"""
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
        # Kiểm tra xem tham số có tồn tại và không phải None
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
                    f"🪙 Số điểm hiện tại: {user['balance']}"
                )
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (ValueError, TypeError):
        if update.effective_message:
            await update.effective_message.reply_text(
                "Định dạng tham số sai hoặc thiếu thông tin, vui lòng nhập số hợp lệ.")


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /block - Admin chặn người dùng"""
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

            # Gửi thông báo cho người dùng bị chặn
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="❌ <b>Thông báo:</b> Tài khoản của bạn đã bị quản trị viên khóa. Liên hệ @hcongdev để biết thêm chi tiết.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Không thể gửi thông báo chặn cho người dùng {target_user_id}: {e}")
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (ValueError, TypeError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập User ID hợp lệ.")


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /white - Admin hủy chặn người dùng"""
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
                    f"✅ Đã đưa người dùng {target_user_id} ra khỏi danh sách đen.")

            # Gửi thông báo cho người dùng được bỏ chặn
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="✅ <b>Thông báo:</b> Tài khoản của bạn đã được quản trị viên bỏ chặn. Bạn đã có thể sử dụng lại hệ thống.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Không thể gửi thông báo bỏ chặn cho người dùng {target_user_id}: {e}")
        else:
            if update.effective_message:
                await update.effective_message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except (ValueError, TypeError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập User ID hợp lệ.")


async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /blacklist - Xem danh sách đen"""
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

    msg = "📋 Danh sách người dùng bị chặn：\n\n"
    for user in blacklist:
        msg += f"User ID: <code>{user['user_id']}</code>\n"
        msg += f"Username: @{user['username']}\n"
        msg += f"Tên: {user['full_name']}\n"
        msg += "---\n"

    if update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML')


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /genkey - Admin tạo mã thẻ (card key)"""
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
                "Thiếu tham số. Vui lòng sử dụng qua Menu Admin để được hướng dẫn.")
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
                f"Mã thẻ：<code>{key_code}</code>\n"
                f"🪙 Số điểm：{balance}\n"
                f"Số lần dùng：{max_uses} lần\n"
            )
            if expire_days:
                msg += f"Thời hạn：{expire_days} ngày\n"
            else:
                msg += "Thời hạn：Vĩnh viễn\n"
            if update.effective_message:
                await update.effective_message.reply_text(msg, parse_mode='HTML')
            return True
        else:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "Mã thẻ đã tồn tại hoặc tạo thất bại, vui lòng đổi tên mã thẻ.")
            return False
    except (ValueError, TypeError):
        if update.effective_message:
            await update.effective_message.reply_text("Định dạng tham số sai, vui lòng nhập số hợp lệ.")
        return False


async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /listkeys - Admin xem danh sách mã thẻ"""
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

    msg = "📋 Danh sách mã thẻ：\n\n"
    for key in keys[:20]:  # Chỉ hiển thị 20 mã đầu tiên
        msg += f"Mã thẻ：<code>{key['key_code']}</code>\n"
        msg += f"🪙 Số điểm：{key['balance']}\n"
        msg += f"Số lần dùng：{key['current_uses']}/{key['max_uses']}\n"

        if key["expire_at"]:
            expire_time = key["expire_at"]
            if isinstance(expire_time, str):
                expire_time = datetime.fromisoformat(expire_time)
            if datetime.now() > expire_time:
                msg += "Trạng thái：Đã hết hạn\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Trạng thái：Còn hiệu lực (Còn {days_left} ngày)\n"
        else:
            msg += "Trạng thái：Vĩnh viễn\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n（Chỉ hiển thị 20 mã đầu tiên, tổng cộng có {len(keys)} mã）"

    if update.effective_message:
        await update.effective_message.reply_text(msg, parse_mode='HTML')


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /broadcast - Admin gửi thông báo hàng loạt"""
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
                "Cách sử dụng: /broadcast <Nội dung>, hoặc trả lời một tin nhắn rồi gửi /broadcast")
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = None
    if update.effective_message:
        status_msg = await update.effective_message.reply_text(
            f"📢 Bắt đầu phát sóng, tổng cộng {len(user_ids)} người dùng...")

    # Chuẩn bị nội dung thông báo hàng loạt
    final_broadcast_text = f"<b>🔊 Thông báo:</b>\n\n{text}"

    for uid in user_ids:
        # Bỏ qua tài khoản admin
        if uid == ADMIN_USER_ID:
            continue

        try:
            await context.bot.send_message(chat_id=uid, text=final_broadcast_text, parse_mode='HTML')
            success += 1
            await asyncio.sleep(0.05)  # Hạn chế tốc độ để tránh bị giới hạn (rate limiting)
        except Exception as e:
            logger.warning("Gửi tin nhắn đến %s thất bại: %s", uid, e)
            failed += 1

    if status_msg:
        await status_msg.edit_text(f"✅ Phát sóng hoàn tất!\nThành công：{success}\nThất bại：{failed}")
