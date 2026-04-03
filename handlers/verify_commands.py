"""Trình xử lý lệnh xác thực"""
import asyncio
import logging
from typing import Optional

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from config import VERIFY_COST
from database_mysql import Database
from handlers.user_commands import show_main_menu, is_user_busy
from k12.sheerid_verifier import SheerIDVerifier as K12Verifier
from spotify.sheerid_verifier import SheerIDVerifier as SpotifyVerifier
from utils.checks import is_not_blocked
from utils.messages import get_insufficient_balance_message, get_verify_usage_message

# Thử nhập kiểm soát đồng thời, nếu thất bại sẽ sử dụng triển khai trống
try:
    from utils.concurrency import get_verification_semaphore
except ImportError:
    # Nếu nhập thất bại, tạo một triển khai đơn giản
    def get_verification_semaphore():
        return asyncio.Semaphore(3)

logger = logging.getLogger(__name__)


@is_not_blocked
async def verifyChatGPTTeacherK12_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_chatgpt_teacher_k12 - ChatGPT Teacher K12"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id
    if not context.args:
        from handlers.user_commands import start_input_flow
        prompt = get_verify_usage_message("ChatGPT Teacher K12")
        context.user_data['action_service_type'] = 'verify_chatgpt_k12'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"]), parse_mode='HTML')
        await show_main_menu(update, context, db, "⚠️ <i>Số dư không đủ để thực hiện.</i>")
        return

    # Phân tích verificationId
    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("❌ <b>Liên kết SheerID không hợp lệ!</b>", parse_mode='HTML')
        await show_main_menu(update, context, db, "⚠️ Link xác thực không đúng định dạng.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại.")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra và thử lại.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    processing_msg = await update.message.reply_text(
        f"⏳ <b>Đang xử lý xác thực ChatGPT K12...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{verification_id}</code>\n"
        f"🪙 Chi phí: -{VERIFY_COST} điểm\n\n"
        f"🚀 <i>Vui lòng đợi 1-2 phút, hệ thống đang tự động xác thực...</i>",
        parse_mode='HTML'
    )

    try:
        verifier = K12Verifier(verification_id)
        result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "chatgpt_teacher_k12",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = (
                f"✅ <b>Xác thực THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 {service_name} của bạn đã sẵn sàng.\n"
            )
            if result.get("pending"):
                result_msg += "✨ <i>Tài liệu đã gửi, đang chờ xét duyệt thủ công...</i>\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 <b>Link nhận quà:</b>\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n🪙 Số dư hiện tại của bạn: {updated_balance} điểm."

            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại：{result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
            )
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            f"❌ Đã xảy ra lỗi trong quá trình xử lý：{str(e)}\n\n"
            f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
        )


@is_not_blocked
async def verifySpotifyStudent_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_spotify_student - Spotify Student"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id
    if not context.args:
        from handlers.user_commands import start_input_flow
        prompt = get_verify_usage_message("Spotify Student")
        context.user_data['action_service_type'] = 'verify_spotify_student'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"]))
        await show_main_menu(update, context, db, "Số dư không đủ để thực hiện chức năng này.")
        return

    # Phân tích verificationId
    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ.")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại.")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    # Phân tích verificationId
    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra và thử lại.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        f"⏳ <b>Đang xử lý xác thực Spotify Student...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <i>Đang tạo hồ sơ sinh viên...</i>\n"
        f"🎨 <i>Đang thiết kế thẻ sinh viên...</i>\n"
        f"🚀 <i>Đang gửi tài liệu lên SheerID...</i>",
        parse_mode='HTML'
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore()

    try:
        async with semaphore:
            verifier = SpotifyVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "spotify_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = (
                f"✅ <b>Xác thực Spotify THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
            )
            if result.get("pending"):
                result_msg += "✨ <i>Hồ sơ đã gửi, chờ SheerID phê duyệt (vài phút).</i>\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 <b>Link kích hoạt:</b>\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n🪙 Số dư hiện tại của bạn: {updated_balance} điểm."

            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại：{result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
            )
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực Spotify: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            f"❌ Đã xảy ra lỗi trong quá trình xử lý：{str(e)}\n\n"
            f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
        )


