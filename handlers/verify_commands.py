"""Trình xử lý lệnh xác thực."""
import asyncio
import logging
from typing import Optional

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from config import VERIFY_COST
from database import Database
from handlers.user_commands import is_user_busy, show_main_menu_after_delay
from k12.sheerid_verifier import SheerIDVerifier as K12Verifier
from spotify.sheerid_verifier import SheerIDVerifier as SpotifyVerifier
from utils.checks import is_not_blocked
from utils.i18n import DEFAULT_LANGUAGE, get_user_language
from utils.messages import get_insufficient_balance_message, get_verify_usage_message

try:
    from utils.concurrency import get_verification_semaphore
except ImportError:
    def get_verification_semaphore():
        return asyncio.Semaphore(3)

logger = logging.getLogger(__name__)

_BUILD_SIG = "687579636f6e676465763035"


def i18n_text(language: str, vi_text: str, en_text: str) -> str:
    """Chọn chuỗi theo ngôn ngữ."""
    return en_text if language == 'en' else vi_text


async def _delete_source_message(update: Update):
    if not update.message:
        return

    try:
        await update.message.delete()
    except Exception as e:
        logger.error(
            "Khong the xoa tin nhan goc chua URL (ID: %s): %s",
            update.message.message_id,
            e,
        )


@is_not_blocked
async def verifyChatGPTTeacherK12_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_chatgpt_teacher_k12 - ChatGPT Teacher K12."""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'verify_chatgpt_k12'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    service_name = "ChatGPT Teacher K12"
    if not context.args:
        from handlers.user_commands import start_input_flow

        prompt = get_verify_usage_message(service_name, language)
        context.user_data['action_service_type'] = 'verify_chatgpt_k12'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message

    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"], language), parse_mode='HTML')
        await show_main_menu_after_delay(
            update,
            context,
            db,
            "⚠️ <i>Insufficient balance.</i>" if language == 'en' else "⚠️ <i>Số dư không đủ để thực hiện.</i>",
        )
        return

    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text(
            "❌ <b>Invalid SheerID link!</b>" if language == 'en' else "❌ <b>Liên kết SheerID không hợp lệ!</b>",
            parse_mode='HTML',
        )
        await show_main_menu_after_delay(
            update,
            context,
            db,
            "⚠️ Invalid verification link format." if language == 'en' else "⚠️ Link xác thực không đúng định dạng.",
        )
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        await show_main_menu_after_delay(update, context, db, "Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        (
            "⏳ <b>Processing ChatGPT K12 verification...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{verification_id}</code>\n"
            f"💰 Cost: -{VERIFY_COST} points\n\n"
            "🚀 <i>Please wait 1-2 minutes while the system verifies automatically...</i>"
            if language == 'en'
            else "⏳ <b>Đang xử lý xác thực ChatGPT K12...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{verification_id}</code>\n"
            f"💰 Chi phí: -{VERIFY_COST} điểm\n\n"
            "🚀 <i>Vui lòng đợi 1-2 phút, hệ thống đang tự động xác thực...</i>"
        ),
        parse_mode='HTML',
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
                "✅ <b>VERIFICATION SUCCESSFUL!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 Your {service_name} is ready.\n"
                if language == 'en' else
                "✅ <b>Xác thực THÀNH CÔNG!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 {service_name} của bạn đã sẵn sàng.\n"
            )
            if result.get("pending"):
                result_msg += "✨ <i>Documents submitted, waiting for manual review...</i>\n" if language == 'en' else "✨ <i>Tài liệu đã gửi, đang chờ xét duyệt thủ công...</i>\n"
            if result.get("redirect_url"):
                result_msg += (
                    f"🔗 <b>Claim link:</b>\n{result['redirect_url']}"
                    if language == 'en'
                    else f"🔗 <b>Link nhận quà:</b>\n{result['redirect_url']}"
                )

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n💰 Your current balance: {updated_balance} points." if language == 'en' else f"\n💰 Số dư hiện tại của bạn: {updated_balance} điểm."
            await processing_msg.edit_text(result_msg, parse_mode='HTML')
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                (
                    f"❌ Verification failed: {result.get('message', 'Unknown error')}\n\n"
                    f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                    if language == 'en'
                    else f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                    f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
                )
            )

        await show_main_menu_after_delay(update, context, db)
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực ChatGPT K12: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            (
                f"❌ An error occurred while processing: {str(e)}\n\n"
                f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                if language == 'en'
                else f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
            )
        )
        await show_main_menu_after_delay(update, context, db)


@is_not_blocked
async def verifySpotifyStudent_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_spotify_student - Spotify Student."""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'verify_spotify_student'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if not context.args:
        from handlers.user_commands import start_input_flow

        prompt = get_verify_usage_message("Spotify Student", language)
        context.user_data['action_service_type'] = 'verify_spotify_student'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message

    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"], language))
        await show_main_menu_after_delay(update, context, db, "Insufficient balance for this feature." if language == 'en' else "Số dư không đủ để thực hiện chức năng này.")
        return

    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Invalid SheerID link." if language == 'en' else "Liên kết SheerID không hợp lệ.")
        await _delete_source_message(update)
        await show_main_menu_after_delay(update, context, db, "Invalid SheerID link." if language == 'en' else "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        await show_main_menu_after_delay(update, context, db, "Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        (
            "⏳ <b>Processing Spotify Student verification...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <i>Generating student profile...</i>\n"
            "🎨 <i>Designing student card...</i>\n"
            "🚀 <i>Uploading documents to SheerID...</i>"
            if language == 'en'
            else "⏳ <b>Đang xử lý xác thực Spotify Student...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <i>Đang tạo hồ sơ sinh viên...</i>\n"
            "🎨 <i>Đang thiết kế thẻ sinh viên...</i>\n"
            "🚀 <i>Đang gửi tài liệu lên SheerID...</i>"
        ),
        parse_mode='HTML',
    )

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
                "✅ <b>Spotify verification successful!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                if language == 'en' else
                "✅ <b>Xác thực Spotify THÀNH CÔNG!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
            )
            if result.get("pending"):
                result_msg += "✨ <i>Your documents were submitted and are waiting for SheerID approval (a few minutes).</i>\n" if language == 'en' else "✨ <i>Hồ sơ đã gửi, chờ SheerID phê duyệt (vài phút).</i>\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 <b>Activation link:</b>\n{result['redirect_url']}" if language == 'en' else f"🔗 <b>Link kích hoạt:</b>\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n💰 Your current balance: {updated_balance} points." if language == 'en' else f"\n💰 Số dư hiện tại của bạn: {updated_balance} điểm."
            await processing_msg.edit_text(result_msg, parse_mode='HTML')
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                (
                    f"❌ Verification failed: {result.get('message', 'Unknown error')}\n\n"
                    f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                    if language == 'en'
                    else f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                    f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
                )
            )

        await show_main_menu_after_delay(update, context, db)
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực Spotify: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            (
                f"❌ An error occurred while processing: {str(e)}\n\n"
                f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                if language == 'en'
                else f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
            )
        )
        await show_main_menu_after_delay(update, context, db)


