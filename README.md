# Telegram Multi-Tasking Bot 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Dự án Telegram Bot đa nhiệm mạnh mẽ được xây dựng bằng Python, tích hợp nhiều dịch vụ xác thực, công cụ media và tiện ích hệ thống. Bot được thiết kế để hoạt động ổn định, hiệu suất cao với khả năng xử lý đồng thời (concurrent updates).

## ✨ Tính Năng Chính

### 🛡️ Dịch Vụ Xác Thực (Verification Services)
Hỗ trợ tự động hóa xác thực qua SheerID cho nhiều dịch vụ phổ biến:
- **Spotify Student**: Xác thực gói sinh viên cho Spotify.
- **YouTube Premium Student**: Xác thực gói sinh viên cho YouTube.
- **ChatGPT Teacher (K12)**: Xác thực tài khoản giáo viên ChatGPT dành cho khối K12.
- **Bolt New Teacher**: Xác thực ưu đãi giáo viên mới trên Bolt.
- **Gemini One Pro**: Hỗ trợ các quy trình xác thực nâng cao.

### 🎥 Công Cụ Netflix (Netflix Utilities)
Bộ công cụ chuyên sâu dành cho người dùng Netflix:
- **YouTube/Netflix URL Converter**: Chuyển đổi định dạng URL app/TV.
- **Netflix TV Login**: Hỗ trợ đăng nhập Netflix trên thiết bị TV.
- **Cookie Management**: Tự động lấy, kiểm tra (checker) và lưu trữ cookie Netflix vào kho dữ liệu.
- **Token Generator**: Tạo mã token xác thực cho ứng dụng Netflix.

### 🛠️ Tiện Ích & Công Cụ Khác
- **Check CC**: Công cụ kiểm tra thẻ tín dụng (Credit Card Checker).
- **Discord Quest Auto**: Tự động hóa các nhiệm vụ trên Discord.
- **Hệ Thống Điểm Thưởng (Balance & Rewards)**:
  - Điểm danh hàng ngày (`/checkin`) nhận điểm.
  - Hệ thống mời bạn bè (`/invite`) nhận hoa hồng.
  - Quản lý số dư và nạp điểm qua mã thẻ (Giftcode/Card Key).
- **Proxy Management**: Tự động cập nhật, kiểm tra và xoay vòng proxy từ Webshare.

### 💎 Quản Trị Viên (Admin Dashboard)
Giao diện quản lý nâng cao dành cho chủ sở hữu:
- Quản lý người dùng: Xem thông tin, cộng/trừ điểm, chặn/bỏ chặn người dùng.
- Phát thông báo hàng loạt (Broadcast) tới toàn bộ người dùng.
- Quản lý kho mã thẻ (Card Keys) và kho Cookie.
- Theo dõi trạng thái hệ thống và bảo trì dịch vụ.

## 💻 Công Nghệ Sử Dụng

- **Ngôn ngữ**: [Python 3.10+](https://www.python.org/)
- **Thư viện chính**: `python-telegram-bot` (version 20.x, hỗ trợ PTB20+ với asyncio).
- **Cơ sở dữ liệu**: PostgreSQL (Supabase) với Connection Pool (Supavisor) giúp tối ưu hóa kết nối.
- **Web Server**: Flask (sử dụng cho cơ chế Keep-alive trên các nền tảng như Render).
- **Network**: `httpx`, `requests` cho các yêu cầu API đồng bộ và bất đồng bộ.
- **Docker**: Hỗ trợ containerization với Dockerfile và Docker Compose.

## 📂 Cấu Trúc Dự Án

```text
├── bot.py                # Điểm khởi chạy chương trình (Main Entry)
├── database.py           # Logic tương tác PostgreSQL/Supabase
├── config.py             # Cấu hình biến môi trường và hằng số
├── handlers/             # Chứa toàn bộ các trình xử lý lệnh (Commands)
│   ├── admin_commands.py # Lệnh dành cho quản trị viên
│   ├── user_commands.py  # Lệnh dành cho người dùng phổ thông
│   ├── netflix_handlers.py # Logic xử lý Netflix
│   └── verify_commands.py  # Logic xác thực SheerID
├── netflix/              # Module chuyên biệt cho Netflix (Checker, TV login...)
├── spotify/              # Module xác thực Spotify
├── youtube/              # Module xác thực YouTube
├── utils/                # Các hàm tiện ích (Proxy, i18n, Checks...)
├── k12/                  # Module xác thực giáo viên K12
└── keep_alive.py         # Script duy trì bot hoạt động (Anti-sleep)
```

## ⚖️ Miễn Trừ Trách Nhiệm Pháp Lý (Disclaimer)

Việc sử dụng phần mềm này đồng nghĩa với việc bạn đã đọc và đồng ý với các điều khoản sau:

1. **Mục đích giáo dục**: Dự án này được phát triển chỉ vì mục đích nghiên cứu, học tập và kiểm thử kỹ thuật (Educational/Research Purpose Only).
2. **Trách nhiệm người dùng**: Chúng tôi không chịu bất kỳ trách nhiệm nào về cách thức bạn sử dụng bot này. Bạn hoàn toàn chịu trách nhiệm trước pháp luật về mọi hành vi liên quan đến việc thu thập dữ liệu, xác thực tài khoản hoặc truy cập trái phép.
3. **Quyền sở hữu trí tuệ**: Các dịch vụ bên thứ ba (Netflix, Spotify, YouTube, ChatGPT, SheerID, v.v.) là tài sản của chủ sở hữu tương ứng. Bot này không có mối liên kết chính thức nào với các tập đoàn trên.
4. **Rủi ro tài khoản**: Việc sử dụng các công cụ tự động hóa hoặc script có thể dẫn đến việc tài khoản dịch vụ của bạn bị khóa hoặc đình chỉ theo điều khoản của nhà cung cấp. Chúng tôi không đảm bảo tính an toàn tuyệt đối cho tài khoản của bạn.
5. **Cập nhật nội dung**: Chúng tôi có toàn quyền thay đổi, tạm dừng hoặc gỡ bỏ bất kỳ tính năng nào của dự án mà không cần thông báo trước.

---
*Dự án gốc bởi **PastKing**. Được nâng cấp, bảo trì và phát triển thêm các tính năng mới bởi [HuyCongDev05](https://github.com/HuyCongDev05)*
