# Sử dụng hình ảnh Python 3.11 chính thức
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các phụ thuộc hệ thống (Cần thiết cho Playwright và WeasyPrint/xhtml2pdf cairo)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    build-essential \
    gcc \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    python3-dev \
    # Thêm các thư viện C/C++ bổ sung cho Cairo và WeasyPrint \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Sao chép tệp yêu cầu
COPY requirements.txt .

# Cài đặt phụ thuộc Python (Không sử dụng cache)
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt trình duyệt Playwright
RUN playwright install chromium

# Sao chép toàn bộ tệp dự án (.dockerignore sẽ tự động loại bỏ các tệp không cần thiết)
COPY . .

# Xóa toàn bộ cache Python (Đảm bảo sử cả dụng mã mới nhất)
RUN find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Thiết lập Python không tạo tệp bytecode (Tránh vấn đề bộ nhớ đệm)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cấu hình cổng cho Render (mặc định 8080)
ENV PORT=8080
EXPOSE 8080

# Kiểm tra sức khỏe (Healthcheck) của bot
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*bot.py" || exit 1

# Khởi chạy bot
CMD ["python", "-u", "bot.py"]
