# 🤖 Telegram Bot Xác Thực SheerID & Công Cụ Tiện Ích

> Bot Telegram tự động hóa quy trình xác thực Sinh viên/Giáo viên qua SheerID và cung cấp các công cụ tiện ích khác.

---

## 📋 Giới Thiệu Dự Án

Dự án này là một Telegram Bot mạnh mẽ được viết bằng Python, được thiết kế để tự động hóa quy trình xác nhận danh tính Sinh viên/Giáo viên trên nền tảng SheerID cho nhiều dịch vụ khác nhau. Bot tự động tạo thông tin định danh, xây dựng tài liệu xác thực và gửi trực tiếp lên hệ thống SheerID, giúp đơn giản hóa quy trình xác minh.

Ngoài ra, bot còn tích hợp các tính năng quản lý người dùng, hệ thống điểm thưởng và một công cụ chuyển đổi cookie Netflix thành URL đăng nhập ứng dụng tiện lợi.

### ✨ Tính Năng Nổi Bật

-   🚀 **Xác thực SheerID tự động**: Hoàn tất tạo thông tin, tạo tài liệu và gửi xác thực chỉ với một lệnh cho các dịch vụ hỗ trợ.
-   🎨 **Tạo ảnh thông minh**: Tự động tạo ảnh thẻ Sinh viên/Giáo viên định dạng PNG cực kỳ chân thực.
-   📺 **Chuyển đổi Netflix Cookie**: Biến cookie Netflix thành URL đăng nhập ứng dụng tiện lợi.
-   💰 **Hệ thống điểm thưởng (Points)**: Tích hợp các tính năng điểm danh (check-in), mời bạn bè (invite) và đổi mã nạp tiền (key).
-   🔐 **An toàn & Tin cậy**: Sử dụng cơ sở dữ liệu MySQL và hỗ trợ cấu hình qua biến môi trường (.env).
-   ⚡ **Kiểm soát đồng thời**: Quản lý thông minh các yêu cầu đồng thời (Concurrency) để đảm bảo hệ thống ổn định.
-   👥 **Quản trị toàn diện**: Hệ thống quản lý người dùng và điểm thưởng mạnh mẽ cho Admin.

---

## 🎯 Các Dịch Vụ Xác Thực Được Hỗ Trợ

Bot hỗ trợ xác thực cho các dịch vụ sau thông qua SheerID:

| Lệnh/Chức năng                 | Dịch vụ                 | Loại xác thực | Trạng thái |
| :----------------------------- | :---------------------- | :------------ | :--------- |
| `/verifyChatGPTTeacherK12`     | ChatGPT Teacher K12     | Giáo viên     | ✅ Hoàn tất |
| `/verifySpotifyStudent`        | Spotify Student         | Sinh viên     | ✅ Hoàn tất |
| `/verifyBoltNewTeacher`        | Bolt.new Teacher        | Giáo viên     | ✅ Hoàn tất |
| `/verifyYouTubePremiumStudent` | YouTube Premium Student | Sinh viên     | ✅ Hoàn tất |
| `Chuyển đổi Netflix URL`       | Netflix                 | Công cụ       | ✅ Hoàn tất |

> **⚠️ Lưu ý trước khi dùng**: Các `programId` của từng module xác thực SheerID có thể thay đổi định kỳ. Nếu xác thực thất bại liên tục, hãy kiểm tra và cập nhật tệp `config.py` tương ứng (xem phần "Hướng dẫn cấu hình" bên dưới).

---

## 🛠️ Công Nghệ Sử Dụng

-   **Ngôn ngữ**: Python 3.11+
-   **Framework Bot**: `python-telegram-bot`
-   **Cơ sở dữ liệu**: MySQL 5.7+
-   **Tự động hóa trình duyệt**: `Playwright` (dùng để render ảnh từ HTML)
-   **HTTP Client**: `httpx`, `requests`
-   **Xử lý ảnh/tài liệu**: `Pillow`, `reportlab`, `xhtml2pdf`
-   **Quản lý môi trường**: `python-dotenv`

