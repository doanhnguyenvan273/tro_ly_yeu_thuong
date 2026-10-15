import os
import sys
import threading
import time
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

def main():
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG TRỢ LÝ YÊU THƯƠNG 24/7 (RENDER.COM WORKER)")
    print("=" * 65)

    # 1. Khởi tạo Cơ sở Dữ liệu SQLite
    print("[1/3] Khởi tạo CSDL SQLite...")
    database.init_db()

    # 2. Kiểm tra nạp sẵn mô hình AI
    print("[2/3] Nạp mô hình AI...")
    deadline_ml.train_or_load_deadline_model()
    menstrual_ml.train_or_load_menstrual_model()

    # 3. Khởi chạy 2 tiến trình ngầm song song
    print("[3/3] Bật các tiến trình Daemon...")
    # Thread 1: Quét lịch & Gửi thông báo tự động (mỗi 60s)
    t1 = threading.Thread(target=scheduler.start_scheduler_loop, daemon=True, name="SchedulerWorkerThread")
    # Thread 2: Lắng nghe tin nhắn tra cứu 2 chiều từ Telegram (Long Polling)
    t2 = threading.Thread(target=bot_interactive.lang_nghe_tin_nhan, daemon=True, name="TelegramPollingThread")

    t1.start()
    t2.start()

    print("✅ Hệ thống Trợ Lý Yêu Thương đã sẵn sàng và đang chạy ngầm 24/7!")
    if config.ALLOWED_CHAT_IDS:
        print(f"🔒 Chế độ bảo mật BẬT: Chỉ phản hồi các Chat ID: {config.ALLOWED_CHAT_IDS}")
    else:
        print("⚠️ Cảnh báo: Chưa cấu hình HER_CHAT_ID hoặc YOUR_CHAT_ID trong biến môi trường!")

    # Giữ tiến trình main không bị thoát
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n[Hệ thống] Đang dừng tiến trình Worker an toàn...")
        scheduler.stop_scheduler()
        bot_interactive.stop_telegram_listener()
        sys.exit(0)

if __name__ == "__main__":
    main()
