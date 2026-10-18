import os
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta
import time

# Thiết lập múi giờ Việt Nam (UTC+7) cho toàn bộ hệ thống
VN_TZ = timezone(timedelta(hours=7))

# Thiết lập timezone cho hệ điều hành Linux (Render) nếu hỗ trợ
if hasattr(time, "tzset"):
    os.environ["TZ"] = "Asia/Ho_Chi_Minh"
    try:
        time.tzset()
    except Exception:
        pass

def get_now() -> datetime:
    """
    Trả về thời gian hiện tại chuẩn múi giờ Việt Nam (GMT+7).
    Trả về naive datetime để tương thích 100% với strptime, sqlite và phép trừ ngày giờ.
    """
    return datetime.now(VN_TZ).replace(tzinfo=None)

# Nạp biến môi trường từ file .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Đường dẫn tuyệt đối chuẩn hóa (hoạt động tốt trên cả Windows và Linux/Render)
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODEL_DIR = str(MODELS_DIR)  # Hỗ trợ string path
UPLOADS_DIR = DATA_DIR / "uploads"

# Đảm bảo các thư mục cần thiết tồn tại
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Đường dẫn CSDL và Mô hình AI
DB_PATH = DATA_DIR / "schedule_data.db"
MENSTRUAL_MODEL_PATH = MODELS_DIR / "menstrual_model.pkl"
DEADLINE_MODEL_PATH = MODELS_DIR / "deadline_model.pkl"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Cấu hình mặc định
DEFAULT_SETTINGS = {
    "telegram_bot_token": "",
    "telegram_her_chat_id": "",
    "telegram_my_chat_id": "",
    "her_name": "Em bé 🌸",
    "my_name": "Anh 💖",
    "startup_greeting_sent": False,
    "secret_mode_enabled": True
}

def load_settings() -> dict:
    """Tải cấu hình từ file settings.json hoặc khởi tạo mặc định."""
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict) -> bool:
    """Lưu cấu hình vào file settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu cài đặt: {e}")
        return False

# Nạp settings từ file (nếu có) để dự phòng
_settings = load_settings()

# ƯU TIÊN BIẾN MÔI TRƯỜNG (os.getenv) cho Render.com, sau đó fallback về settings.json
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or _settings.get("telegram_bot_token", "")
HER_CHAT_ID = os.getenv("HER_CHAT_ID") or _settings.get("telegram_her_chat_id", "")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID") or _settings.get("telegram_my_chat_id", "")

# Danh sách Chat ID được phép tương tác với Bot (Bảo mật, chống spam)
ALLOWED_CHAT_IDS = [str(cid).strip() for cid in [HER_CHAT_ID, YOUR_CHAT_ID] if str(cid).strip()]

# Mật khẩu bảo vệ giao diện Web (Streamlit trên Render hoặc mạng LAN)
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "Love2010")

# TURSO CLOUD DATABASE
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
if TURSO_DATABASE_URL.startswith("libsql://"):
    TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace("libsql://", "https://")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()

# Biến tương thích ngược
settings = _settings
TELEGRAM_HER_CHAT_ID = HER_CHAT_ID
TELEGRAM_MY_CHAT_ID = YOUR_CHAT_ID
