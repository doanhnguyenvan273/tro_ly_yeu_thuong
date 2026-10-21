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
    "her_name": "Cậu 🌸",
    "my_name": "Tớ 💫",
    "startup_greeting_sent": False,
    "secret_mode_enabled": True,
    "app_passcode": "2010",
    "web_app_url": "",
    "weather_city": "Hà Nội",
    "weather_latitude": 21.0285,
    "weather_longitude": 105.8542,
    "pinned_note": "",
    "pinned_note_time": ""
}

def load_settings() -> dict:
    """Tải cấu hình từ file settings.json và đồng bộ với CSDL Cloud Turso (0MB lưu trữ)."""
    res = DEFAULT_SETTINGS.copy()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    res.update(data)
        except Exception:
            pass
    else:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Đồng bộ thêm từ CSDL Cloud (Turso / SQLite app_kv) để luôn đồng nhất tức thì giữa Telegram Bot & Web
    try:
        import database
        db_kv = database.get_all_app_kv()
        if db_kv:
            for k in ["pinned_note", "pinned_note_time", "app_passcode", "web_app_url", "weather_city", "her_name", "my_name", "secret_mode_enabled"]:
                if k in db_kv:
                    res[k] = db_kv[k]
    except Exception:
        pass

    return res

def save_settings(settings: dict) -> bool:
    """Lưu cấu hình vào file settings.json và CSDL Cloud Turso."""
    success = False
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        success = True
    except Exception as e:
        print(f"Lỗi khi lưu cài đặt vào file: {e}")

    # Ghi nhận lên Cloud CSDL để Web App Render cập nhật tức thì
    try:
        import database
        for k in ["pinned_note", "pinned_note_time", "app_passcode", "web_app_url", "weather_city", "her_name", "my_name", "secret_mode_enabled"]:
            if k in settings:
                database.set_app_kv(k, settings[k])
    except Exception:
        pass

    return success

# Nạp settings từ file (nếu có) để dự phòng
_settings = load_settings()

# ƯU TIÊN BIẾN MÔI TRƯỜNG (os.getenv) cho Render.com, sau đó fallback về settings.json
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or _settings.get("telegram_bot_token", "")
HER_CHAT_ID = os.getenv("HER_CHAT_ID") or _settings.get("telegram_her_chat_id", "")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID") or _settings.get("telegram_my_chat_id", "")

# Tên hiển thị: ưu tiên biến môi trường, sau đó settings.json, cuối cùng là default
HER_NAME = os.getenv("HER_NAME") or _settings.get("her_name", "Cậu 🌸")
MY_NAME = os.getenv("MY_NAME") or _settings.get("my_name", "Tớ 💫")

def get_her_name() -> str:
    """Lấy tên hiển thị của Cậu Ấy đồng bộ từ settings."""
    st = load_settings()
    return os.getenv("HER_NAME") or st.get("her_name", "Cậu 🌸").strip() or "Cậu 🌸"

def get_my_name() -> str:
    """Lấy tên hiển thị của Tớ đồng bộ từ settings."""
    st = load_settings()
    return os.getenv("MY_NAME") or st.get("my_name", "Tớ 💫").strip() or "Tớ 💫"

def get_display_names() -> tuple[str, str]:
    """Lấy cặp tên hiển thị (her_name, my_name) chuẩn hóa."""
    return get_her_name(), get_my_name()

# Danh sách Chat ID được phép tương tác với Bot (Bảo mật, chống spam)
ALLOWED_CHAT_IDS = [str(cid).strip() for cid in [HER_CHAT_ID, YOUR_CHAT_ID] if str(cid).strip()]

# Mật khẩu bảo vệ giao diện Web (Streamlit trên Render hoặc mạng LAN)
APP_PASSCODE = os.getenv("APP_PASSCODE") or _settings.get("app_passcode", "2010")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", APP_PASSCODE)
WEB_APP_URL  = os.getenv("WEB_APP_URL") or _settings.get("web_app_url", "")

# TURSO CLOUD DATABASE
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
if TURSO_DATABASE_URL.startswith("libsql://"):
    TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace("libsql://", "https://")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()

# Biến tương thích ngược
settings = _settings
TELEGRAM_HER_CHAT_ID = HER_CHAT_ID
TELEGRAM_MY_CHAT_ID = YOUR_CHAT_ID

def get_magic_link(nav=None) -> str:
    """Trả về Magic Link 1-chạm mở thẳng Web App nếu web_app_url đã cấu hình."""
    cfg = load_settings()
    base_url = os.getenv("WEB_APP_URL") or cfg.get("web_app_url", "").strip()
    passcode = os.getenv("APP_PASSCODE") or cfg.get("app_passcode", "2010").strip()
    if not base_url:
        return ""
    url = f"{base_url.rstrip('/')}/?key={passcode}"
    if nav:
        url += f"&nav={nav}"
    return url
