# 🤖 Telegram Bot Xác Thực SheerID & Công Cụ Tiện Ích

> Bot Telegram tự động hóa quy trình xác thực Sinh viên/Giáo viên qua SheerID và cung cấp các công cụ tiện ích khác.

---

## 📋 Giới Thiệu Dự Án

Dự án này là một Telegram Bot mạnh mẽ được viết bằng Python, được thiết kế để tự động hóa quy trình xác nhận danh tính Sinh viên/Giáo viên trên nền tảng SheerID cho nhiều dịch vụ khác nhau. Bot tự động tạo thông tin định danh, xây dựng tài liệu xác thực và gửi trực tiếp lên hệ thống SheerID, giúp đơn giản hóa quy trình xác minh.

Ngoài ra, bot còn tích hợp các tính năng quản lý người dùng, hệ thống điểm thưởng và một công cụ chuyển đổi cookie Netflix thành URL đăng nhập ứng dụng tiện lợi.

### ✨ Tính Năng Nổi Bật

- 🚀 **Xác thực SheerID tự động**: Hoàn tất tạo thông tin, tạo hồ sơ và gửi xác thực chỉ với một lệnh.
- 🎨 **Tạo hồ sơ thông minh**: Tự động render ảnh thẻ Sinh viên/Giáo viên định dạng PNG chuyên nghiệp.
- 🎬 **Chuyển đổi Netflix Cookie**: Biến cookie Netflix thành link đăng nhập ứng dụng cực nhanh.
- 🃏 **Check CC Quick**: Hỗ trợ kiểm tra hàng loạt thẻ tín dụng với tốc độ và độ chính xác cao.
- 💎 **Hệ thống điểm thưởng**: Tích hợp điểm danh hằng ngày, mời bạn bè và nạp thẻ (key).
- 🛡️ **Bảo mật Username**: Bắt buộc người dùng phải có Telegram Username để định danh và chống spam.
- ⚡ **Chống Spam & Dọn dẹp**: Tự động dọn dẹp tin nhắn rác và ngăn chặn hành động trùng lặp (Busy Check).
- 🛠️ **Quản trị nâng cao**: Tìm kiếm người dùng bằng Username/ID và quản lý "một chạm" cho Admin.

---

## 🎯 Các Dịch Vụ Xác Thực Được Hỗ Trợ

Bot hỗ trợ xác thực cho các dịch vụ sau thông qua SheerID:

