import os
import sys
import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

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

# Thống kê uptime
_START_TIME = time.time()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP Handler siêu nhẹ phục vụ UptimeRobot ping mỗi 5 phút.
    Giúp Render Free Web Service chạy 24/7 mà không bị ngủ (Never Sleep).
    """
    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/" or path == "/health":
            self._handle_health()
        elif path == "/ping":
            self._handle_ping()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def _handle_health(self):
        """Endpoint chi tiết cho monitoring."""
        uptime_seconds = int(time.time() - _START_TIME)
        uptime_h = uptime_seconds // 3600
        uptime_m = (uptime_seconds % 3600) // 60

        # Lấy thông tin nhanh từ DB
        try:
            all_schedules = database.get_all_schedules()
            all_tasks = database.get_all_tasks()
            active_tasks = [t for t in all_tasks if t.get("status") != "Đã hoàn thành"]
            db_status = "connected"
        except Exception:
            all_schedules = []
            active_tasks = []
            db_status = "error"

        response_body = {
            "status": "online",
            "app": "Trợ Lý Yêu Thương 💖",
            "version": "2.0-cloud",
            "database": "Turso Cloud DB" if (config.TURSO_DATABASE_URL and config.TURSO_AUTH_TOKEN) else "SQLite Local",
            "db_status": db_status,
            "uptime": f"{uptime_h}h {uptime_m}m",
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stats": {
                "subjects": len(all_schedules),
                "active_deadlines": len(active_tasks),
            }
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode("utf-8"))

    def _handle_ping(self):
        """Endpoint cực nhẹ cho UptimeRobot."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"pong")

    def log_message(self, format, *args):
        # Tắt bớt log ping để terminal sạch đẹp hơn
        pass


def start_http_server(port: int):
    """Khởi chạy máy chủ HTTP tối giản."""
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌐 [HTTP Server] Đang lắng nghe trên cổng {port}...")
    httpd.serve_forever()


def main():
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG TRỢ LÝ YÊU THƯƠNG (CLOUD WEB SERVICE 24/7)")
    print("=" * 65)

    # 1. Khởi tạo & Kiểm tra kết nối CSDL
    print("[1/4] Kiểm tra Cơ sở dữ liệu...")
    database.init_db()
    db_mode = "Turso Cloud" if (config.TURSO_DATABASE_URL and config.TURSO_AUTH_TOKEN) else "SQLite Local"
    print(f"      ✅ CSDL: {db_mode}")

    # 2. Nạp mô hình AI
    print("[2/4] Nạp mô hình Machine Learning...")
    deadline_ml.train_or_load_deadline_model()
    menstrual_ml.train_or_load_menstrual_model()
    print("      ✅ Mô hình AI đã sẵn sàng.")

    # 3. Chạy 2 tiến trình ngầm Scheduler và Telegram Bot
    print("[3/4] Kích hoạt Daemon Threads...")
    t1 = threading.Thread(target=scheduler.start_scheduler_loop, daemon=True, name="SchedulerLoop")
    t2 = threading.Thread(target=bot_interactive.lang_nghe_tin_nhan, daemon=True, name="TelegramPolling")
    t1.start()
    t2.start()
    print("      ✅ SchedulerLoop & TelegramPolling đã khởi động.")

    # 4. Chạy HTTP Server trên port được Render cấp (PORT)
    port = int(os.getenv("PORT", 10000))
    print(f"[4/4] Khởi động Web Endpoint trên port {port}...")

    if config.ALLOWED_CHAT_IDS:
        print(f"🔒 Bảo mật BẬT: Chỉ phản hồi Chat IDs: {config.ALLOWED_CHAT_IDS}")
    else:
        print("⚠️  Cảnh báo: Chưa cấu hình HER_CHAT_ID / YOUR_CHAT_ID!")

    print("✅ Hệ thống Trợ Lý Yêu Thương đã sẵn sàng 24/7!")
    print(f"   🌐 Health: http://0.0.0.0:{port}/health")
    print(f"   🏓 Ping:   http://0.0.0.0:{port}/ping")
    print("=" * 65)

    start_http_server(port)


if __name__ == "__main__":
    main()