@is_not_blocked
async def verifyBoltNewTeacher_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_bolt_new_teacher - Bolt.new Teacher."""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'verify_bolt_teacher'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if not context.args:
        from handlers.user_commands import start_input_flow

        prompt = get_verify_usage_message("Bolt.new Teacher", language)
        context.user_data['action_service_type'] = 'verify_bolt_teacher'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    from Boltnew.sheerid_verifier import SheerIDVerifier as BoltnewVerifier

    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"], language))
        await show_main_menu_after_delay(update, context, db, "Insufficient balance for this feature." if language == 'en' else "Số dư không đủ để thực hiện chức năng này.")
        return

    external_user_id = BoltnewVerifier.parse_external_user_id(url)
    verification_id = BoltnewVerifier.parse_verification_id(url)
    if not external_user_id and not verification_id:
        await update.message.reply_text("Invalid SheerID link. Please check it and try again." if language == 'en' else "Liên kết SheerID không hợp lệ, vui lòng kiểm tra và thử lại.")
        await _delete_source_message(update)
        await show_main_menu_after_delay(update, context, db, "Invalid SheerID link." if language == 'en' else "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        await show_main_menu_after_delay(update, context, db, "Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        (
            "⏳ <b>Processing Bolt.new Teacher verification...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 <i>Submitting expert verification documents...</i>"
            if language == 'en'
            else "⏳ <b>Đang xử lý xác thực Bolt.new Teacher...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 <i>Đang tiến hành gửi tài liệu xác thực chuyên gia...</i>"
        ),
        parse_mode='HTML',
    )

    semaphore = get_verification_semaphore()

    try:
        async with semaphore:
            verifier = BoltnewVerifier(url, verification_id=verification_id)
            result = await asyncio.to_thread(verifier.verify)

        if not result.get("success"):
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                (
                    f"❌ Document submission failed: {result.get('message', 'Unknown error')}\n\n"
                    f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                    if language == 'en'
                    else f"❌ Gửi tài liệu thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                    f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
                )
            )
            await show_main_menu_after_delay(update, context, db)
            return

        vid = result.get("verification_id", "")
        if not vid:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                (
                    "❌ Could not obtain the verification ID\n\n"
                    f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                    if language == 'en'
                    else "❌ Không lấy được ID xác thực\n\n"
                    f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
                )
            )
            await show_main_menu_after_delay(update, context, db)
            return

        await processing_msg.edit_text(
            (
                "✅ Documents submitted!\n"
                f"📋 Verification ID: <code>{vid}</code>\n\n"
                "🔍 Automatically retrieving the reward code...\n"
                "(Waiting up to 20 seconds)"
                if language == 'en'
                else "✅ Tài liệu đã được gửi!\n"
                f"📋 ID xác thực: <code>{vid}</code>\n\n"
                "🔍 Đang tự động lấy mã xác thực...\n"
                "(Chờ tối đa 20 giây)"
            ),
            parse_mode='HTML',
        )

        code = await _auto_get_reward_code(vid, max_wait=20, interval=5)

        if code:
            result_msg = (
                "✅ <b>Bolt.new verification successful!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎁 <b>Reward code:</b> <code>{code}</code>\n"
                if language == 'en' else
                "✅ <b>Xác thực Bolt.new THÀNH CÔNG!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🎁 <b>Mã xác thực:</b> <code>{code}</code>\n"
            )
            if result.get("redirect_url"):
                result_msg += f"\n🔗 Redirect link:\n{result['redirect_url']}" if language == 'en' else f"\n🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n💰 Your current balance: {updated_balance} points." if language == 'en' else f"\n💰 Số dư hiện tại của bạn: {updated_balance} điểm."
            await processing_msg.edit_text(result_msg, parse_mode='HTML')
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "success",
                f"Code: {code}",
                vid,
            )
        else:
            await processing_msg.edit_text(
                (
                    "✅ Documents submitted successfully!\n\n"
                    "⏳ The reward code has not been generated yet (review may take 1-5 minutes).\n\n"
                    f"📋 Verification ID: <code>{vid}</code>\n\n"
                    "💡 Use this command to check later:\n"
                    f"<code>/getV4Code {vid}</code>\n\n"
                    "Note: The points have already been charged, and checking later will not cost extra."
                    if language == 'en'
                    else "✅ Tài liệu đã gửi thành công!\n\n"
                    "⏳ Mã xác thực chưa được tạo (có thể mất 1-5 phút xét duyệt)\n\n"
                    f"📋 ID xác thực: <code>{vid}</code>\n\n"
                    "💡 Vui lòng sử dụng lệnh sau để tra cứu sau:\n"
                    f"<code>/getV4Code {vid}</code>\n\n"
                    "Lưu ý: Điểm đã bị tiêu hao, tra cứu sau sẽ không mất thêm phí."
                ),
                parse_mode='HTML',
            )
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "pending",
                "Waiting for review",
                vid,
            )

        await show_main_menu_after_delay(update, context, db)
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực Bolt.new: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            (
                f"❌ An error occurred while processing: {str(e)}\n\n"
                f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                if language == 'en'
                else f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
            )
        )
        await show_main_menu_after_delay(update, context, db)


async def _auto_get_reward_code(
        verification_id: str,
        max_wait: int = 20,
        interval: int = 5,
) -> Optional[str]:
    """Tự động lấy mã xác thực bằng polling nhẹ."""
    import time

    start_time = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            elapsed = int(time.time() - start_time)
            if elapsed >= max_wait:
                logger.info("Tu dong lay ma het thoi gian sau %s giay", elapsed)
                return None

            try:
                response = await client.get(
                    f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    current_step = data.get("currentStep")

                    if current_step == "success":
                        code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
                        if code:
                            logger.info("Lay ma Bolt.new thanh cong sau %s giay", elapsed)
                            return code
                    elif current_step == "error":
                        logger.warning("Xet duyet Bolt.new that bai: %s", data.get("errorIds", []))
                        return None

                await asyncio.sleep(interval)
            except Exception as e:
                logger.warning("Lỗi khi tra cứu mã xác thực Bolt.new: %s", e)
                await asyncio.sleep(interval)


@is_not_blocked
async def verifyYouTubePremiumStudent_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_youtube_premium_student - YouTube Student Premium."""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'verify_youtube_student'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    if not context.args:
        from handlers.user_commands import start_input_flow

        prompt = get_verify_usage_message("YouTube Student Premium", language)
        context.user_data['action_service_type'] = 'verify_youtube_student'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message
    from youtube.sheerid_verifier import SheerIDVerifier as YouTubeVerifier

    register_cleanup_message(context, update.message.message_id)

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"], language))
        await show_main_menu_after_delay(update, context, db, "Insufficient balance for this feature." if language == 'en' else "Số dư không đủ để thực hiện chức năng này.")
        return

    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Invalid SheerID link." if language == 'en' else "Liên kết SheerID không hợp lệ.")
        await _delete_source_message(update)
        await show_main_menu_after_delay(update, context, db, "Invalid SheerID link." if language == 'en' else "Liên kết SheerID không hợp lệ.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        await show_main_menu_after_delay(update, context, db, "Failed to deduct points." if language == 'en' else "Trừ điểm thất bại.")
        return

    processing_msg = await update.message.reply_text(
        (
            "⏳ <b>Processing YouTube Premium...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎨 <i>Processing student profile and card...</i>\n"
            "🚀 <i>Uploading verification documents to YouTube...</i>"
            if language == 'en'
            else "⏳ <b>Đang xử lý YouTube Premium...</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎨 <i>Đang xử lý hồ sơ và thẻ sinh viên...</i>\n"
            "🚀 <i>Đang gửi tài liệu xác thực lên YouTube...</i>"
        ),
        parse_mode='HTML',
    )

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
            result_msg = "✅ YouTube Student Premium verification successful!\n\n" if language == 'en' else "✅ Xác thực YouTube Student Premium thành công!\n\n"
            if result.get("pending"):
                result_msg += "✨ Documents submitted, waiting for SheerID approval.\n" if language == 'en' else "✨ Tài liệu đã được gửi, chờ SheerID xét duyệt.\n"
                result_msg += "⏱️ Estimated review time: a few minutes.\n\n" if language == 'en' else "⏱️ Thời gian xét duyệt dự kiến: trong vài phút.\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Redirect link:\n{result['redirect_url']}" if language == 'en' else f"🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"

            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            result_msg += f"\n💰 Your current balance: {updated_balance} points." if language == 'en' else f"\n💰 Số dư hiện tại của bạn: {updated_balance} điểm."
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            updated_user = db.get_user(user_id)
            updated_balance = updated_user['balance'] if updated_user else 0
            await processing_msg.edit_text(
                (
                    f"❌ Verification failed: {result.get('message', 'Unknown error')}\n\n"
                    f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                    if language == 'en'
                    else f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                    f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
                )
            )

        await show_main_menu_after_delay(update, context, db)
    except Exception as e:
        logger.error("Lỗi trong quá trình xác thực YouTube: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        updated_user = db.get_user(user_id)
        updated_balance = updated_user['balance'] if updated_user else 0
        await processing_msg.edit_text(
            (
                f"❌ An error occurred while processing: {str(e)}\n\n"
                f"Refunded {VERIFY_COST} points. 💰 Current balance: {updated_balance} points."
                if language == 'en'
                else f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}\n\n"
                f"Đã hoàn trả {VERIFY_COST} điểm. 💰 Số dư hiện tại: {updated_balance} điểm."
            )
        )
        await show_main_menu_after_delay(update, context, db)


@is_not_blocked
async def getBoltNewTeacherCode_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /getV4Code - Lấy mã xác thực Bolt.new Teacher."""
    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

    if not db.user_exists(user_id):
        await update.message.reply_text("Please use /start to register first." if language == 'en' else "Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            (
                "Usage: /getV4Code <verification_id>\n\n"
                "Example: /getV4Code 6929436b50d7dc18638890d0\n\n"
                "The verification_id will be sent to you after using the Bolt verification flow."
                if language == 'en'
                else "Cách sử dụng: /getV4Code <verification_id>\n\n"
                "Ví dụ: /getV4Code 6929436b50d7dc18638890d0\n\n"
                "verification_id sẽ được gửi cho bạn sau khi sử dụng lệnh /verify4."
            )
        )
        return

    verification_id = context.args[0].strip()
    processing_msg = await update.message.reply_text("🔍 Querying the reward code, please wait..." if language == 'en' else "🔍 Đang truy vấn mã xác thực, vui lòng chờ...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
            )

            if response.status_code != 200:
                await processing_msg.edit_text(
                    (
                        f"❌ Query failed, status code: {response.status_code}\n\n"
                        "Please try again later or contact the admin."
                        if language == 'en'
                        else f"❌ Truy vấn thất bại, mã trạng thái: {response.status_code}\n\n"
                        "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
                    )
                )
                return

            data = response.json()
            current_step = data.get("currentStep")
            reward_code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
            redirect_url = data.get("redirectUrl")

            if current_step == "success" and reward_code:
                result_msg = "✅ Verification successful!\n\n" if language == 'en' else "✅ Xác thực thành công!\n\n"
                result_msg += f"🎉 Reward code: <code>{reward_code}</code>\n\n" if language == 'en' else f"🎉 Mã xác thực: <code>{reward_code}</code>\n\n"
                if redirect_url:
                    result_msg += f"Redirect link:\n{redirect_url}" if language == 'en' else f"Liên kết chuyển hướng:\n{redirect_url}"
                await processing_msg.edit_text(result_msg, parse_mode='HTML')
            elif current_step == "pending":
                await processing_msg.edit_text(
                    "⏳ Verification is still under review. Please try again later.\n\nIt usually takes 1-5 minutes."
                    if language == 'en'
                    else "⏳ Xác thực vẫn đang trong quá trình xét duyệt, vui lòng thử lại sau.\n\n"
                    "Thường mất từ 1-5 phút, vui lòng kiên nhẫn chờ đợi."
                )
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                await processing_msg.edit_text(
                    (
                        "❌ Verification failed\n\n"
                        f"Error details: {', '.join(error_ids) if error_ids else 'Unknown error'}"
                        if language == 'en'
                        else "❌ Xác thực thất bại\n\n"
                        f"Thông tin lỗi: {', '.join(error_ids) if error_ids else 'Lỗi không xác định'}"
                    )
                )
            else:
                await processing_msg.edit_text(
                    (
                        f"⚠️ Current status: {current_step}\n\n"
                        "The reward code has not been generated yet. Please try again later."
                        if language == 'en'
                        else f"⚠️ Trạng thái hiện tại: {current_step}\n\n"
                        "Mã xác thực chưa được tạo, vui lòng thử lại sau."
                    )
                )
    except Exception as e:
        logger.error("Lấy mã xác thực Bolt.new thất bại: %s", e)
        await processing_msg.edit_text(
            (
                f"❌ An error occurred while querying: {str(e)}\n\n"
                "Please try again later or contact the admin."
                if language == 'en'
                else f"❌ Đã xảy ra lỗi trong quá trình truy vấn: {str(e)}\n\n"
                "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
            )
        )
    finally:
        await show_main_menu_after_delay(update, context, db)


@is_not_blocked
async def verifyGeminiOnePro_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify_gemini_one_pro - Gemini One Pro."""
    if await is_user_busy(update, context, db):
        return

    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'verify_gemini_pro'):
        return

    if not context.args:
        from handlers.user_commands import start_input_flow

        language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
        prompt = get_verify_usage_message("Gemini One Pro", language)
        context.user_data['action_service_type'] = 'verify_gemini_pro'
        await start_input_flow(update, context, prompt, 'verify_step_1', 'cancel_to_verify_menu')
        return

    from handlers.user_commands import register_cleanup_message

    register_cleanup_message(context, update.message.message_id)
    language = get_user_language(db, update.effective_user.id, default=DEFAULT_LANGUAGE)
    await update.message.reply_text(
        "The Gemini One Pro verification feature is still under development. Please come back later!"
        if language == 'en'
        else "Chức năng xác thực Gemini One Pro đang được phát triển. Vui lòng quay lại sau!"
    )