| Lệnh/Chức năng                    | Dịch vụ                 | Loại xác thực | Trạng thái          |
|:----------------------------------|:------------------------|:--------------|:--------------------|
| `/verify_chatgpt_teacher_k12`     | ChatGPT Teacher K12     | Giáo viên     | ✅ Hoàn tất          |
| `/verify_spotify_student`         | Spotify Student         | Sinh viên     | ✅ Hoàn tất          |
| `/verify_bolt_new_teacher`        | Bolt.new Teacher        | Giáo viên     | ✅ Hoàn tất          |
| `/verify_youtube_premium_student` | YouTube Premium Student | Sinh viên     | ✅ Hoàn tất          |
| `/verify_gemini_one_pro`          | Gemini One Pro          | Công cụ       | 🛠️ Đang phát triển |
| `/convert_netflix_url`            | Netflix                 | Công cụ       | ✅ Hoàn tất          |
| `/check_cc`                       | Credit Card             | Công cụ       | ✅ Hoàn tất          |

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
git clone git clone https://github.com/HuyCongDev05/telegram-bot-multitasking.git
cd telegram-bot-multitasking
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
MYSQL_DATABASE=telegram-bot-multitasking
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
    docker build -t telegram-bot-multitasking .
    docker run -d --name telegram-bot-multitasking --env-file .env -v $(pwd)/logs:/app/logs telegram-bot-multitasking
    ```

---

## 📖 Hướng Dẫn Sử Dụng

Các lệnh này có thể được truy cập thông qua Menu nút bấm hoặc gõ trực tiếp (Slash commands):

**Lệnh cơ bản:**

- `/start` - Bắt đầu và đăng ký tài khoản (Yêu cầu phải có Username).
- `/help` - Xem hướng dẫn sử dụng chi tiết.
- `/balance` - Kiểm tra số dư điểm hiện tại.
- `/invite` - Lấy link mời bạn bè.
- `/checkin` - Điểm danh hằng ngày.
- `/to_up` - Nạp điểm bằng thẻ Key.

**Dịch vụ xác thực SheerID (Auto Verify):**

- `/verify_chatgpt_teacher_k12` - Xác thực ChatGPT Giáo viên.
- `/verify_spotify_student` - Xác thực Spotify Sinh viên.
- `/verify_bolt_new_teacher` - Xác thực Bolt.new Giáo viên.
- `/verify_youtube_premium_student` - Xác thực YouTube Premium.
- `/verify_gemini_one_pro` - Xác thực Gemini Pro (Đang phát triển).

**Công cụ tiện ích:**

- `/convert_netflix_url` - Chuyển đổi Cookie Netflix sang Link App.
- `/check_cc` - Kiểm tra thẻ tín dụng nhanh.

Để đảm bảo an toàn, các lệnh quản trị đã được gỡ bỏ khỏi lệnh slash công khai. Admin chỉ có thể thao tác thông qua nút
bấm **"🛠 Quản trị viên"** sau khi xác thực danh tính bởi BOT.

**Các tính năng nổi bật cho Admin:**

- 🔍 **Tìm người dùng**: Tìm kiếm profile chi tiết bằng `@username` hoặc `ID`.
- 💰 **Cộng tiền nhanh**: Các nút bấm cộng nhanh 10, 50, 100 điểm cho người dùng.
- 🔒 **Quản lý trạng thái**: Khóa (Block) hoặc Mở khóa người dùng chỉ với 1 chạm.
- 🗝 **Hệ thống Key**: Tạo và quản lý mã nạp điểm tự động.
- 📣 **Broadcast**: Gửi thông báo toàn hệ thống kèm định dạng HTML.

### Quy Trình Xác Thực SheerID

1.  Truy cập trang xác thực của dịch vụ bạn muốn (ví dụ: Spotify Student), bắt đầu quy trình xác minh.
2.  Sao chép toàn bộ đường dẫn URL trên thanh địa chỉ trình duyệt (phải chứa tham số `verificationId`).
3. Gửi lệnh kèm link cho bot, ví dụ:
   `/verify_spotify_student https://services.sheerid.com/verify/xxx/?verificationId=yyy`
4.  Chờ bot xử lý tự động. Quy trình duyệt tài liệu thường mất vài phút.

### Quy Trình Chuyển Đổi Netflix URL

1. Chọn chức năng "Chuyển đổi Netflix URL" từ menu bot hoặc dùng lệnh `/convert_netflix_url`.
2.  Bot sẽ yêu cầu bạn nhập cookie Netflix hoặc gửi một tệp `.txt` chứa cookie.
3.  Gửi cookie của bạn (đảm bảo định dạng chính xác).
4.  Bot sẽ xử lý và trả về một URL đăng nhập ứng dụng Netflix.

### Quy Trình Kiểm Tra Thẻ (Check CC)

1. Chọn chức năng "🃏 Check CC Quick" từ menu hoặc dùng lệnh `/check_cc`.
2. Gửi danh sách thẻ theo định dạng `Số thẻ|Tháng|Năm|CVV` (hỗ trợ nhập văn bản trực tiếp hoặc file `.txt`).
3. Bot sẽ kiểm tra từng thẻ (tối đa 50 thẻ/lần).
4. Bot trả về bản tóm tắt (Live/Declined) và một file `cc.txt` chứa chi tiết kết quả.

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
│   ├── verify_commands.py  # Xử lý các lệnh xác thực SheerID
│   └── cc_handlers.py      # Xử lý tính năng kiểm tra thẻ tín dụng (Check CC)
├── checkCC/                # Module xử lý logic Check CC (Stripe/Thum.io)
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
|:-------------------|:---------|:-----------------------------------------|
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