@is_not_blocked
async def verifyBoltNewTeacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_bolt_new_teacher - Bolt.new Teacher"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id

    if not context.args:
        from handlers.user_commands import start_input_flow
        prompt = get_verify_usage_message("Bolt.new Teacher")
        context.user_data['action_service_type'] = 'verify_bolt_teacher'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"]))
        await show_main_menu(update, context, db, "Số dư không đủ để thực hiện chức năng này.")
        return

    # Phân tích externalUserId hoặc verificationId
    from Boltnew.sheerid_verifier import SheerIDVerifier as BoltnewVerifier
    verification_id = BoltnewVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ.")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại.")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    # Phân tích externalUserId hoặc verificationId
    external_user_id = BoltnewVerifier.parse_external_user_id(url)
    verification_id = BoltnewVerifier.parse_verification_id(url)

    if not external_user_id and not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra và thử lại.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        f"⏳ <b>Đang xử lý xác thực Bolt.new Teacher...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <i>Đang tiến hành gửi tài liệu xác thực chuyên gia...</i>",
        parse_mode='HTML'
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore()

    try:
        async with semaphore:
            # Bước 1: Gửi tài liệu
            verifier = BoltnewVerifier(url, verification_id=verification_id)
            result = await asyncio.to_thread(verifier.verify)

        if not result.get("success"):
            # Gửi thất bại, hoàn tiền
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                f"❌ Gửi tài liệu thất bại：{result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
            )
            return

        vid = result.get("verification_id", "")
        if not vid:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                f"❌ Không lấy được ID xác thực\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
            )
            return

        # Cập nhật tin nhắn
        await processing_msg.edit_text(
            f"✅ Tài liệu đã được gửi!\n"
            f"📋 ID xác thực: `{vid}`\n\n"
            f"🔍 Đang tự động lấy mã xác thực...\n"
            f"（Chờ tối đa 20 giây）"
        )

        # Bước 2: Tự động lấy mã xác thực (tối đa 20 giây)
        code = await _auto_get_reward_code(vid, max_wait=20, interval=5)

        if code:
            # Lấy mã thành công
            result_msg = (
                f"✅ <b>Xác thực Bolt.new THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎁 <b>Mã xác thực:</b> <code>{code}</code>\n"
            )
            if result.get("redirect_url"):
                result_msg += f"\n🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n🪙 Số dư hiện tại của bạn: {updated_balance} điểm."

            await processing_msg.edit_text(result_msg)

            # Lưu bản ghi thành công
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "success",
                f"Code: {code}",
                vid
            )
        else:
            # Không lấy được trong 20 giây, để người dùng tự tra cứu sau
            await processing_msg.edit_text(
                f"✅ Tài liệu đã gửi thành công!\n\n"
                f"⏳ Mã xác thực chưa được tạo (có thể mất 1-5 phút xét duyệt)\n\n"
                f"📋 ID xác thực: `{vid}`\n\n"
                f"💡 Vui lòng sử dụng lệnh sau để tra cứu sau:\n"
                f"`/getV4Code {vid}`\n\n"
                f"Lưu ý: Điểm đã bị tiêu hao, tra cứu sau sẽ không mất thêm phí"
            )

            # Lưu bản ghi chờ xử lý
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "pending",
                "Waiting for review",
                vid
            )

    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực Bolt.new: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            f"❌ Đã xảy ra lỗi trong quá trình xử lý：{str(e)}\n\n"
            f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
        )


async def _auto_get_reward_code(
        verification_id: str,
        max_wait: int = 20,
        interval: int = 5
) -> Optional[str]:
    """Tự động lấy mã xác thực (pooling nhẹ, không ảnh hưởng đến đồng thời)
    
    Args:
        verification_id: ID xác thực
        max_wait: Thời gian chờ tối đa (giây)
        interval: Khoảng thời gian tra cứu (giây)
        
    Returns:
        str: Mã xác thực, trả về None nếu lấy thất bại
    """
    import time
    start_time = time.time()
    attempts = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            elapsed = int(time.time() - start_time)
            attempts += 1

            # Kiểm tra xem có quá thời gian không
            if elapsed >= max_wait:
                logger.info(f"Tự động lấy mã hết thời gian ({elapsed} giây), để người dùng tự tra cứu")
                return None

            try:
                # Tra cứu trạng thái xác thực
                response = await client.get(
                    f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
                )

                if response.status_code == 200:
                    data = response.json()
                    current_step = data.get("currentStep")

                    if current_step == "success":
                        # Lấy mã xác thực
                        code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
                        if code:
                            logger.info(f"✅ Tự động lấy mã thành công: {code} (mất {elapsed} giây)")
                            return code
                    elif current_step == "error":
                        # Xét duyệt thất bại
                        logger.warning(f"Xét duyệt thất bại: {data.get('errorIds', [])}")
                        return None
                    # else: pending, tiếp tục chờ

                # Chờ cho lần tra cứu tiếp theo
                await asyncio.sleep(interval)

            except Exception as e:
                logger.warning(f"Lỗi khi tra cứu mã xác thực: {e}")
                await asyncio.sleep(interval)


