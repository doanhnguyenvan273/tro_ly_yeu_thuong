import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path

# Đảm bảo đường dẫn import hoạt động chính xác
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import config
import database
import deadline_ml
import menstrual_ml
import scheduler
import bot_interactive

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP Handler siêu nhẹ phục vụ UptimeRobot ping mỗi 5 phút.
    Giúp Render Free Web Service chạy 24/7 vĩnh viễn mà không bao giờ bị ngủ (Never Sleep).
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        response_body = {
            "status": "online",
            "app": "Trợ Lý Yêu Thương 💖",
            "database": "Turso Cloud DB",
            "timestamp": time.time()
        }
        self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Tắt bớt log ping để terminal sạch đẹp
        pass

def start_http_server(port: int):
    """Khởi chạy máy chủ HTTP tối giản."""
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌐 [HTTP Server] Đang lắng nghe trên cổng {port} (Sẵn sàng nhận UptimeRobot ping)...")
    httpd.serve_forever()

def main():
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG TRỢ LÝ YÊU THƯƠNG (HYBRID CLOUD WEB SERVICE 24/7)")
    print("=" * 65)

    # 1. Khởi tạo & Kiểm tra kết nối Turso CSDL
    print("[1/4] Kiểm tra Cơ sở dữ liệu...")
    database.init_db()

    # 2. Nạp mô hình AI
    print("[2/4] Nạp mô hình Machine Learning...")
    deadline_ml.train_or_load_deadline_model()
    menstrual_ml.train_or_load_menstrual_model()

    # 3. Chạy 2 tiến trình ngầm Scheduler và Telegram Bot
    print("[3/4] Kích hoạt Daemon Threads...")
    t1 = threading.Thread(target=scheduler.start_scheduler_loop, daemon=True, name="SchedulerLoop")
    t2 = threading.Thread(target=bot_interactive.lang_nghe_tin_nhan, daemon=True, name="TelegramPolling")
    t1.start()
    t2.start()

    # 4. Chạy HTTP Server trên port được Render cấp (PORT)
    port = int(os.getenv("PORT", 10000))
    print(f"[4/4] Khởi động Web Endpoint trên port {port}...")
    print("✅ Hệ thống đã sẵn sàng 24/7! Dữ liệu đồng bộ trực tiếp với Turso Cloud.")
    start_http_server(port)

if __name__ == "__main__":
    main()
