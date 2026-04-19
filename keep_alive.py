from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    # Render cung cấp cổng qua biến môi trường PORT, mặc định là 8080 nếu chạy local
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