---

## 🚀 Khởi Động Nhanh

### 1. Sao chép dự án (Clone)

```bash
git clone https://github.com/your-username/telegram-bot-verify.git # Thay bằng URL repo của bạn
cd telegram-bot-verify
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Cấu hình biến môi trường

Sao chép tệp `env.example` thành `.env` và điền các thông tin cần thiết:

```env
BOT_TOKEN=your_bot_token_here
CHANNEL_USERNAME=your_channel_username # Tùy chọn
CHANNEL_URL=https://t.me/your_channel # Tùy chọn
ADMIN_USER_ID=your_admin_id # ID Telegram của bạn

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=tgbot_verify
```

### 4. Chạy Bot

```bash
python bot.py
```

---

## 🐳 Triển Khai Với Docker

Để triển khai bot bằng Docker, bạn có thể sử dụng `docker-compose` hoặc xây dựng image thủ công.

1.  **Cấu hình `.env`**: Đảm bảo bạn đã sao chép `env.example` thành `.env` và điền đầy đủ thông tin như hướng dẫn ở trên.

2.  **Sử dụng Docker Compose**:

    ```bash
    docker-compose up -d
    # Xem logs
    docker-compose logs -f
    ```

3.  **Xây dựng và chạy thủ công**:

    ```bash
    docker build -t tgbot-verify .
    docker run -d --name tgbot-verify --env-file .env -v $(pwd)/logs:/app/logs tgbot-verify
    ```

---

## 📖 Hướng Dẫn Sử Dụng

### Lệnh Cho Người Dùng

Các lệnh này có thể được truy cập thông qua các nút bấm trong bot hoặc gõ trực tiếp:

```text
/start              # Bắt đầu sử dụng bot và đăng ký tài khoản
/help               # Hiển thị hướng dẫn và các lệnh có sẵn
/balance            # Kiểm tra số dư điểm hiện tại của bạn
/invite             # Tạo link mời bạn bè để nhận điểm thưởng
/checkin            # Điểm danh hàng ngày để nhận điểm thưởng
/to_up              # Sử dụng mã nạp tiền để đổi lấy điểm

# Các lệnh xác thực SheerID (yêu cầu link xác thực)
/verifyChatGPTTeacherK12 <link>     # Xác thực ChatGPT Teacher K12
/verifySpotifyStudent <link>        # Xác thực Spotify Student
/verifyBoltNewTeacher <link>        # Xác thực Bolt.new Teacher
/verifyYouTubePremiumStudent <link> # Xác thực YouTube Premium Student
/getBoltNewTeacherCode              # Lấy mã xác thực Bolt.new (nếu không tự động lấy được)

# Công cụ tiện ích
/convert_url_login_app_netflix      # Chuyển đổi cookie Netflix thành URL đăng nhập ứng dụng
```

### Lệnh Cho Quản Trị Viên

Chỉ dành cho `ADMIN_USER_ID` đã cấu hình:

```text
/addbalance <user_id> <số_điểm>           # Cộng/trừ điểm cho người dùng (số âm để trừ)
/block <user_id>                         # Chặn người dùng khỏi việc sử dụng bot
/white <user_id>                         # Bỏ chặn người dùng
/blacklist                               # Xem danh sách các người dùng bị chặn
/genkey <mã> <điểm> [lượt] [ngày]         # Tạo mã nạp tiền tự động (lượt và ngày là tùy chọn)
/listkeys                                # Xem danh sách các mã nạp tiền hiện có
/broadcast <nội_dung>                    # Gửi thông báo đến toàn bộ người dùng bot
```

### Quy Trình Xác Thực SheerID

1.  Truy cập trang xác thực của dịch vụ bạn muốn (ví dụ: Spotify Student), bắt đầu quy trình xác minh.
2.  Sao chép toàn bộ đường dẫn URL trên thanh địa chỉ trình duyệt (phải chứa tham số `verificationId`).
3.  Gửi lệnh kèm link cho bot, ví dụ: `/verifySpotifyStudent https://services.sheerid.com/verify/xxx/?verificationId=yyy`
4.  Chờ bot xử lý tự động. Quy trình duyệt tài liệu thường mất vài phút.

