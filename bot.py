"""Chương trình chính của Telegram Bot"""
import asyncio
import logging
from functools import partial

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN

_BUILD_SIG = "687579636f6e676465763035"
from database import Database
from keep_alive import keep_alive
from handlers.cc_handlers import checkCC_command
from handlers.user_commands import (
    start_command,
    help_command,
    button_callback,
    handle_text_input,
    handle_file_input,
    convertNetflixUrl_command,
    get_cookie_netflix_command,
    invite_command,
    checkin_command,
    balance_command,
    to_up_command,
    check_cookie_netflix_command,
)
from handlers.verify_commands import (
    verifyChatGPTTeacherK12_command,
    verifySpotifyStudent_command,
    verifyBoltNewTeacher_command,
    verifyYouTubePremiumStudent_command,
    getBoltNewTeacherCode_command,
    verifyGeminiOnePro_command,
)

# Cấu hình logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_BUILD_SIGN_ID = "687579636f6e676465763035"


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lỗi toàn cục"""
    logger.error("Exception while handling an update:", exc_info=context.error)


def main():
    """Hàm chính"""
    # Khởi tạo cơ sở dữ liệu
    db = Database()

    # Khởi động Web Server Keep-Alive
    keep_alive()

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
    application.add_handler(
        CommandHandler("verify_chatgpt_teacher_k12", partial(verifyChatGPTTeacherK12_command, db=db)))
    application.add_handler(CommandHandler("verify_spotify_student", partial(verifySpotifyStudent_command, db=db)))
    application.add_handler(CommandHandler("verify_bolt_new_teacher", partial(verifyBoltNewTeacher_command, db=db)))
    application.add_handler(
        CommandHandler("verify_youtube_premium_student", partial(verifyYouTubePremiumStudent_command, db=db)))
    application.add_handler(CommandHandler("getBoltNewTeacherCode", partial(getBoltNewTeacherCode_command, db=db)))
    application.add_handler(CommandHandler("verify_gemini_one_pro", partial(verifyGeminiOnePro_command, db=db)))

    # Đăng ký các lệnh tiện ích khác
    application.add_handler(CommandHandler("invite", partial(invite_command, db=db)))
    application.add_handler(CommandHandler("checkin", partial(checkin_command, db=db)))
    application.add_handler(CommandHandler("balance", partial(balance_command, db=db)))
    application.add_handler(CommandHandler("toUp", partial(to_up_command, db=db)))

    # Đăng ký lệnh Check CC
    application.add_handler(CommandHandler("check_cc", partial(checkCC_command, db=db)))

    # Đăng ký lệnh Chuyển đổi Netflix URL
    application.add_handler(CommandHandler("convert_netflix_url", partial(convertNetflixUrl_command, db=db)))
    application.add_handler(CommandHandler("login_app_netflix", partial(convertNetflixUrl_command, db=db)))
    application.add_handler(CommandHandler("get_cookie_netflix", partial(get_cookie_netflix_command, db=db)))

    # Đăng ký lệnh Check Netflix Cookie
    application.add_handler(CommandHandler("check_cookie_netflix", partial(check_cookie_netflix_command, db=db)))

    # Đăng ký lệnh Đăng nhập Netflix TV
    from handlers.netflix_handlers import login_tv_netflix_command
    application.add_handler(CommandHandler("login_tv_netflix", partial(login_tv_netflix_command, db=db)))

    # Đăng ký trình xử lý lỗi
    application.add_error_handler(error_handler)

    async def post_init(app: Application):
        """Các công việc cần khởi động sau khi bot sẵn sàng."""
        from handlers.jobs import start_proxy_management_loop
        # Chạy vòng lặp quản lý proxy (Cập nhật + Dọn dẹp) trong task asyncio riêng biệt
        asyncio.create_task(start_proxy_management_loop(app, db, interval=900))
        logger.info("🕒 Background Task: Đã kích hoạt vòng lặp quản lý proxy (Webshare Update + Cleanup - 15 phút/lần).")

        # Cơ chế Self-ping để chống ngủ trên Render
        async def self_ping():
            import httpx
            import os
            port = os.environ.get('PORT', '8080')
            url = f"http://localhost:{port}/health"
            # Đợi một chút cho server Flask khởi động hẳn
            await asyncio.sleep(10)
            while True:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url)
                        logger.info(f"❤️ Self-ping status: {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ Self-ping failed: {e}")
                # Ping mỗi 10 phút (600 giây)
                await asyncio.sleep(600)

        asyncio.create_task(self_ping())
        logger.info("🚀 Background Task: Đã kích hoạt Self-ping để chống ngủ trên Render.")

    application.post_init = post_init

    logger.info("Bot đang khởi động...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
