"""Trình xử lý Discord Quest Auto"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import DISCORD_QUEST_COST
from database_mysql import Database
from discordQuestAuto.discordQuestAuto import start_quest_auto
from handlers.user_commands import is_user_busy, send_or_reply, show_main_menu_after_delay
from utils.i18n import DEFAULT_LANGUAGE, get_user_language
from utils.checks import is_not_blocked, check_maintenance
from utils.messages import get_insufficient_balance_message, get_ui_label

logger = logging.getLogger(__name__)

# Internal build sign ID
_BUILD_SIG = "687579636f6e676465763035"


@is_not_blocked
async def discord_quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /discord_quest_auto"""
    if await is_user_busy(update, context, db):
        return

    if await check_maintenance(update, db, 'discord_quest_auto'):
        return

    user_id = update.effective_user.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)
    user = db.get_user(user_id)
    
    if user["balance"] < DISCORD_QUEST_COST:
        await send_or_reply(update, context, get_insufficient_balance_message(user["balance"], language), parse_mode='HTML')
        await show_main_menu_after_delay(
            update,
            context,
            db,
            "⚠️ <i>Insufficient balance to use Discord Quest Auto.</i>"
            if language == 'en'
            else "⚠️ <i>Số dư không đủ để sử dụng Discord Quest Auto.</i>",
        )
        return

    context.user_data['action_service_type'] = 'discord_quest'
    service_label = get_ui_label('discord_quest_auto', language)

    prompt_text = (
        f"<b>{service_label}</b>\n\n"
        + (
            f"This feature will automatically complete your Discord quests.\n"
            f"Cost: 💰 <b>{DISCORD_QUEST_COST} points</b>\n\n"
            f"Please send your <b>Discord Token</b> in the reply message below:\n"
            f"<i>(The token will be deleted immediately after receipt for safety.)</i>"
            if language == 'en'
            else f"Chức năng này sẽ tự động hoàn thành các Quest trên Discord của bạn.\n"
            f"Chi phí: 💰 <b>{DISCORD_QUEST_COST} điểm</b>\n\n"
            f"Vui lòng gửi <b>Discord Token</b> của bạn vào tin nhắn trả lời bên dưới:\n"
            f"<i>(Token sẽ được xóa ngay sau khi nhận để đảm bảo an toàn)</i>"
        )
    )

    from handlers.user_commands import start_input_flow
    await start_input_flow(update, context, prompt_text, 'discord_quest_step_1', 'cancel_to_main')

async def process_discord_token(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, token: str):
    """Xử lý token Discord và bắt đầu tác vụ chạy ngầm"""
    # Kiểm tra bảo trì
    from utils.checks import check_maintenance
    if await check_maintenance(update, db, 'discord_quest_auto'):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    language = get_user_language(db, user_id, default=DEFAULT_LANGUAGE)

    async def return_to_main_menu(message_text: str = ""):
        await show_main_menu_after_delay(update, context, db, message_text)

    # Xóa tin nhắn chứa token ngay lập tức
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Không thể xóa tin nhắn chứa token: {e}")

    # Kiểm tra số dư lần nữa (phòng hờ)
    user = db.get_user(user_id)
    if user["balance"] < DISCORD_QUEST_COST:
        await context.bot.send_message(chat_id=chat_id, text="❌ Insufficient balance!" if language == 'en' else "❌ Số dư không đủ!")
        await return_to_main_menu(
            "⚠️ <i>Insufficient balance to use Discord Quest Auto.</i>"
            if language == 'en'
            else "⚠️ <i>Số dư không đủ để sử dụng Discord Quest Auto.</i>"
        )
        return

    # Trừ điểm
    if not db.deduct_balance(user_id, DISCORD_QUEST_COST):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to deduct points. Please try again later." if language == 'en' else "❌ Lỗi trừ điểm, vui lòng thử lại sau.",
        )
        await return_to_main_menu("❌ Failed to deduct points." if language == 'en' else "❌ Trừ điểm thất bại.")
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ Deducted {DISCORD_QUEST_COST} points. Verifying the token..."
            if language == 'en'
            else f"✅ Đã trừ {DISCORD_QUEST_COST} điểm. Đang xác thực token..."
        ),
        parse_mode='HTML'
    )

    # Chạy tác vụ trong nền
    # Lưu ý: start_quest_auto là async, chúng ta sẽ create_task để không làm treo bot
    async def run_quest_task():
        try:
            success = await start_quest_auto(token, context.bot, chat_id)
            if not success:
                # Nếu xác thực thất bại ngay từ đầu, hoàn tiền
                db.add_balance(user_id, DISCORD_QUEST_COST)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Invalid Discord token! Points have been refunded." if language == 'en' else "❌ Token Discord không hợp lệ! Đã hoàn lại điểm.",
                    parse_mode='HTML'
                )
                await return_to_main_menu("❌ Invalid Discord token." if language == 'en' else "❌ Token Discord không hợp lệ.")
                return
        except Exception as e:
            logger.error(f"Lỗi trong tác vụ Discord Quest: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"❌ An error occurred while running Discord Quest Auto: {str(e)}"
                    if language == 'en'
                    else f"❌ Đã xảy ra lỗi khi chạy Discord Quest Auto: {str(e)}"
                ),
                parse_mode='HTML'
            )
            await return_to_main_menu("❌ Discord Quest Auto failed." if language == 'en' else "❌ Discord Quest Auto gặp lỗi.")
            return

        await return_to_main_menu()

    asyncio.create_task(run_quest_task())
