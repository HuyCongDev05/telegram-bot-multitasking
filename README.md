# Telegram Multi-Tasking Bot 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

Một giải pháp Telegram Bot đa nhiệm mạnh mẽ, ổn định và bảo mật. Dự án được thiết kế để cung cấp các dịch vụ tự động hóa, xác thực và tiện ích giải trí với hiệu suất cao nhất thông qua cơ chế xử lý bất đồng bộ (asyncio).

## ✨ Tính Năng Nổi Bật

### 🌐 Hệ Thống Đa Ngôn Ngữ (Multi-language)
- Hỗ trợ hoàn hảo hai ngôn ngữ: **Tiếng Việt 🇻🇳** và **Tiếng Anh 🇬🇧**.
- Tự động nhận diện và lưu trữ ngôn ngữ theo từng người dùng.
- Giao diện thân thiện, nút bấm thông minh thay thế hoàn toàn cho các lệnh gõ tay phức tạp.

### 🎬 Công Cụ Netflix Chuyên Sâu
- **Netflix App Login**: Chuyển đổi cookie thành link đăng nhập ứng dụng tự động.
- **Cơ chế Retry thông minh**: Tự động thử lại tối đa 10 lần với các proxy và cookie khác nhau khi gặp lỗi kết nối hoặc bị chặn, đảm bảo tỷ lệ thành công cao nhất.
- **Netflix TV Login**: Hỗ trợ kích hoạt đăng nhập trên Smart TV qua mã code.
- **Netflix Checker**: Kiểm tra tình trạng hoạt động (Live/Die) của cookie với khả năng xoay vòng proxy tự động.

### 🛡️ Dịch Vụ Xác Thực Tự Động (Auto-Verify)
Tích hợp quy trình xác thực SheerID tự động cho các nền tảng lớn:
- **Spotify & YouTube Student**: Xác thực gói ưu đãi sinh viên.
- **ChatGPT & Bolt Teacher**: Xác thực dành cho giáo viên và khối K12.
- **Gemini One Pro**: Hỗ trợ các quy trình xác thực nâng cao.

### 🎮 Discord & Tiện Ích Media
- **Discord Quest Auto**: Tự động hoàn thành các nhiệm vụ Discord Quest, nhận phần thưởng nhanh chóng.
- **Image Generator**: Tạo ảnh xác thực sinh viên/giáo viên chuyên nghiệp phục vụ kiểm thử.

### 💰 Hệ Thống Kinh Tế & Thành Viên
- **Check-in**: Điểm danh nhận thưởng hàng ngày.
- **Referral System**: Mời bạn bè qua link giới thiệu thông minh (Nhấn là tự động sao chép) để nhận điểm hoa hồng.
- **Giftcode**: Nạp điểm vào tài khoản qua hệ thống mã Key được quản lý chặt chẽ.

### 🛠️ Quản Trị Viên (Admin Tools)
- Bảng điều khiển quản trị toàn diện: Quản lý người dùng, cộng điểm, chặn/mở khóa tài khoản.
- Hệ thống gửi thông báo (Broadcast) nhanh chóng tới toàn bộ thành viên.
- Quản lý kho Cookie và Key tự động.
- Chế độ bảo trì (Maintenance mode) linh hoạt cho từng dịch vụ riêng lẻ.

## 💻 Công Nghệ Sử Dụng

- **Backend**: Python 3.10+ (Asyncio, python-telegram-bot 20.x).
- **Database**: PostgreSQL (Supabase) với Supavisor Connection Pool cho hiệu năng tối ưu.
- **Infrastructure**: Flask (Keep-alive), httpx, requests.
- **Automation**: Playwright (Image Generation), Webshare Proxy API integration.

## ⚖️ Miễn Trừ Trách Nhiệm (Disclaimer)

Việc sử dụng mã nguồn này đồng nghĩa với việc bạn đã đọc và đồng ý với các điều khoản sau:

1. **Mục đích giáo dục**: Dự án này được phát triển chỉ vì mục đích nghiên cứu, học tập và kiểm thử kỹ thuật. Chúng tôi khuyến khích việc tìm hiểu về kiến trúc hệ thống và lập trình bất đồng bộ.
2. **Trách nhiệm người dùng**: Chúng tôi **KHÔNG** chịu bất kỳ trách nhiệm nào về cách thức bạn sử dụng bot này. Người dùng hoàn toàn chịu trách nhiệm trước pháp luật về mọi hành vi liên quan đến việc xác thực tài khoản hoặc truy cập các dịch vụ bên thứ ba.
3. **Quyền sở hữu trí tuệ**: Các thương hiệu và dịch vụ như Netflix, Spotify, YouTube, ChatGPT, SheerID... thuộc quyền sở hữu của các tập đoàn tương ứng. Bot này không có mối liên kết chính thức nào với các đơn vị trên.
4. **Tính ổn định**: Chúng tôi không đảm bảo tính an toàn tuyệt đối cho tài khoản dịch vụ của bạn khi sử dụng các công cụ tự động. Mọi rủi ro về việc khóa tài khoản là trách nhiệm của người dùng.
5. **Dữ liệu**: Dự án tập trung vào tính năng và trải nghiệm người dùng, không tích hợp các cơ chế thu thập dữ liệu cá nhân trái phép.

---
*Dự án gốc bởi **PastKing**. Được nâng cấp, tái cấu trúc và phát triển thêm các tính năng mới bởi [HuyCongDev05](https://github.com/HuyCongDev05)*