### Quy Trình Chuyển Đổi Netflix URL

1.  Chọn chức năng "Chuyển đổi Netflix URL" từ menu bot.
2.  Bot sẽ yêu cầu bạn nhập cookie Netflix hoặc gửi một tệp `.txt` chứa cookie.
3.  Gửi cookie của bạn (đảm bảo định dạng chính xác).
4.  Bot sẽ xử lý và trả về một URL đăng nhập ứng dụng Netflix.

---

## 💡 Hướng Dẫn Lấy Link Xác Thực và Cookie

Để sử dụng các chức năng xác thực SheerID và công cụ chuyển đổi Netflix URL, bạn cần cung cấp cho bot các thông tin đầu vào chính xác. Dưới đây là hướng dẫn chi tiết cách lấy chúng.

### 1. Lấy Link Xác Thực SheerID (cho Spotify, YouTube, ChatGPT, Bolt.new)

Nguyên tắc chung là bạn phải bắt đầu quá trình xác thực trên trang web chính thức của dịch vụ, sau đó lấy link khi bạn được chuyển hướng đến trang của SheerID.

**Link SheerID hợp lệ thường có dạng:**
`https://services.sheerid.com/verify/...` hoặc `https://my.sheerid.com/verify/...`
Và quan trọng nhất, nó phải chứa một mã định danh duy nhất như `verificationId` hoặc `externalUserId` trong URL.

#### a) Spotify Student (Xác thực Sinh viên)

1.  **Truy cập trang Spotify Premium for Students:**
    *   Vào Google và tìm kiếm "Spotify Premium for Students" hoặc truy cập: `https://www.spotify.com/vn-vi/student/`
    *   Nhấn vào nút "Get Started" hoặc "Bắt đầu".
2.  **Đăng nhập tài khoản Spotify:** Đăng nhập vào tài khoản Spotify của bạn.
3.  **Bắt đầu quá trình xác thực:**
    *   Spotify sẽ yêu cầu bạn điền thông tin về trường học (tên, ngày sinh, tên trường đại học).
    *   Nhấn "Next" hoặc "Verify".
4.  **Lấy link từ trang SheerID:**
    *   Spotify sẽ **chuyển hướng bạn sang một trang mới có địa chỉ của SheerID**. Trang này sẽ yêu cầu bạn cung cấp tài liệu chứng minh.
    *   **Tại thời điểm này, hãy sao chép TOÀN BỘ URL trên thanh địa chỉ của trình duyệt.**
    *   Ví dụ URL: `https://services.sheerid.com/verify/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/?token=...&verificationId=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy`
    *   **Gửi toàn bộ link này cho bot.**

#### b) YouTube Premium Student (Xác thực Sinh viên)

1.  **Truy cập trang YouTube Premium for Students:**
    *   Tìm kiếm "YouTube Premium Student" hoặc truy cập: `https://www.youtube.com/premium/student`
    *   Nhấn vào "Try it Free" hoặc "Thử miễn phí".
2.  **Đăng nhập tài khoản Google:** Đăng nhập vào tài khoản Google/YouTube của bạn.
3.  **Bắt đầu xác thực với SheerID:**
    *   YouTube sẽ thông báo hợp tác với SheerID. Nhấn "Continue" hoặc "Tiếp tục".
    *   Bạn sẽ được yêu cầu điền tên trường học của mình.
4.  **Lấy link từ trang SheerID:**
    *   Sau khi điền thông tin, bạn sẽ được chuyển hướng đến trang của SheerID để tải lên tài liệu.
    *   **Sao chép TOÀN BỘ URL trên thanh địa chỉ trình duyệt tại thời điểm này.**
    *   **Gửi toàn bộ link này cho bot.**