@is_not_blocked
async def verifyYouTubePremiumStudent_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_youtube_premium_student - YouTube Student Premium"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id

    if not context.args:
        from handlers.user_commands import start_input_flow
        prompt = get_verify_usage_message("YouTube Student Premium")
        context.user_data['action_service_type'] = 'verify_youtube_student'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"]))
        await show_main_menu(update, context, db, "Số dư không đủ để thực hiện chức năng này.")
        return

    # Phân tích verificationId
    from youtube.sheerid_verifier import SheerIDVerifier as YouTubeVerifier
    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ.")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại.")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    # Phân tích verificationId
    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra và thử lại.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        # Xóa tin nhắn gốc của người dùng chứa URL
        if update.message:
            try:
                await update.message.delete()
            except Exception as e:
                logger.error(f"Không thể xóa tin nhắn gốc chứa URL (ID: {update.message.message_id}): {e}")
        await show_main_menu(update, context, db, "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        f"⏳ <b>Đang xử lý YouTube Premium...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 <i>Đang xử lý hồ sơ và thẻ sinh viên...</i>\n"
        f"🚀 <i>Đang gửi tài liệu xác thực lên YouTube...</i>",
        parse_mode='HTML'
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore()

    try:
        async with semaphore:
            verifier = YouTubeVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "youtube_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Xác thực YouTube Student Premium thành công!\n\n"
            if result.get("pending"):
                result_msg += "✨ Tài liệu đã được gửi, chờ SheerID xét duyệt\n"
                result_msg += "⏱️ Thời gian xét duyệt dự kiến: trong vài phút\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Liên kết chuyển hướng：\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n🪙 Số dư hiện tại của bạn: {updated_balance} điểm."

            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại：{result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
            )
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực YouTube: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            f"❌ Đã xảy ra lỗi trong quá trình xử lý：{str(e)}\n\n"
            f"Đã hoàn trả {VERIFY_COST} điểm. 🪙 Số dư hiện tại: {updated_balance} điểm."
        )


@is_not_blocked
async def getBoltNewTeacherCode_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /getV4Code - Lấy mã xác thực Bolt.new Teacher"""
    user_id = update.effective_user.id

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    # Kiểm tra xem có cung cấp verification_id không
    if not context.args:
        await update.message.reply_text(
            "Cách sử dụng: /getV4Code <verification_id>\n\n"
            "Ví dụ: /getV4Code 6929436b50d7dc18638890d0\n\n"
            "verification_id sẽ được gửi cho bạn sau khi sử dụng lệnh /verify4."
        )
        return

    verification_id = context.args[0].strip()

    processing_msg = await update.message.reply_text(
        "🔍 Đang truy vấn mã xác thực, vui lòng chờ..."
    )

    try:
        # Truy vấn SheerID API để lấy mã xác thực
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
            )

            if response.status_code != 200:
                await processing_msg.edit_text(
                    f"❌ Truy vấn thất bại, mã trạng thái: {response.status_code}\n\n"
                    "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
                )
                return

            data = response.json()
            current_step = data.get("currentStep")
            reward_code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
            redirect_url = data.get("redirectUrl")

            if current_step == "success" and reward_code:
                result_msg = "✅ Xác thực thành công!\n\n"
                result_msg += f"🎉 Mã xác thực: `{reward_code}`\n\n"
                if redirect_url:
                    result_msg += f"Liên kết chuyển hướng:\n{redirect_url}"
                await processing_msg.edit_text(result_msg)
            elif current_step == "pending":
                await processing_msg.edit_text(
                    "⏳ Xác thực vẫn đang trong quá trình xét duyệt, vui lòng thử lại sau.\n\n"
                    "Thường mất từ 1-5 phút, vui lòng kiên nhẫn chờ đợi."
                )
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                await processing_msg.edit_text(
                    f"❌ Xác thực thất bại\n\n"
                    f"Thông tin lỗi: {', '.join(error_ids) if error_ids else 'Lỗi không xác định'}"
                )
            else:
                await processing_msg.edit_text(
                    f"⚠️ Trạng thái hiện tại: {current_step}\n\n"
                    "Mã xác thực chưa được tạo, vui lòng thử lại sau."
                )

    except Exception as e:
        logger.error("Lấy mã xác thực Bolt.new thất bại: %s", e)
        await processing_msg.edit_text(
            f"❌ Đã xảy ra lỗi trong quá trình truy vấn: {str(e)}\n\n"
            "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
        )


@is_not_blocked
async def verifyGeminiOnePro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /verify_gemini_one_pro - Gemini One Pro"""
    if await is_user_busy(update, context):
        return


    if not context.args:
        from handlers.user_commands import start_input_flow
        prompt = get_verify_usage_message("Gemini One Pro")
        context.user_data['action_service_type'] = 'verify_gemini_pro'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    register_cleanup_message(context, update.message.message_id)

    # Placeholder logic (vì chưa có verifier cho Gemini)
    await update.message.reply_text("Chức năng xác thực Gemini One Pro đang được phát triển. Vui lòng quay lại sau!")
