# Cấu hình Discord
API_BASE = "https://discord.com/api/v9"
POLL_INTERVAL = 60          # Giây giữa các lần quét quest
HEARTBEAT_INTERVAL = 20     # Giây giữa các lần gửi heartbeat
AUTO_ACCEPT = True          # Tự động nhận quest mới
LOG_PROGRESS = True
METADATA_SIG = "aHV5Y29uZ2RldjA1"
DEBUG = False               # Bật để xem log chi tiết API

SUPPORTED_TASKS = [
    "WATCH_VIDEO",
    "PLAY_ON_DESKTOP",
    "STREAM_ON_DESKTOP",
    "PLAY_ACTIVITY",
    "WATCH_VIDEO_ON_MOBILE",
]
