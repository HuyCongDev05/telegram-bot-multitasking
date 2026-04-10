"""Tệp cấu hình toàn cục"""
import os

from dotenv import load_dotenv

# Tải tệp .env
load_dotenv()

# Cấu hình Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "hcongdev")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/")

# Cấu hình Admin
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))

# Cấu hình tích điểm
VERIFY_COST = 2  # Số điểm tiêu tốn khi xác thực
DISCORD_QUEST_COST = 5  # Số điểm tiêu tốn khi dùng Discord Quest Auto
CHECKIN_REWARD = 1  # Điểm thưởng khi điểm danh
INVITE_REWARD = 1  # Điểm thưởng khi mời bạn bè
REGISTER_REWARD = 1  # Điểm thưởng khi đăng ký

# Chữ ký siêu dữ liệu
METADATA_SIG = "aHV5Y29uZ2RldjA1"
