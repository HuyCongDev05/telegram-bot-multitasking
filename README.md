# 🤖 Telegram Bot Multitasking - Xác Thực & Công Cụ Tiện Ích

> Giải pháp tự động hóa quy trình xác thực Sinh viên/Giáo viên qua SheerID, hỗ trợ Discord Quest Auto và các công cụ
> Multimedia mạnh mẽ.

---

## 📋 Giới Thiệu Dự Án

Dự án này là một Telegram Bot đa năng được viết bằng Python, tích hợp nhiều dịch vụ từ xác thực danh tính giáo dục đến
các công cụ hỗ trợ người dùng cuối. Bot được thiết kế để hoạt động 24/7 với hiệu suất cao, bảo mật thông tin và giao
diện điều khiển (UI) trực quan.

### ✨ Tính Năng Nổi Bật

- 🚀 **Xác thực SheerID tự động**: Hỗ trợ ChatGPT, Spotify, YouTube, Bolt.new... Hoàn tất tạo thông tin và gửi xác thực
  chỉ với một hành động.
- 🎮 **Discord Quest Auto**: Tự động hoàn thành các Quest trên Discord để nhận thưởng mà không cần thao tác tay.
- 🎬 **Netflix Tool**: Chuyển đổi Netflix Cookie thành URL đăng nhập ứng dụng (App Login) cực nhanh.
- 💳 **Check CC**: Hệ thống kiểm tra thẻ tín dụng an toàn, hỗ trợ lọc và lưu danh sách Live.
- 🛠️ **Quản trị nâng cao**: Hệ thống bảo trì (Maintenance mode) dịch vụ, tìm kiếm người dùng thông minh và gửi thông báo
  toàn hệ thống.
- 💎 **check credit card**: Tích hợp hệ thống điểm thưởng, điểm danh hàng ngày và nạp điểm qua mã Key.
- 🛡️ **Bảo mật tối đa**: Yêu cầu Telegram Username, cơ chế Busy-check (chống trùng lặp tác vụ) và tự dọn dẹp tin nhắn
  nhạy cảm (Tokens/Cookies).

---

## 🎯 Dịch Vụ & Lệnh Điều Khiển

Tất cả các lệnh đã được chuẩn hóa sang định dạng `snake_case` để dễ dàng sử dụng và đồng bộ.

| Lệnh                              | Dịch vụ                 | Phân loại    | Trạng thái |
|:----------------------------------|:------------------------|:-------------|:-----------|
| `/verify_chatgpt_teacher_k12`     | ChatGPT Teacher K12     | Xác thực     | ✅ Ổn định  |
| `/verify_spotify_student`         | Spotify Student         | Xác thực     | ✅ Ổn định  |
| `/verify_youtube_premium_student` | YouTube Premium Student | Xác thực     | ✅ Ổn định  |
| `/verify_bolt_new_teacher`        | Bolt.new Teacher        | Xác thực     | ✅ Ổn định  |
| `/discord_quest_auto`             | Discord Quest Auto      | Công cụ Play | ✅ Mới      |
| `/convert_netflix_url`            | Netflix Cookie to App   | Media        | ✅ Ổn định  |
| `/check_cc`                       | Card Checker            | Tiện ích     | ✅ Ổn định  |
| `/invite`                         | Mời bạn bè              | Hệ thống     | ✅ Ổn định  |
| `/checkin`                        | Điểm danh hàng ngày     | Hệ thống     | ✅ Ổn định  |
| `/balance`                        | Kiểm tra số dư          | Hệ thống     | ✅ Ổn định  |
| `/to_up`                          | Nạp điểm qua Key        | Hệ thống     | ✅ Ổn định  |

---

## ⚖️ Miễn Trừ Trách Nhiệm (Disclaimer)

> [!WARNING]
> **VUI LÒNG ĐỌC KỸ TRƯỚC KHI SỬ DỤNG**
>
> 1. **Mục đích sử dụng**: Dự án này được phát triển hoàn toàn cho mục đích giáo dục, nghiên cứu và học tập nâng cao
     kiến thức về API và tự động hóa. Tác giả không khuyến khích và không ủng hộ bất kỳ hành vi vi phạm điều khoản dịch
     vụ (TOS) của các nền tảng bên thứ ba.