#### c) ChatGPT Teacher K12 & Bolt.new Teacher (Xác thực Giáo viên)

1.  **Tìm trang xác thực của dịch vụ:**
    *   **ChatGPT:** Tìm kiếm "OpenAI for Educators" hoặc các trang hướng dẫn đăng ký tài khoản giáo dục của OpenAI.
    *   **Bolt.new:** Truy cập trang chủ của Bolt (`https://www.bolt.com/`) và tìm chương trình dành cho giáo viên (Teacher Program).
2.  **Bắt đầu quy trình xác thực:**
    *   Trên trang của dịch vụ, tìm nút "Verify as a Teacher", "Get Verified", hoặc tương tự.
    *   Bạn sẽ được yêu cầu điền thông tin cá nhân và thông tin trường học.
3.  **Lấy link từ trang SheerID:**
    *   Sau khi điền thông tin, bạn sẽ được chuyển hướng đến trang của SheerID.
    *   **Sao chép TOÀN BỘ URL trên thanh địa chỉ trình duyệt.**
    *   **Gửi toàn bộ link này cho bot.**

### 2. Lấy Cookie Netflix (cho chức năng chuyển đổi URL đăng nhập)

Việc lấy cookie yêu cầu thao tác trên trình duyệt máy tính.

1.  **Đăng nhập vào Netflix:**
    *   Trên trình duyệt Chrome, Firefox, hoặc Edge, truy cập `https://www.netflix.com/` và đăng nhập vào tài khoản của bạn.
2.  **Mở Công cụ phát triển (Developer Tools):**
    *   Nhấn phím `F12` trên bàn phím.
    *   Hoặc, click chuột phải vào bất kỳ đâu trên trang và chọn "Inspect" hoặc "Kiểm tra".
3.  **Tìm Cookie:**
    *   Trong cửa sổ Developer Tools, chọn tab **"Network"**.
    *   Tải lại trang Netflix (nhấn `F5`).
    *   Click vào một yêu cầu bất kỳ trong danh sách (thường là yêu cầu đầu tiên có tên `browse` hoặc `MainDocument`).
    *   Trong cửa sổ bên phải, tìm đến phần **"Request Headers"**.
    *   Tìm dòng có tên **`cookie:`**.
4.  **Sao chép Cookie:**
    *   **Click chuột phải vào TOÀN BỘ giá trị của dòng `cookie:` và chọn "Copy value".**
    *   Giá trị bạn copy sẽ là một chuỗi văn bản rất dài, chứa tất cả các cookie, ví dụ: `NetflixId=...; SecureNetflixId=...; ...`
5.  **Gửi cho bot:**
    *   Dán chuỗi cookie vừa copy vào một file `.txt` rồi gửi cho bot.
    *   Hoặc, dán trực tiếp vào ô chat của bot khi được yêu cầu.

---

## 📁 Cấu Trúc Dự Án

```text
telegram-bot-verify/
├── bot.py                  # Chương trình chính của bot
├── config.py               # Cấu hình toàn cục và hằng số
├── database_mysql.py       # Lớp quản lý tương tác với cơ sở dữ liệu MySQL
├── env.example             # Mẫu tệp biến môi trường
├── requirements.txt        # Danh sách các thư viện Python cần thiết
├── Dockerfile              # Cấu hình Docker để đóng gói ứng dụng
├── docker-compose.yml      # Cấu hình Docker Compose để triển khai dễ dàng
├── handlers/               # Chứa các module xử lý lệnh và callback của bot
│   ├── user_commands.py    # Xử lý các lệnh và tương tác của người dùng
│   ├── admin_commands.py   # Xử lý các lệnh quản trị viên
│   └── verify_commands.py  # Xử lý các lệnh xác thực SheerID
├── k12/                    # Module và cấu hình cho xác thực ChatGPT K12
├── spotify/                # Module và cấu hình cho xác thực Spotify Student
├── youtube/                # Module và cấu hình cho xác thực YouTube Premium Student
├── Boltnew/                # Module và cấu hình cho xác thực Bolt.new Teacher
├── nftokenNetflix/         # Module cho công cụ chuyển đổi Netflix URL
│   └── nf_token_generator.py # Logic tạo NFT token từ cookie
└── utils/                  # Các hàm và tiện ích hỗ trợ
    ├── messages.py         # Chứa các mẫu tin nhắn và bàn phím bot
    ├── concurrency.py      # Cơ chế kiểm soát đồng thời
    └── checks.py           # Các hàm kiểm tra quyền hạn và trạng thái
```

