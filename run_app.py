import os
import sys
import subprocess
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

def main():
    print("=" * 60)
    print("🌸 TRỢ LÝ YÊU THƯƠNG (HER PERSONAL ASSISTANT) v2.0 💖")
    print("=" * 60)
    print("[1/4] Khởi tạo Cơ sở Dữ liệu SQLite...")
    database.init_db()
    
    print("[2/4] Kiểm tra & Huấn luyện Mô hình Machine Learning...")
    deadline_ml.train_or_load_deadline_model()
    menstrual_ml.train_or_load_menstrual_model()
    
    print("[3/4] Môi trường & Backend sẵn sàng...")
    
    print("[4/4] Khởi chạy giao diện Desktop Streamlit App...")
    # Lấy đường dẫn python hiện tại
    python_exe = sys.executable
    app_file = CURRENT_DIR / "app.py"
    
    # Khởi chạy streamlit app
    cmd = [
        python_exe,
        "-m", "streamlit",
        "run",
        str(app_file),
        "--server.headless=false",
        "--browser.gatherUsageStats=false"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[Hệ thống] Đang dừng Trợ Lý Yêu Thương...")
        scheduler.stop_scheduler()
        sys.exit(0)

if __name__ == "__main__":
    main()
