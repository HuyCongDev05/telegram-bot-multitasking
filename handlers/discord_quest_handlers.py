"""Trình xử lý Discord Quest Auto"""
import asyncio
import logging
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import DISCORD_QUEST_COST
from database_mysql import Database
from handlers.user_commands import show_main_menu, is_user_busy, register_cleanup_message, clear_user_state
from utils.checks import is_not_blocked
from utils.messages import get_insufficient_balance_message
from discordQuestAuto.discordQuestAuto import start_quest_auto

logger = logging.getLogger(__name__)

@is_not_blocked
async def discord_quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /discord_quest_auto"""
    if await is_user_busy(update, context):
        return

    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user["balance"] < DISCORD_QUEST_COST:
        await update.message.reply_text(get_insufficient_balance_message(user["balance"]), parse_mode='HTML')
        await show_main_menu(update, context, db, "⚠️ <i>Số dư không đủ để sử dụng Discord Quest Auto.</i>")
        return

    context.user_data['action_service_type'] = 'discord_quest'
    
    prompt_text = (
        f"🚀 <b>Discord Quest Auto</b>\n\n"
        f"Chức năng này sẽ tự động hoàn thành các Quest trên Discord của bạn.\n"
        f"Chi phí: 🪙 <b>{DISCORD_QUEST_COST} điểm</b>\n\n"
        f"Vui lòng gửi <b>Discord Token</b> của bạn vào tin nhắn trả lời bên dưới:\n"
        f"<i>(Token sẽ được xóa ngay sau khi nhận để đảm bảo an toàn)</i>"
    )

    from handlers.user_commands import start_input_flow
    await start_input_flow(update, context, prompt_text, 'discord_quest_step_1', 'cancel_to_main')

async def process_discord_token(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, token: str):
    """Xử lý token Discord và bắt đầu tác vụ chạy ngầm"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Xóa tin nhắn chứa token ngay lập tức
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Không thể xóa tin nhắn chứa token: {e}")

    # Kiểm tra số dư lần nữa (phòng hờ)
    user = db.get_user(user_id)
    if user["balance"] < DISCORD_QUEST_COST:
        await context.bot.send_message(chat_id=chat_id, text="❌ Số dư không đủ!")
        return

    # Trừ điểm
    if not db.deduct_balance(user_id, DISCORD_QUEST_COST):
        await context.bot.send_message(chat_id=chat_id, text="❌ Lỗi trừ điểm, vui lòng thử lại sau.")
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Đã trừ {DISCORD_QUEST_COST} điểm. Đang xác thực token...",
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
                    text="❌ Token Discord không hợp lệ! Đã hoàn lại điểm.",
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Lỗi trong tác vụ Discord Quest: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Đã xảy ra lỗi khi chạy Discord Quest Auto: {str(e)}",
                parse_mode='HTML'
            )

    asyncio.create_task(run_quest_task())
    
    # Quay về menu chính
    await show_main_menu(update, context, db)