---

## ⚙️ Hướng Dẫn Cấu Hình Chi Tiết

### Chi Tiết Biến Môi Trường

| Tên biến           | Bắt buộc | Mô tả                                    |
| :----------------- | :------- | :--------------------------------------- |
| `BOT_TOKEN`        | ✅        | Token của Telegram Bot lấy từ @BotFather |
| `ADMIN_USER_ID`    | ✅        | ID Telegram của người quản trị           |
| `MYSQL_HOST`       | ✅        | Địa chỉ máy chủ MySQL                    |
| `MYSQL_USER`       | ✅        | Tên đăng nhập MySQL                      |
| `MYSQL_PASSWORD`   | ✅        | Mật khẩu MySQL                           |
| `MYSQL_DATABASE`   | ✅        | Tên cơ sở dữ liệu                        |
| `CHANNEL_USERNAME` | ❌        | Tên kênh Telegram (ví dụ: `my_channel`)  |
| `CHANNEL_URL`      | ❌        | Đường dẫn kênh Telegram                  |
| `MYSQL_PORT`       | ❌        | Cổng MySQL (Mặc định: `3306`)            |

### Cập Nhật `programId` (Cho xác thực SheerID)

Nếu xác thực SheerID thất bại liên tục, nguyên nhân thường là do `programId` đã hết hạn hoặc thay đổi. Cách cập nhật:

1.  Truy cập trang xác thực dịch vụ bạn muốn, mở công cụ phát triển của trình duyệt (F12) và chuyển sang tab `Network`.
2.  Bắt đầu quy trình xác thực trên trang web.
3.  Tìm kiếm các yêu cầu (request) có dạng: `https://services.sheerid.com/rest/v2/verification/`
4.  Trong phần `Payload` hoặc `URL` của yêu cầu đó, tìm giá trị `programId`.
5.  Cập nhật giá trị `programId` này vào tệp `config.py` của module tương ứng trong thư mục `k12/`, `spotify/`, `youtube/`, hoặc `Boltnew/`.

### Cấu Hình Điểm Thưởng (`config.py`)

Bạn có thể tùy chỉnh các giá trị điểm thưởng và chi phí xác thực trong tệp `config.py` ở thư mục gốc của dự án:

```python
VERIFY_COST = 1  # Điểm tiêu tốn cho mỗi lần xác thực SheerID hoặc sử dụng công cụ Netflix
CHECKIN_REWARD = 1  # Điểm thưởng khi người dùng điểm danh hàng ngày
INVITE_REWARD = 2  # Điểm thưởng khi người dùng mời thành công một người bạn mới
REGISTER_REWARD = 1  # Điểm thưởng khi người dùng đăng ký tài khoản mới lần đầu
```

---

## 🛠️ Phát Triển Thêm (Secondary Development)

Hoan nghênh các bạn phát triển thêm dựa trên dự án này. Vui lòng tuân thủ các nguyên tắc sau:

-   Tuân thủ giấy phép MIT — các dự án phát sinh cũng nên là mã nguồn mở.
-   Sử dụng cá nhân miễn phí; sử dụng thương mại vui lòng tự chịu trách nhiệm về tối ưu hóa và pháp lý.

---

## 📜 Nguồn 

Dự án này được phát hành dựa trên dự án của PastKing

---

<p align="center">
  <strong>⭐ Nếu dự án này có ích cho bạn, hãy tặng một Star nhé!</strong>
</p>