> 2. **Rủi ro tài khoản**: Việc sử dụng các công cụ tự động hóa hoặc xác thực không chính thống có thể dẫn đến việc tài
     khoản của bạn bị tạm khóa, đình chỉ hoặc cấm vĩnh viễn (Banned). Người dùng tự chịu rủi ro này khi quyết định sử
     dụng bot.
> 3. **Trách nhiệm pháp lý**: Tác giả KHÔNG chịu trách nhiệm cho bất kỳ tổn thất, thiệt hại (trực tiếp hoặc gián tiếp),
     hoặc các vấn đề pháp lý phát sinh từ việc sử dụng, sửa đổi hoặc phân phối mã nguồn này. Bạn phải tuân thủ luật pháp
     tại quốc gia/vùng lãnh thổ của mình.
> 4. **Bảo mật dữ liệu**: Bot được thiết kế để không lưu giữ các thông tin nhạy cảm. Tuy nhiên, người vận hành bot (
     Admin) phải có trách nhiệm bảo mật máy chủ và tệp cấu hình `.env` để tránh rò rỉ dữ liệu.
> 5. **Không bảo hành**: Mã nguồn được cung cấp "NGUYÊN TRẠNG" (AS-IS) mà không có bất kỳ sự đảm bảo nào về tính ổn định
     hay tính năng. Tác giả có quyền ngừng cập nhật bất cứ lúc nào.

---

## 🚀 Khởi Động Nhanh

### 1. Yêu cầu hệ thống

- Python 3.11+
- MySQL 5.7+
- Playwright (Chromium)

### 2. Cài đặt & Cấu hình
```bash
git clone https://github.com/HuyCongDev05/telegram-bot-multitasking.git
cd telegram-bot-multitasking
pip install -r requirements.txt
playwright install chromium
```

Sao chép `env.example` thành `.env` và điền:

- `BOT_TOKEN`: Token từ @BotFather.
- `ADMIN_USER_ID`: ID Telegram của bạn (để mở menu Admin).
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`: Thông tin kết nối MySQL.

### 3. Chạy ứng dụng
```bash
python bot.py
```

---

## ⚙️ Hướng dẫn cho Quản trị viên (Admin)

Sau khi xác thực là Admin (thông qua `ADMIN_USER_ID`), bạn sẽ có quyền truy cập menu **"🛠 Quản trị viên"** với các tính
năng:

- 🛠 **Quản lý bảo trì**: Bật/Tắt trạng thái bảo trì cho từng dịch vụ riêng biệt. Khi ở trạng thái bảo trì, người dùng sẽ
  nhận được thông báo và không thể sử dụng dịch vụ đó.
- 🔍 **Tìm người dùng**: Tìm kiếm profile người dùng bằng ID hoặc Username để quản lý số dư hoặc chặn (Block/Blacklist).
- 📣 **Gửi thông báo (Broadcast)**: Gửi tin nhắn định dạng HTML tới toàn bộ người dùng trong hệ thống.
- 🗝 **Hệ thống Key**: Tạo mã nạp tiền tự động với mệnh giá và số lần sử dụng tùy chỉnh.

---

## 📁 Cấu Trúc Thư Mục
```text
├── bot.py                  # Entry point
├── config.py               # Cấu hình & Điểm thưởng
├── database_mysql.py       # Xử lý MySQL (Maintenance, Users, Keys)
├── handlers/               # Xử lý Logic Telegram
│   ├── discord_quest_handlers.py # Discord Quest Logic
│   ├── maintenance_handlers.py   # Admin Maintenance System
│   └── ...
├── discordQuestAuto/       # Core Discord Automation
├── checkCC/                # Card Checking Engine
├── utils/                  # Tiện ích & Messages
└── ...
```

---

## 📜 Giấy Phép & Tín Dụng

Dự án được phát triển dựa trên nền tảng của PastKing. Tác giả hiện tại: **HuyCongDev05**.
Vui lòng tặng một ⭐ nếu bạn thấy dự án hữu ích!
