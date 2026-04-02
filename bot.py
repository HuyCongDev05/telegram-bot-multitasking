"""Chương trình chính của Telegram Bot"""
import logging
from functools import partial

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN
from database_mysql import Database
from handlers.admin_commands import (
    addbalance_command,
    block_command,
    white_command,
    blacklist_command,
    genkey_command,
    listkeys_command,
    broadcast_command,
)
from handlers.user_commands import (
    start_command,
    help_command,
    button_callback,
    handle_text_input,
    handle_file_input,
)
from handlers.verify_commands import (
    verifyChatGPTTeacherK12_command,
    verifySpotifyStudent_command,
    verifyBoltNewTeacher_command,
    verifyYouTubePremiumStudent_command,
    getBoltNewTeacherCode_command,
)

# Cấu hình logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lỗi toàn cục"""
    logger.error("Exception while handling an update:", exc_info=context.error)


def main():
    """Hàm chính"""
    # Khởi tạo cơ sở dữ liệu
    db = Database()

    # Tạo ứng dụng - Cho phép xử lý đồng thời
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .concurrent_updates(True)
        .build()
    )

    # Đăng ký các lệnh người dùng
    application.add_handler(CommandHandler("start", partial(start_command, db=db)))
    application.add_handler(CommandHandler("help", partial(help_command, db=db)))
    # application.add_handler(CommandHandler("clear", clear_command)) # Đã xóa đăng ký lệnh /clear

    # Đăng ký trình xử lý callback cho các nút bấm
    application.add_handler(CallbackQueryHandler(partial(button_callback, db=db)))

    # Đăng ký trình xử lý tin nhắn trả lời
    application.add_handler(
        MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND, partial(handle_text_input, db=db)))
    application.add_handler(MessageHandler(filters.REPLY & filters.Document.ALL, partial(handle_file_input, db=db)))

    # Đăng ký các lệnh xác thực (vẫn giữ lại để dùng trực tiếp nếu cần)
    application.add_handler(CommandHandler("verifyChatGPTTeacherK12", partial(verifyChatGPTTeacherK12_command, db=db)))
    application.add_handler(CommandHandler("verifySpotifyStudent", partial(verifySpotifyStudent_command, db=db)))
    application.add_handler(CommandHandler("verifyBoltNewTeacher", partial(verifyBoltNewTeacher_command, db=db)))
    application.add_handler(
        CommandHandler("verifyYouTubePremiumStudent", partial(verifyYouTubePremiumStudent_command, db=db)))
    application.add_handler(CommandHandler("getBoltNewTeacherCode", partial(getBoltNewTeacherCode_command, db=db)))

    # Đăng ký các lệnh admin (vẫn giữ lại để dùng trực tiếp nếu cần)
    application.add_handler(CommandHandler("addbalance", partial(addbalance_command, db=db)))
    application.add_handler(CommandHandler("block", partial(block_command, db=db)))
    application.add_handler(CommandHandler("white", partial(white_command, db=db)))
    application.add_handler(CommandHandler("blacklist", partial(blacklist_command, db=db)))
    application.add_handler(CommandHandler("genkey", partial(genkey_command, db=db)))
    application.add_handler(CommandHandler("listkeys", partial(listkeys_command, db=db)))
    application.add_handler(CommandHandler("broadcast", partial(broadcast_command, db=db)))

    # Đăng ký trình xử lý lỗi
    application.add_error_handler(error_handler)

    logger.info("Bot đang khởi động...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
