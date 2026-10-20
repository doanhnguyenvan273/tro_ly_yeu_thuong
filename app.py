import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import os
import base64

import importlib
import config
import database
importlib.reload(database)
import deadline_ml
import menstrual_ml
import medicine_ocr
import notifier
import scheduler
import telegram_listener

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (phải là lệnh đầu tiên)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trợ Lý Yêu Thương 💖",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Khởi động scheduler & telegram listener (chỉ 1 lần duy nhất cho toàn bộ app)
@st.cache_resource
def init_background_services():
    scheduler.start_scheduler()
    telegram_listener.start_telegram_listener()
    return True

init_background_services()

# ──────────────────────────────────────────────────────────────────────────────
# PWA & MOBILE META INJECTION
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Trợ Lý 🌸">
<link rel="apple-touch-icon" href="/app/static/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="/app/static/icon-192.png">
<meta name="theme-color" content="#ff758c">
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Modern Soft Dashboard
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; color: #333; }

/* ── Nền tổng thể ── */
.stApp { background: linear-gradient(135deg, #fff5f7 0%, #fbf5ff 50%, #fff9f5 100%) !important; }

/* ── Ẩn sidebar hoàn toàn ── */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Ẩn menu Streamlit mặc định & giải phóng không gian đỉnh ── */
#MainMenu { display: none !important; }
footer    { display: none !important; }
header, [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }

/* ── Container chính: cho phép cuộn tự nhiên 100%, không bị khóa cuộn ── */
html, body, .stApp, section.main, [data-testid="stMain"], [data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
    overflow-y: auto !important;
}
.block-container {
    padding-top: 75px !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
    overflow: visible !important;
}

/* ══════════════════════════════════════════════════════
   STICKY NAVBAR TRÀN HẾT MÀN HÌNH (EDGE-TO-EDGE FIXED)
   ══════════════════════════════════════════════════════ */
.st-key-sticky_nav_container {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    z-index: 999999 !important;
    background: rgba(255, 255, 255, 0.96) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08) !important;
    border-bottom: 1.5px solid rgba(255, 182, 193, 0.5) !important;
    padding: 8px 24px !important;
    box-sizing: border-box !important;
    border-radius: 0 !important;
    margin: 0 !important;
}
.st-key-sticky_nav_container div[data-testid="stHorizontalBlock"] {
    align-items: center !important;
}
.navbar-logo {
    font-size: 1.15rem;
    font-weight: 700;
    color: #d81159;
    white-space: nowrap;
    display: flex;
    align-items: center;
}
.nav-status-wrap {
    display: flex;
    justify-content: flex-end;
    align-items: center;
}
.navbar-status {
    background: linear-gradient(135deg, #e8f8f0, #f0fff6);
    border: 1px solid #b7ebd0;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #0d8a52;
    white-space: nowrap;
}

/* ── RESPONSIVE BREAKPOINT CHO NAVBAR: DESKTOP (> 768px) vs MOBILE (<= 768px) ── */
@media (min-width: 769px) {
    .st-key-desktop_nav_wrap {
        display: block !important;
    }
    .st-key-mobile_nav_wrap {
        display: none !important;
    }
    .block-container {
        padding-top: 75px !important;
    }
}

@media (max-width: 768px) {
    .st-key-desktop_nav_wrap {
        display: none !important;
    }
    .st-key-mobile_nav_wrap {
        display: block !important;
    }
    .st-key-sticky_nav_container {
        padding: 6px 12px !important;
    }
    .block-container {
        padding-top: 68px !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    .navbar-logo-mobile {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #d81159 !important;
        white-space: nowrap !important;
        display: flex !important;
        align-items: center !important;
    }
    .hero-section {
        flex-direction: column !important;
        align-items: flex-start !important;
        padding: 18px 16px !important;
        gap: 12px !important;
    }
    .hero-status-box {
        width: 100% !important;
        margin-top: 6px !important;
    }
    .hero-title {
        font-size: 1.45rem !important;
    }
}

/* Style nút Hamburger Popover trên Mobile */
.st-key-mobile_nav_wrap button[data-testid="stBaseButton-popover"] {
    background: linear-gradient(135deg, #fff0f3, #ffe6eb) !important;
    color: #d81159 !important;
    border: 1.5px solid #ffb6c1 !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    padding: 4px 12px !important;
    box-shadow: 0 2px 6px rgba(216, 17, 89, 0.12) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
.st-key-mobile_nav_wrap button[data-testid="stBaseButton-popover"]:hover {
    background: linear-gradient(135deg, #ffe6eb, #ffd9e2) !important;
    transform: translateY(-1px) !important;
    border-color: #d81159 !important;
}

/* Chấm tròn xanh 🟢 nhấp nháy cho Mobile Badge Popover */
.st-key-mobile_cloud_badge button[data-testid="stBaseButton-popover"] {
    background: #e8f8f0 !important;
    color: #0d8a52 !important;
    border: 1.5px solid #a8e6cf !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.05rem !important;
    box-shadow: 0 0 8px rgba(0, 184, 148, 0.35) !important;
    animation: pulse-cloud-badge 2s infinite !important;
    margin: 0 auto !important;
}

@keyframes pulse-cloud-badge {
    0% {
        box-shadow: 0 0 0 0 rgba(0, 184, 148, 0.6);
    }
    70% {
        box-shadow: 0 0 0 8px rgba(0, 184, 148, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(0, 184, 148, 0);
    }
}

/* ── STICKY NAVBAR RADIO BUTTONS (Horizontal Pill Navigation) ── */
.st-key-sticky_nav_container div[data-testid="stRadio"] {
    margin-bottom: 0 !important;
}
.st-key-sticky_nav_container div[data-testid="stWidgetLabel"],
.st-key-sticky_nav_container div[data-testid="stRadio"] > label {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-sticky_nav_container div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 6px !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    scrollbar-width: none !important;
}
.st-key-sticky_nav_container div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar {
    display: none !important;
}

/* Ẩn triệt để hình tròn radio của Streamlit */
.st-key-sticky_nav_container [data-testid="stRadioOption"] [class*="e1dm8mpf4"],
.st-key-sticky_nav_container [data-testid="stRadioOption"] [class*="e1dm8mpf5"],
.st-key-sticky_nav_container [data-testid="stRadioOption"] label > div:first-child,
.st-key-sticky_nav_container [data-testid="stRadioOption"] > div > div:first-child,
.st-key-sticky_nav_container [data-testid="stRadioOption"] input[type="radio"],
.st-key-sticky_nav_container [data-testid="stRadioOption"] svg,
.st-key-sticky_nav_container [data-testid="stRadioOption"] div[role="radio"],
.st-key-sticky_nav_container [data-testid="stRadioOption"] div:has(> div[style*="border-radius: 50%"]),
.st-key-sticky_nav_container [data-testid="stRadioOption"] div[style*="border-radius: 50%"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    position: absolute !important;
    pointer-events: none !important;
}

/* Định dạng từng Pill button menu */
.st-key-sticky_nav_container [data-testid="stRadioOption"] {
    margin: 0 !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
}
.st-key-sticky_nav_container [data-testid="stRadioOption"] > label,
.st-key-sticky_nav_container [data-testid="stRadioOption"] > div {
    background: rgba(255, 245, 247, 0.75) !important;
    border: 1.2px solid rgba(255, 182, 193, 0.5) !important;
    border-radius: 20px !important;
    padding: 5px 11px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    user-select: none !important;
}
.st-key-sticky_nav_container [data-testid="stRadioOption"]:hover > label,
.st-key-sticky_nav_container [data-testid="stRadioOption"]:hover > div {
    background: #fff0f5 !important;
    border-color: #ff758c !important;
    transform: translateY(-1px) !important;
}
.st-key-sticky_nav_container [data-testid="stRadioOption"] p,
.st-key-sticky_nav_container [data-testid="stRadioOption"] span {
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    color: #555555 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}

/* Nút được chọn (Active) */
.st-key-sticky_nav_container [data-testid="stRadioOption"]:has(input:checked) > label,
.st-key-sticky_nav_container [data-testid="stRadioOption"]:has(input:checked) > div,
.st-key-sticky_nav_container [data-testid="stRadioOption"][data-selected="true"] > label,
.st-key-sticky_nav_container [data-testid="stRadioOption"][data-selected="true"] > div {
    background: linear-gradient(135deg, #ff758c, #ff7eb3) !important;
    border-color: transparent !important;
    box-shadow: 0 4px 12px rgba(255, 117, 140, 0.35) !important;
}
.st-key-sticky_nav_container [data-testid="stRadioOption"]:has(input:checked) p,
.st-key-sticky_nav_container [data-testid="stRadioOption"]:has(input:checked) span,
.st-key-sticky_nav_container [data-testid="stRadioOption"][data-selected="true"] p,
.st-key-sticky_nav_container [data-testid="stRadioOption"][data-selected="true"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ══════════════════════════════════════════════════════
   HERO SECTION
   ══════════════════════════════════════════════════════ */
.hero-section {
    background: linear-gradient(135deg, #FF758C 0%, #FF7EB3 100%);
    border-radius: 20px;
    padding: 28px 36px 24px 36px;
    color: white;
    box-shadow: 0 10px 30px rgba(255, 117, 140, 0.28);
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
}
.hero-title {
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 0.95rem;
    opacity: 0.92;
    margin: 0 0 16px 0;
    line-height: 1.55;
}
.hero-btn, a.hero-btn, a.hero-btn:visited, a.hero-btn:hover, a.hero-btn:active {
    display: inline-block !important;
    background: rgba(255,255,255,0.22) !important;
    border: 1.5px solid rgba(255,255,255,0.5) !important;
    border-radius: 24px !important;
    padding: 8px 20px !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    cursor: pointer !important;
    margin-right: 8px !important;
    backdrop-filter: blur(4px) !important;
    transition: all 0.2s !important;
    text-decoration: none !important;
}
.hero-btn:hover, a.hero-btn:hover {
    background: rgba(255,255,255,0.38) !important;
    transform: translateY(-1px) !important;
    color: #ffffff !important;
    text-decoration: none !important;
}
.hero-status-box {
    background: rgba(255,255,255,0.18);
    border: 1.5px solid rgba(255,255,255,0.35);
    border-radius: 16px;
    padding: 14px 20px;
    text-align: center;
    min-width: 170px;
    backdrop-filter: blur(6px);
}
.hero-status-row { font-size: 0.82rem; margin: 3px 0; opacity: 0.95; }

/* ══════════════════════════════════════════════════════
   NAVBAR TABS (st.tabs override — full-width polished)
   ══════════════════════════════════════════════════════ */
div[data-testid="stTabs"] > div:first-child {
    background: rgba(255,255,255,0.9) !important;
    border-radius: 14px !important;
    padding: 6px 10px 4px 10px !important;
    border: 1.5px solid rgba(255,182,193,0.4) !important;
    box-shadow: 0 4px 16px rgba(255,182,193,0.14) !important;
    margin-bottom: 16px !important;
    gap: 4px !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    color: #c0185a !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.22s !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    background: #fff0f5 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #ff758c, #ff7eb3) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(255,117,140,0.35) !important;
}
div[data-testid="stTabs"] [role="tabpanel"] {
    padding-top: 4px !important;
}

/* ══════════════════════════════════════════════════════
   CARDS
   ══════════════════════════════════════════════════════ */
.card {
    background: #FFFFFF;
    border: 1px solid #FFE4E8;
    border-radius: 16px;
    padding: 18px 22px;
    box-shadow: 0 4px 15px rgba(255, 182, 193, 0.12);
    margin-bottom: 14px;
}
.card-hover-click {
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s !important;
}
.card-hover-click:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 25px rgba(255, 117, 140, 0.25) !important;
    border-color: #ff758c !important;
}
.cat-card {
    background: #FFFFFF;
    border: 1px solid #FFE4E8;
    border-radius: 14px;
    padding: 10px;
    box-shadow: 0 4px 15px rgba(255, 182, 193, 0.12);
    text-align: center;
}
.section-title { font-size: 1.05rem; font-weight: 700; color: #d81159; margin-bottom: 10px; }

/* ── Preview / Info box ── */
.preview-box {
    background: linear-gradient(135deg, #fff0f5, #ffe4e9);
    border: 1.5px solid #ffb3c6;
    border-radius: 14px;
    padding: 14px 18px;
    margin-top: 10px;
    font-size: 0.95rem;
    line-height: 1.7;
}
.preview-box b { color: #c0185a; }

/* ── Badges ── */
.badge-danger { background:#ffe0e6; color:#d81159; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #ffb3c1; display:inline-block; }
.badge-safe   { background:#e8f8f0; color:#0d8a52; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #b7ebd0; display:inline-block; }
.badge-warn   { background:#fff4e5; color:#d97706; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #fed7aa; display:inline-block; }

/* ── Step label ── */
.step-label { background:#ff758c; color:white; border-radius:50%; width:24px; height:24px;
    display:inline-flex; align-items:center; justify-content:center; font-weight:700;
    font-size:.82rem; margin-right:7px; }

/* ── Hint text ── */
.hint-text { font-size:.82rem; color:#888; margin-top:-4px; margin-bottom:7px; }

/* ── Buttons ── */
div.stButton > button {
    border-radius: 22px !important;
    font-weight: 600 !important;
    border: none !important;
    transition: all .22s !important;
}
div.stButton > button:hover { transform: scale(1.025) translateY(-1px) !important; }

/* ══════════════════════════════════════════════════════
   FOOTER
   ══════════════════════════════════════════════════════ */
.page-footer {
    margin-top: 36px;
    border-top: 1.5px solid #FFE4E8;
    padding-top: 18px;
    text-align: center;
    color: #888888;
    font-size: 0.82rem;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HIGH-PERFORMANCE DATA LAYER (Tăng tốc độ phản hồi, loại bỏ lag khi thao tác)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_settings():
    return config.load_settings()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_schedules():
    return database.get_all_schedules()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_tasks():
    return database.get_all_tasks()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_medicines():
    return database.get_all_medicines()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_today_meds(today_str: str):
    return database.get_today_medicine_status(today_str)

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_attendance_stats():
    return database.get_all_attendance_stats()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_single_attendance_stats(schedule_id: int):
    return database.get_attendance_stats(schedule_id)

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_menstrual_records():
    return database.get_all_menstrual_records()

@st.cache_data(ttl=45, show_spinner=False)
def get_cached_cycle_prediction():
    return menstrual_ml.predict_next_cycle()

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_mood_range(start_date: str, end_date: str):
    """Cache mood logs theo khoảng ngày — TTL 60s để matrix luôn fresh."""
    return database.get_mood_logs_range(start_date, end_date)

def invalidate_cache():
    """Xóa bộ nhớ đệm ngay lập tức khi thêm/sửa/xóa để giao diện cập nhật tức thì."""
    st.cache_data.clear()

@st.cache_data(show_spinner=False)
def get_cat_image_bytes(filename: str):
    path = os.path.join("catmeme", filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

def get_cat_image_base64(filename: str):
    raw = get_cat_image_bytes(filename)
    if raw:
        return base64.b64encode(raw).decode("utf-8")
    return None

def render_cat(filename: str, caption: str, width: int = 150):
    """Hiển thị sticker mèo mượt mà trực tiếp từ RAM cache."""
    data = get_cat_image_bytes(filename)
    if data:
        st.image(data, caption=caption, width=width)

settings = get_cached_settings()
her_name = settings.get("her_name", "Em Bé 🌸")

def check_schedule_conflicts(schedules):
    """Kiểm tra trùng lịch."""
    by_day = {}
    for s in schedules:
        by_day.setdefault(s.get("day_of_week", 0), []).append(s)
    for d, s_list in by_day.items():
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                s1, s2 = s_list[i], s_list[j]
                if s1["start_time"] < s2["end_time"] and s2["start_time"] < s1["end_time"]:
                    return True, s1, s2
    return False, None, None


# ──────────────────────────────────────────────────────────────────────────────
# STICKY NAVBAR (Widget Điều Hướng Tự Động Thích Ứng Desktop & Mobile)
# ──────────────────────────────────────────────────────────────────────────────
NAV_OPTIONS = [
    "🏠 Trang Chủ",
    "🎒 Lịch Học",
    "📝 Deadline",
    "🌸 Chu Kỳ",
    "💊 Đơn Thuốc",
    "📖 Cảm Xúc",
    "⚙️ Cài Đặt",
]

NAV_QUERY_MAP = {
    "TrangChu": "🏠 Trang Chủ",
    "LichHoc":  "🎒 Lịch Học",
    "Deadline": "📝 Deadline",
    "ChuKy":    "🌸 Chu Kỳ",
    "DonThuoc": "💊 Đơn Thuốc",
    "CamXuc":   "📖 Cảm Xúc",
    "CaiDat":   "⚙️ Cài Đặt",
}

# 1-Click chuyển tab từ các liên kết trên giao diện (?nav=...)
if "nav" in st.query_params:
    _qp_nav = st.query_params.get("nav")
    if _qp_nav in NAV_QUERY_MAP:
        _target_tab = NAV_QUERY_MAP[_qp_nav]
        st.session_state["active_nav"] = _target_tab
        st.session_state["nav_desktop"] = _target_tab
        st.session_state["nav_mobile"] = _target_tab
    try:
        del st.query_params["nav"]
    except Exception:
        pass

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = NAV_OPTIONS[0]

def sync_nav_from_desktop():
    if "nav_desktop" in st.session_state:
        val = st.session_state["nav_desktop"]
        st.session_state["active_nav"] = val
        st.session_state["nav_mobile"] = val

def sync_nav_from_mobile():
    if "nav_mobile" in st.session_state:
        val = st.session_state["nav_mobile"]
        st.session_state["active_nav"] = val
        st.session_state["nav_desktop"] = val

def goto_nav(target):
    st.session_state["active_nav"] = target
    st.session_state["nav_desktop"] = target
    st.session_state["nav_mobile"] = target
    st.rerun()

cur_idx = NAV_OPTIONS.index(st.session_state["active_nav"]) if st.session_state["active_nav"] in NAV_OPTIONS else 0

with st.container(key="sticky_nav_container"):
    # ── 1. GIAO DIỆN DESKTOP (width > 768px): Thanh ngang đầy đủ ──
    with st.container(key="desktop_nav_wrap"):
        c_logo, c_menu, c_status = st.columns([1.1, 5.8, 1.1], vertical_alignment="center")
        with c_logo:
            st.markdown('<div class="navbar-logo">💖 Trợ Lý Yêu Thương</div>', unsafe_allow_html=True)
        with c_menu:
            st.radio(
                "",
                options=NAV_OPTIONS,
                index=cur_idx,
                horizontal=True,
                label_visibility="collapsed",
                key="nav_desktop",
                on_change=sync_nav_from_desktop,
            )
        with c_status:
            st.markdown('<div class="nav-status-wrap"><span class="navbar-status">🟢 Cloud 24/7 &amp; Turso DB</span></div>', unsafe_allow_html=True)

    # ── 2. GIAO DIỆN MOBILE / TABLET (width <= 768px): Hamburger ☰ Popover & Chấm Xanh 🟢 ──
    with st.container(key="mobile_nav_wrap"):
        m_logo, m_menu, m_badge = st.columns([1.6, 3.4, 0.8], vertical_alignment="center")
        with m_logo:
            st.markdown('<div class="navbar-logo-mobile">💖 Trợ Lý</div>', unsafe_allow_html=True)
        with m_menu:
            with st.popover(f"☰ {st.session_state['active_nav']}", use_container_width=True):
                st.markdown("<div style='font-weight:700;color:#d81159;font-size:0.95rem;margin-bottom:8px;'>🌸 Chọn chuyên mục:</div>", unsafe_allow_html=True)
                st.radio(
                    "Mobile Nav",
                    options=NAV_OPTIONS,
                    index=cur_idx,
                    key="nav_mobile",
                    label_visibility="collapsed",
                    on_change=sync_nav_from_mobile,
                )
        with m_badge:
            with st.container(key="mobile_cloud_badge"):
                with st.popover("🟢", use_container_width=True):
                    st.markdown("""
                    <div style="font-size:0.86rem;line-height:1.65;min-width:210px;padding:4px 2px;">
                        <div style="font-weight:700;color:#0d8a52;font-size:0.95rem;margin-bottom:6px;border-bottom:1px solid #e0f2e9;padding-bottom:4px;">
                            🟢 Cloud 24/7 &amp; Turso DB
                        </div>
                        ☁️ <b>Server:</b> Online (Render Singapore)<br>
                        🗄️ <b>Database:</b> Turso Cloud (Tokyo)<br>
                        🤖 <b>Bot Telegram:</b> Polling 24/7 Active<br>
                        🔄 <b>Đồng bộ:</b> Thời gian thực 0đ
                    </div>
                    """, unsafe_allow_html=True)

selected_nav = st.session_state["active_nav"]

# ──────────────────────────────────────────────────────────────────────────────
# HERO SECTION
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-section">
    <div>
        <div class="hero-title">💖 Trợ Lý Yêu Thương 🌸</div>
        <div class="hero-subtitle">Dành riêng cho <b>{her_name}</b> — Đồng hành mỗi ngày<br>trong học tập và chăm sóc sức khỏe!</div>
        <div style="margin-top:14px;">
            <a href="?nav=LichHoc" target="_self" class="hero-btn" style="color:#ffffff !important;text-decoration:none !important;">📅 Xem Lịch Hôm Nay</a>
            <a href="?nav=DonThuoc" target="_self" class="hero-btn" style="color:#ffffff !important;text-decoration:none !important;">💊 Nhắc Uống Thuốc</a>
            <a href="?nav=CamXuc" target="_self" class="hero-btn" style="color:#ffffff !important;text-decoration:none !important;">📖 Ghi Cảm Xúc</a>
        </div>
    </div>
    <div class="hero-status-box">
        <div style="font-size:1.6rem;margin-bottom:4px;">🐱</div>
        <div class="hero-status-row">🟢 <b>Cloud 24/7</b></div>
        <div class="hero-status-row">Turso DB: Đã kết nối</div>
        <div class="hero-status-row">🤖 Telegram: Đang bật</div>
        <div class="hero-status-row" style="margin-top:6px;opacity:.8;">
            🕐 {config.get_now().strftime('%H:%M, %d/%m/%Y')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTING NỘI DUNG THEO STICKY NAVBAR
# ══════════════════════════════════════════════════════════════════════════════
if selected_nav == "🏠 Trang Chủ":
    # ── Trang Chủ Dashboard ──
    today_date = date.today()
    day_idx = today_date.weekday()
    day_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    today_day_name = day_names[day_idx]

    all_scheds_home = get_cached_schedules()
    today_scheds = [s for s in all_scheds_home if s.get("day_of_week") == day_idx]

    all_tasks_home = get_cached_tasks()
    pending_tasks = [t for t in all_tasks_home if t.get("status") != "Đã hoàn thành"]

    pred_home = get_cached_cycle_prediction()

    today_str_home = today_date.strftime("%Y-%m-%d")
    today_meds_home = get_cached_today_meds(today_str_home)
    total_meds_home = len(today_meds_home)
    taken_meds_home = sum(1 for m in today_meds_home if m["taken"]) if today_meds_home else 0

    # 1. Bốn Thẻ KPI Tổng Quan Nhanh (Click trực tiếp vào thẻ để chuyển tab Navbar tương ứng)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(
            f'<a href="?nav=LichHoc" target="_self" style="text-decoration:none;color:inherit;display:block;">'
            f'<div class="card card-hover-click" style="text-align:center;padding:18px 14px;cursor:pointer;">'
            f'<div style="font-size:1.8rem;margin-bottom:4px;">🎒</div>'
            f'<div style="font-weight:700;color:#d81159;font-size:0.95rem;">Lịch Học Hôm Nay</div>'
            f'<div style="font-size:1.35rem;font-weight:800;color:#333;margin:4px 0;">{len(today_scheds)} ca học</div>'
            f'<div style="font-size:0.78rem;color:#888;">{today_day_name} ({today_date.strftime("%d/%m")})</div>'
            f'<div style="font-size:0.75rem;color:#d81159;margin-top:6px;font-weight:600;">Xem chi tiết ➔</div>'
            f'</div>'
            f'</a>',
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f'<a href="?nav=Deadline" target="_self" style="text-decoration:none;color:inherit;display:block;">'
            f'<div class="card card-hover-click" style="text-align:center;padding:18px 14px;cursor:pointer;">'
            f'<div style="font-size:1.8rem;margin-bottom:4px;">⏰</div>'
            f'<div style="font-weight:700;color:#e67e22;font-size:0.95rem;">Deadline Cần Làm</div>'
            f'<div style="font-size:1.35rem;font-weight:800;color:#333;margin:4px 0;">{len(pending_tasks)} bài tập</div>'
            f'<div style="font-size:0.78rem;color:#888;">Đang chờ hoàn thành</div>'
            f'<div style="font-size:0.75rem;color:#e67e22;margin-top:6px;font-weight:600;">Quản lý task ➔</div>'
            f'</div>'
            f'</a>',
            unsafe_allow_html=True,
        )

    with kpi3:
        ck_status = f"Còn {pred_home['days_left']} ngày" if pred_home.get("has_data") else "Chưa có dữ liệu"
        st.markdown(
            f'<a href="?nav=ChuKy" target="_self" style="text-decoration:none;color:inherit;display:block;">'
            f'<div class="card card-hover-click" style="text-align:center;padding:18px 14px;cursor:pointer;">'
            f'<div style="font-size:1.8rem;margin-bottom:4px;">🌸</div>'
            f'<div style="font-weight:700;color:#e84393;font-size:0.95rem;">Chu Kỳ Sinh Lý</div>'
            f'<div style="font-size:1.35rem;font-weight:800;color:#333;margin:4px 0;">{ck_status}</div>'
            f'<div style="font-size:0.78rem;color:#888;">Dự kiến: {pred_home.get("predicted_next_date", "---")}</div>'
            f'<div style="font-size:0.75rem;color:#e84393;margin-top:6px;font-weight:600;">Xem dự đoán ➔</div>'
            f'</div>'
            f'</a>',
            unsafe_allow_html=True,
        )

    with kpi4:
        med_status = f"{taken_meds_home}/{total_meds_home} liều" if total_meds_home else "Trống lịch"
        med_sub = 'Đã uống đủ! 🎉' if total_meds_home and taken_meds_home == total_meds_home else 'Nhắc giờ Telegram 🤖'
        st.markdown(
            f'<a href="?nav=DonThuoc" target="_self" style="text-decoration:none;color:inherit;display:block;">'
            f'<div class="card card-hover-click" style="text-align:center;padding:18px 14px;cursor:pointer;">'
            f'<div style="font-size:1.8rem;margin-bottom:4px;">💊</div>'
            f'<div style="font-weight:700;color:#00b894;font-size:0.95rem;">Thuốc Hôm Nay</div>'
            f'<div style="font-size:1.35rem;font-weight:800;color:#333;margin:4px 0;">{med_status}</div>'
            f'<div style="font-size:0.78rem;color:#888;">{med_sub}</div>'
            f'<div style="font-size:0.75rem;color:#00b894;margin-top:6px;font-weight:600;">Xem đơn thuốc ➔</div>'
            f'</div>'
            f'</a>',
            unsafe_allow_html=True,
        )

    # 2. Bố cục 2.5 : 1 — Chi tiết ngày hôm nay & Meme Mèo
    c_home_main, c_home_cat = st.columns([2.5, 1])
    with c_home_main:
        st.markdown(
            f'<div class="card">'
            f'<div class="section-title">✨ Chào ngày mới, {her_name}! 🌸</div>'
            f'<div style="font-size:0.93rem;color:#555;line-height:1.75;margin-bottom:14px;">'
            f'Hôm nay là <b>{today_day_name}, ngày {today_date.strftime("%d/%m/%Y")}</b>. Chúc em một ngày học tập thật hiệu quả, luôn rạng rỡ và nhớ chăm sóc sức khỏe nhé! Anh và Trợ Lý Yêu Thương luôn đồng hành cùng em 💖'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_sch_d, col_task_d = st.columns(2)
        with col_sch_d:
            if today_scheds:
                sch_items = []
                for sc in today_scheds:
                    sch_items.append(
                        f'<div style="border-left:3px solid #ff758c;padding-left:12px;margin-bottom:10px;text-align:left;">'
                        f'<div style="font-weight:700;color:#333;font-size:0.92rem;">{sc["subject_name"]}</div>'
                        f'<div style="font-size:0.83rem;color:#666;margin-top:2px;">🕒 {sc["start_time"]} - {sc["end_time"]} | 📍 {sc.get("room") or "Chưa có phòng"}</div>'
                        f'</div>'
                    )
                sch_body_html = "".join(sch_items)
            else:
                sch_body_html = '<div style="color:#888;font-size:0.88rem;margin-top:8px;line-height:1.6;">🎉 Hôm nay không có môn học nào! Em thoải mái nghỉ ngơi hoặc ôn bài nhé.</div>'

            sch_card_html = (
                f'<a href="?nav=LichHoc" target="_self" style="text-decoration:none;color:inherit;display:block;">'
                f'<div class="card card-hover-click" style="min-height:190px;cursor:pointer;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;width:100%;margin-bottom:12px;">'
                f'<div class="section-title" style="margin:0;display:inline-flex;align-items:center;">🎒 Chi tiết lịch học hôm nay</div>'
                f'<div style="font-size:0.8rem;color:#d81159;font-weight:700;white-space:nowrap;margin-left:auto;">Mở lịch ➔</div>'
                f'</div>'
                f'{sch_body_html}'
                f'</div>'
                f'</a>'
            )
            st.markdown(sch_card_html, unsafe_allow_html=True)

        with col_task_d:
            if pending_tasks:
                task_items = []
                for tk in pending_tasks[:3]:
                    _task_title = tk.get('task_name') or tk.get('title') or 'Nhiệm vụ'
                    _subject    = tk.get('subject_name') or 'Môn học'
                    _dl         = tk.get('deadline') or 'Chưa có hạn'
                    task_items.append(
                        f'<div style="border-left:3px solid #e67e22;padding-left:12px;margin-bottom:10px;text-align:left;">'
                        f'<div style="font-weight:700;color:#333;font-size:0.92rem;">{_task_title}</div>'
                        f'<div style="font-size:0.83rem;color:#666;margin-top:2px;">⏳ Hạn: {_dl} | Môn: {_subject}</div>'
                        f'</div>'
                    )
                task_body_html = "".join(task_items)
            else:
                task_body_html = '<div style="color:#888;font-size:0.88rem;margin-top:8px;line-height:1.6;">✨ Không có deadline nào đang dồn ập! Cứ từ từ thưởng thức ngày mới nha.</div>'

            task_card_html = (
                f'<a href="?nav=Deadline" target="_self" style="text-decoration:none;color:inherit;display:block;">'
                f'<div class="card card-hover-click" style="min-height:190px;cursor:pointer;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;width:100%;margin-bottom:12px;">'
                f'<div class="section-title" style="margin:0;display:inline-flex;align-items:center;">⏰ Deadline gần nhất</div>'
                f'<div style="font-size:0.8rem;color:#e67e22;font-weight:700;white-space:nowrap;margin-left:auto;">Quản lý ➔</div>'
                f'</div>'
                f'{task_body_html}'
                f'</div>'
                f'</a>'
            )
            st.markdown(task_card_html, unsafe_allow_html=True)

    with c_home_cat:
        cat_b64 = get_cat_image_base64("smile-cat.png")
        if cat_b64:
            cat_card_html = (
                f'<div class="cat-card">'
                f'<img src="data:image/png;base64,{cat_b64}" style="width:100%;max-width:180px;border-radius:12px;margin:0 auto 8px auto;display:block;">'
                f'<div style="font-size:0.84rem;color:#777;font-weight:600;">Chúc {her_name} một ngày siêu vui vẻ! 😸🌸</div>'
                f'</div>'
            )
            st.markdown(cat_card_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="cat-card">', unsafe_allow_html=True)
            render_cat("smile-cat.png", f"Chúc {her_name} một ngày siêu vui vẻ! 😸🌸", width=170)
            st.markdown('</div>', unsafe_allow_html=True)

        remind_card_html = (
            f'<div class="card" style="margin-top:14px;text-align:center;">'
            f'<div style="font-weight:700;color:#d81159;font-size:0.9rem;">💌 Lời nhắc hôm nay</div>'
            f'<div style="font-size:0.84rem;color:#666;margin-top:6px;line-height:1.6;">'
            f'Uống đủ 2 lít nước, không bỏ bữa sáng và nhớ mỉm cười thật nhiều nha bé iu! 🍵✨'
            f'</div>'
            f'</div>'
        )
        st.markdown(remind_card_html, unsafe_allow_html=True)

elif selected_nav == "🎒 Lịch Học":
    all_scheds = get_cached_schedules()
    has_conflict, c_s1, c_s2 = check_schedule_conflicts(all_scheds)

    # ── Header row ──
    col_lh_main, col_lh_cat = st.columns([2.5, 1])
    with col_lh_main:
        st.subheader("🎒 Lịch Học & Điểm Danh Chuyên Cần")
        st.markdown('<p class="hint-text">Theo dõi lịch học cả tuần, quản lý số buổi vắng và tự động tính chuyên cần.</p>', unsafe_allow_html=True)
        if has_conflict:
            st.warning(f"⚠️ **HUH? Phát hiện trùng lịch:** Môn **{c_s1['subject_name']}** và **{c_s2['subject_name']}** bị đè giờ nhau vào {c_s1['day_name']} ({c_s1['start_time']}-{c_s1['end_time']} & {c_s2['start_time']}-{c_s2['end_time']})!")
    with col_lh_cat:
        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        if has_conflict:
            render_cat("huh-cat.jpg", "HUH? Trùng lịch rồi?! 🙀❓", width=150)
        else:
            render_cat("study-cat.jpg", "Học bài thuiii, không là thành người tối cổ đó! 🐱📚", width=150)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Sub-tabs ──
    sub_add, sub_att, sub_view = st.tabs(["➕ Thêm Môn Học", "📝 Điểm Danh Hôm Nay", "📊 Toàn Bộ Lịch Học"])

    # ────────────────────── THÊM MÔN HỌC ──────────────────────
    with sub_add:
        form_col, tips_col = st.columns([2.2, 1])

        with form_col:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="hint-text">Điền thông tin bên dưới để lưu một môn học vào lịch tuần. (*) là bắt buộc.</p>', unsafe_allow_html=True)

            fa, fb = st.columns([1.8, 1])
            with fa:
                st.markdown('<span class="step-label">1</span> <b>Tên môn học (*)</b>', unsafe_allow_html=True)
                subj_name = st.text_input("ten_mon", placeholder="VD: Lập trình Web, Tiếng Anh B2...",
                    label_visibility="collapsed",
                    help="Nhập đúng tên môn học trên thời khóa biểu của em")
            with fb:
                day_opts  = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"]
                day_select = st.selectbox("📅 Ngày học (*)", day_opts,
                    help="Chọn thứ mà môn này được dạy mỗi tuần")

            fc, fd, fe = st.columns(3)
            with fc:
                category = st.selectbox("🏷️ Loại môn",
                    ["Môn lý thuyết","Môn đồ án/bài tập lớn","Môn ngoại ngữ"])
            with fd:
                start_str = st.text_input("🕗 Giờ bắt đầu (*)", value="07:30", placeholder="07:30")
            with fe:
                end_str   = st.text_input("🕙 Giờ kết thúc (*)", value="11:00", placeholder="11:00")

            # Quick-fill
            st.markdown('<p class="hint-text">⚡ Gợi ý ca học nhanh:</p>', unsafe_allow_html=True)
            qc1, qc2, qc3, qc4, qc5 = st.columns(5)
            if qc1.button("Ca 1\n07:30-11:00", use_container_width=True):  start_str="07:30"; end_str="11:00"
            if qc2.button("Ca 2\n11:30-15:00", use_container_width=True):  start_str="11:30"; end_str="15:00"
            if qc3.button("Ca 3\n13:00-16:30", use_container_width=True):  start_str="13:00"; end_str="16:30"
            if qc4.button("Ca 4\n15:30-19:00", use_container_width=True):  start_str="15:30"; end_str="19:00"
            if qc5.button("Ca tối\n18:00-21:00", use_container_width=True): start_str="18:00"; end_str="21:00"

            fg, fh, fi = st.columns(3)
            with fg:
                room = st.text_input("📍 Phòng học", placeholder="VD: A2-301, Zoom...",
                    help="Có thể bỏ trống")
            with fh:
                total_sess = st.number_input("📋 Tổng số buổi (*)", min_value=1, max_value=100, value=10, step=1)
            with fi:
                max_allowed_limit = max(0, int(total_sess)-1)
                default_max       = min(1, max_allowed_limit)
                max_abs = st.number_input(f"🚨 Buổi được nghỉ (0–{max_allowed_limit}) (*)",
                    min_value=0, max_value=max_allowed_limit, value=default_max, step=1,
                    help=f"Phải nhỏ hơn tổng số buổi ({int(total_sess)})")

            notes = ""
            with st.expander("📝 Ghi chú (không bắt buộc)"):
                notes = st.text_area("Ghi chú", placeholder="VD: Nhớ mang máy tính...", height=70, label_visibility="collapsed")

            if subj_name.strip():
                pct = round((max_abs/total_sess)*100, 1) if total_sess else 0
                st.markdown(f"""<div class="preview-box">
                    <b>👁️ Xem trước:</b><br>
                    📚 <b>{subj_name}</b> &nbsp;|&nbsp; 🏷️ {category}<br>
                    📅 <b>{day_select}</b> &nbsp;|&nbsp; 🕒 <b>{start_str} → {end_str}</b> &nbsp;|&nbsp; 📍 {room or "(Chưa điền)"}<br>
                    📋 Tổng <b>{int(total_sess)} buổi</b> &nbsp;|&nbsp; 🚨 Được nghỉ: <b>{int(max_abs)} buổi</b> ({pct}%)
                </div>""", unsafe_allow_html=True)

            if st.button("💖 Lưu Môn Học Này Vào Lịch", use_container_width=True, type="primary"):
                err = []
                if not subj_name.strip(): err.append("Chưa nhập tên môn học")
                try: datetime.strptime(start_str, "%H:%M")
                except: err.append(f"Giờ bắt đầu '{start_str}' sai định dạng HH:MM")
                try: datetime.strptime(end_str, "%H:%M")
                except: err.append(f"Giờ kết thúc '{end_str}' sai định dạng HH:MM")
                if max_abs >= total_sess:
                    err.append(f"Số buổi nghỉ ({int(max_abs)}) phải nhỏ hơn tổng buổi ({int(total_sess)})!")
                if err:
                    for e in err: st.error(f"⚠️ {e}")
                    render_cat("huh-cat.jpg","HUH? Sai thông tin rồi! 🙀❓", width=120)
                else:
                    day_idx = day_opts.index(day_select)
                    database.add_schedule(subj_name.strip(), day_idx, day_select, start_str, end_str,
                                          room.strip(), category, notes.strip() if notes else "",
                                          int(total_sess), int(max_abs))
                    invalidate_cache()
                    st.success(f"✅ Đã lưu môn '{subj_name}'! (Tổng: {int(total_sess)} buổi | Được nghỉ: {int(max_abs)} buổi)")
                    st.balloons()
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        with tips_col:
            st.markdown("""<div class="card">
                <div class="section-title">💡 Mẹo nhỏ</div>
                <div style="font-size:.87rem;line-height:1.75;color:#555;">
                🎯 Nhập đúng tên môn sẽ giúp Bot nhắc lịch chính xác hơn!<br><br>
                ⏰ Số buổi nghỉ = 20% tổng buổi là mức phổ biến tại đa số trường.<br><br>
                📱 Sau khi lưu, Bot Telegram sẽ nhắc em <b>30 phút trước</b> giờ học!<br><br>
                🚨 Khi số buổi vắng vượt giới hạn → Hệ thống tự gửi cảnh báo CẤM THI!
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="cat-card">', unsafe_allow_html=True)
            render_cat("study-cat.jpg", "Học chăm vào nha bé! 📚😸", width=160)
            st.markdown('</div>', unsafe_allow_html=True)

    # ────────────────────── ĐIỂM DANH ──────────────────────
    with sub_att:
        if not all_scheds:
            st.info("📭 Chưa có môn học nào. Hãy thêm môn ở tab **➕ Thêm Môn Học** trước nhé!")
        else:
            st.markdown('<p class="hint-text">Chọn môn học, ngày học và đánh dấu trạng thái tham dự.</p>', unsafe_allow_html=True)

            sched_labels = [f"{s['subject_name']} ({s['day_name']} {s['start_time']}-{s['end_time']})" for s in all_scheds]
            sched_ids    = [s["id"] for s in all_scheds]

            att_c1, att_c2, att_c3, att_c4 = st.columns([2, 1, 1.2, 1.4])
            with att_c1:
                sel_idx = st.selectbox("Chọn môn học:", sched_labels)
                sel_id  = sched_ids[sched_labels.index(sel_idx)]
            with att_c2:
                att_date = st.date_input("Ngày học:", value=date.today())
            with att_c3:
                att_status = st.selectbox("Trạng thái:", ["Đã đi học","Vắng mặt","Học Online"])
            with att_c4:
                att_note = st.text_input("Lý do / ghi chú:", placeholder="VD: Bệnh...")

            stats       = get_cached_single_attendance_stats(sel_id)
            max_abs_val = stats.get("max_absences", 3)
            remaining   = stats.get("remaining_absences", max_abs_val - stats["absent"])

            ms1, ms2, ms3, ms4 = st.columns(4)
            ms1.metric("Đã đi học",    f"{stats['attended']} buổi")
            ms2.metric("Vắng mặt",     f"{stats['absent']} buổi",
                delta=f"{stats['absent_rate']}%", delta_color="inverse")
            ms3.metric("Học Online",   f"{stats['online']} buổi")
            ms4.metric("Giới hạn vắng", f"{max_abs_val} buổi")

            if stats["is_warning"]:
                st.error(f"🚨 **NGUY CƠ CẤM THI!** Đã vắng {stats['absent']}/{stats['total']} buổi ({stats['absent_rate']}%). Giới hạn: **{max_abs_val} buổi**!")
            elif remaining == 1:
                st.warning(f"⚠️ **CẢNH BÁO!** Chỉ còn được vắng **{remaining} buổi** nữa!")
            else:
                st.success(f"✅ Chuyên cần tốt! Còn được vắng tối đa **{remaining}** buổi (Giới hạn: {max_abs_val}).")

            if st.button("📝 Ghi Nhận Điểm Danh Buổi Này", use_container_width=True, type="primary"):
                database.log_attendance(sel_id, att_date.strftime("%Y-%m-%d"), att_status, att_note)
                invalidate_cache()
                st.success(f"✅ Đã ghi nhận: **{att_status}** ngày {att_date.strftime('%d/%m/%Y')}!")
                st.rerun()

    # ────────────────────── TOÀN BỘ LỊCH HỌC ──────────────────────
    with sub_view:
        if not all_scheds:
            st.info("Chưa có môn học nào.")
        else:
            all_stats    = get_cached_attendance_stats()
            stats_by_id  = {stt["schedule_id"]: stt for stt in all_stats}
            rows = []
            for s in all_scheds:
                stt        = stats_by_id.get(s["id"], {})
                max_abs_v  = stt.get("max_absences", s.get("max_absences", 3))
                abs_cnt    = stt.get("absent", 0)
                tot_cnt    = stt.get("total",  s.get("total_sessions", 10))
                remaining_v= stt.get("remaining_absences", max_abs_v - abs_cnt)
                rows.append({
                    "ID": s["id"], "Tên Môn": s["subject_name"], "Thứ": s["day_name"],
                    "Thời Gian": f"{s['start_time']}-{s['end_time']}", "Phòng": s["room"] or "-",
                    "Loại": s["category"],
                    "Vắng / Tổng": f"{abs_cnt}/{tot_cnt} ({stt.get('absent_rate',0.0)}%)",
                    "Giới hạn": f"{max_abs_v} buổi",
                    "Còn lại": f"{remaining_v} buổi",
                    "Cấm Thi": "🚨 Nguy cơ!" if stt.get("is_warning") else "✅ An toàn",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander("⚙️ Chỉnh sửa số buổi & giới hạn nghỉ"):
                sched_map  = {f"ID {s['id']}: {s['subject_name']} ({s['day_name']})": s for s in all_scheds}
                edit_label = st.selectbox("Chọn môn:", list(sched_map.keys()), key="edit_sched_sel")
                edit_sched = sched_map[edit_label]
                cur_total  = edit_sched.get("total_sessions", 10) or 10
                cur_max    = edit_sched.get("max_absences", 1) or 1
                ce1, ce2   = st.columns(2)
                with ce1:
                    new_total = st.number_input("Tổng số buổi:", 1, 100, int(cur_total), 1, key=f"et_{edit_sched['id']}")
                with ce2:
                    max_ed = max(0, int(new_total)-1)
                    val_ed = min(int(cur_max), max_ed)
                    new_max = st.number_input(f"Số buổi nghỉ (0–{max_ed}):", 0, max_ed, val_ed, 1, key=f"em_{edit_sched['id']}")
                if st.button("💾 Cập Nhật", use_container_width=True, type="primary"):
                    if new_max >= new_total:
                        st.error("Số buổi nghỉ phải nhỏ hơn tổng!")
                    else:
                        database.update_schedule_limits(edit_sched["id"], int(new_total), int(new_max))
                        invalidate_cache()
                        st.success(f"✅ Đã cập nhật '{edit_sched['subject_name']}': {int(new_total)} buổi, nghỉ {int(new_max)}!")
                        st.rerun()

            with st.expander("🗑️ Xóa môn học"):
                del_label = st.selectbox("Chọn môn cần xóa:",
                    [f"ID {s['id']}: {s['subject_name']} ({s['day_name']})" for s in all_scheds])
                del_id = int(del_label.split(":")[0].replace("ID","").strip())
                if st.button("Xác nhận xóa", type="primary"):
                    database.delete_schedule(del_id)
                    invalidate_cache()
                    st.success("Đã xóa!")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEADLINE & AI
# ══════════════════════════════════════════════════════════════════════════════
elif selected_nav == "📝 Deadline":
    # ── Header row ──
    col_dl_main, col_dl_cat = st.columns([2.5, 1])
    with col_dl_main:
        st.subheader("⏰ Quản Lý Deadline & AI Dự Đoán Rủi Ro")
        st.markdown('<p class="hint-text">Thêm bài tập, AI tự tính xác suất trễ hạn và Bot nhắc nhở đúng các mốc thời gian.</p>', unsafe_allow_html=True)

    tasks = get_cached_tasks()
    all_scheds = get_cached_schedules()
    now_dt = config.get_now()
    today_wd = now_dt.weekday()
    classes_today = len([s for s in all_scheds if s.get("day_of_week") == today_wd])

    with col_dl_cat:
        # Kiểm tra có bài tập nào đang trễ không để hiển thị meme phù hợp
        _has_overdue_p = any(
            t["status"] != "Đã hoàn thành" and datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M") < now_dt
            for t in tasks
        ) if tasks else False
        _has_pending_p = any(t["status"] != "Đã hoàn thành" for t in tasks) if tasks else False

        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        if not tasks or not _has_pending_p:
            render_cat("smile-cat.png", "Không có deadline! Tận hưởng thôi 😸✨", width=150)
        elif _has_overdue_p:
            render_cat("cry-cat.jpg", "Huhu, deadline trễ rồi cứu tuiii 😿", width=150)
        else:
            render_cat("burnOut_cat.jpg", "Deadline dí sát nút rùi! Áaaaa 🙀🔥", width=150)
        st.markdown('</div>', unsafe_allow_html=True)

    sub_add_t, sub_list_t, sub_ai_t = st.tabs(["➕ Thêm Deadline", "📋 Danh Sách Task", "🤖 Kiểm Tra AI Nhanh"])

    # ── Thêm deadline ──
    with sub_add_t:
        form_dl, tip_dl = st.columns([2.2, 1])
        with form_dl:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            subj_list  = list(set([s["subject_name"] for s in all_scheds])) if all_scheds else []

            st.markdown('<span class="step-label">1</span> <b>Thông tin bài tập</b>', unsafe_allow_html=True)
            ta1, ta2 = st.columns([2, 1])
            with ta1:
                task_name = st.text_input("Tên bài tập / đồ án (*)",
                    placeholder="VD: Báo cáo đồ án SE2033, Bài tập nhóm chương 4...",
                    help="Đặt tên rõ ràng để dễ nhận biết trong danh sách và tin nhắn nhắc nhở")
            with ta2:
                if subj_list:
                    subj_task = st.selectbox("Thuộc môn học:", subj_list)
                else:
                    subj_task = st.text_input("Thuộc môn học:", placeholder="VD: Công nghệ phần mềm")

            st.markdown('<span class="step-label">2</span> <b>Thời hạn nộp bài (Deadline)</b>', unsafe_allow_html=True)
            tb1, tb2 = st.columns(2)
            with tb1:
                due_date = st.date_input("Ngày hết hạn (*)", value=date.today() + timedelta(days=3))
            with tb2:
                due_hour = st.select_slider("Giờ hết hạn (*)",
                    options=["00:00","01:00","02:00","06:00","07:00","08:00","09:00","10:00",
                             "11:00","11:59","12:00","13:00","14:00","15:00","16:00","17:00",
                             "18:00","19:00","20:00","21:00","22:00","23:00","23:59"],
                    value="23:59")

            st.markdown('<span class="step-label">3</span> <b>Khối lượng công việc</b>', unsafe_allow_html=True)
            est_hours = st.slider("Ước tính cần bao nhiêu giờ để làm xong?",
                min_value=0.5, max_value=24.0, value=3.0, step=0.5)

            if task_name.strip():
                deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
                deadline_dt  = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
                diff_h       = (deadline_dt - config.get_now()).total_seconds() / 3600.0
                if diff_h > 0:
                    quick_ai   = deadline_ml.predict_deadline_risk(task_name, classes_today, diff_h, est_hours)
                    risk_color = "#d81159" if quick_ai["risk_percentage"] >= 70 else ("#d97706" if quick_ai["risk_percentage"] >= 40 else "#0d8a52")
                    st.markdown(f"""<div class="preview-box">
                        <b>👁️ Xem trước:</b><br>
                        📌 <b>{task_name}</b> &nbsp;|&nbsp; 📖 {subj_task}<br>
                        ⏳ Deadline: <b>{due_date.strftime('%d/%m/%Y')} lúc {due_hour}</b> (còn <b>{diff_h:.1f} giờ</b>)<br>
                        ⏱️ Ước tính: <b>{est_hours}h</b><br>
                        🤖 AI rủi ro hôm nay: <b style="color:{risk_color};">{quick_ai['risk_percentage']}% — {quick_ai['warning_level']}</b>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Ngày deadline đã qua rồi! Hãy chọn lại ngày đúng nhé.")

            if st.button("🚀 Lưu Task & Bắt Đầu Theo Dõi", use_container_width=True, type="primary"):
                if not task_name.strip():
                    st.error("Chưa nhập tên bài tập!")
                elif not subj_task or not str(subj_task).strip():
                    st.error("Chưa chọn môn học!")
                else:
                    deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
                    database.add_task(task_name.strip(), str(subj_task), deadline_str, float(est_hours), "Chưa làm")
                    invalidate_cache()
                    st.success(f"✅ Đã lưu task '{task_name}'! Bot Telegram sẽ nhắc đúng các mốc thời gian.")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        with tip_dl:
            st.markdown("""<div class="card">
                <div class="section-title">⚡ Mẹo Deadline</div>
                <div style="font-size:.87rem;line-height:1.8;color:#555;">
                🤖 AI phân tích dựa trên số ca học hôm đó & giờ rảnh thực tế.<br><br>
                🔴 Rủi ro ≥70%: Nên làm ngay hôm nay!<br>
                🟡 Rủi ro 40–70%: Ưu tiên làm sớm.<br>
                🟢 Rủi ro &lt;40%: Còn thời gian thoải mái.<br><br>
                📱 Bot tự nhắc trước <b>24h, 6h và 1h</b> deadline!
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Danh sách task ──
    with sub_list_t:
        if not tasks:
            col_notask, col_cat_dl = st.columns([2.2, 1])
            with col_notask:
                st.markdown("""<div class="card" style="padding:24px;">
                    <div class="section-title">🎉 Trống deadline!</div>
                    <p style="color:#555;line-height:1.75;">Em không có deadline nào đang chờ. Được nghỉ ngơi rồi! Tận hưởng khoảnh khắc nhé 🌸</p>
                </div>""", unsafe_allow_html=True)
            with col_cat_dl:
                st.markdown('<div class="cat-card">', unsafe_allow_html=True)
                render_cat("smile-cat.png", "Sạch deadline! Tận hưởng thôi! 😸✨", width=160)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            has_overdue = any(
                t["status"] != "Đã hoàn thành" and datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M") < now_dt
                for t in tasks
            )
            has_pending = any(t["status"] != "Đã hoàn thành" for t in tasks)

            col_tasks_main, col_tasks_cat = st.columns([2.2, 1])
            with col_tasks_cat:
                st.markdown('<div class="cat-card">', unsafe_allow_html=True)
                if not has_pending:
                    render_cat("smile-cat.png", "Em giỏi lắm! Dọn sạch deadline rồi! 😸✨", width=160)
                elif has_overdue:
                    render_cat("cry-cat.jpg", "Huhu, deadline trễ rồi cứu tuiii 😿💔", width=160)
                else:
                    render_cat("burnOut_cat.jpg", "Áaaaa! Sắp trễ deadline rồi cứu tuiii! 🔥🙀", width=160)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_tasks_main:
                filter_status = st.selectbox("Lọc:", ["Tất cả","Chưa làm","Đang làm","Đã hoàn thành"])

                for t in tasks:
                    if filter_status and filter_status != "Tất cả" and t["status"] != filter_status:
                        continue
                    d_dt   = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                    diff_h = (d_dt - now_dt).total_seconds() / 3600.0
                    pred   = deadline_ml.predict_deadline_risk(t["task_name"], classes_today, max(0.1,diff_h), t["estimated_hours"])
                    badge_cls = "badge-safe" if t["status"]=="Đã hoàn thành" else ("badge-warn" if t["status"]=="Đang làm" else "badge-danger")
                    risk_icon = "🔴" if pred["risk_percentage"]>=70 else ("🟡" if pred["risk_percentage"]>=40 else "🟢")
                    with st.container():
                        st.markdown(f"""<div class="card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                              <span style="font-weight:700;font-size:1rem;">📌 {t['task_name']}</span>
                              <span class="{badge_cls}">{t['status']}</span>
                            </div>
                            📖 {t['subject_name']} &nbsp;|&nbsp; ⏳ Hạn: <b>{t['deadline']}</b> (còn <b>{max(0,diff_h):.1f}h</b>) &nbsp;|&nbsp; ⏱️ {t['estimated_hours']}h<br>
                            {risk_icon} <b>AI Rủi ro:</b> {pred['risk_percentage']}% — {pred['warning_message']}
                        </div>""", unsafe_allow_html=True)
                        b1,b2,b3,b4 = st.columns(4)
                        if b1.button("⏳ Chưa làm", key=f"td_{t['id']}"):
                            database.update_task_status(t["id"],"Chưa làm")
                            invalidate_cache()
                            st.rerun()
                        if b2.button("🔨 Đang làm",  key=f"tp_{t['id']}"):
                            database.update_task_status(t["id"],"Đang làm")
                            invalidate_cache()
                            st.rerun()
                        if b3.button("🎉 Đã xong",   key=f"td2_{t['id']}"):
                            database.update_task_status(t["id"],"Đã hoàn thành")
                            invalidate_cache()
                            st.rerun()
                        if b4.button("🗑️ Xóa",        key=f"del_{t['id']}", type="secondary"):
                            database.delete_task(t["id"])
                            invalidate_cache()
                            st.rerun()

    # ── AI nhanh ──
    with sub_ai_t:
        col_ai_form, col_ai_tip = st.columns([2.2, 1])
        with col_ai_form:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**Thử nghiệm AI dự đoán rủi ro với thông số tùy chỉnh:**")
            st.markdown('<p class="hint-text">Công cụ kiểm tra nhanh — Không cần lưu vào CSDL.</p>', unsafe_allow_html=True)
            ai_name = st.text_input("Tên bài tập:", value="Bài tập thử nghiệm")
            ai1, ai2, ai3 = st.columns(3)
            with ai1: ai_classes = st.number_input("Số ca học hôm đó:", 0, 4, 2)
            with ai2: ai_free    = st.number_input("Giờ rảnh còn lại (h):", 0.5, 48.0, 6.0, step=0.5)
            with ai3: ai_load    = st.number_input("Khối lượng cần làm (h):", 0.5, 20.0, 4.0, step=0.5)
            r = deadline_ml.predict_deadline_risk(ai_name, int(ai_classes), ai_free, ai_load)
            st.metric("Xác suất trễ hạn", f"{r['risk_percentage']}%", delta=r['warning_level'], delta_color="inverse")
            if r["risk_percentage"] >= 70:   st.error(r["warning_message"])
            elif r["risk_percentage"] >= 40: st.warning(r["warning_message"])
            else:                            st.success(r["warning_message"])
            st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CHU KỲ SINH LÝ
# ══════════════════════════════════════════════════════════════════════════════
elif selected_nav == "🌸 Chu Kỳ":
    pred = get_cached_cycle_prediction()

    # ── Header row ──
    col_ck_main, col_ck_cat = st.columns([2.5, 1])
    with col_ck_main:
        st.subheader("🌸 Theo Dõi & AI Dự Đoán Chu Kỳ Kinh Nguyệt")
        st.markdown('<p class="hint-text">Hệ thống AI thích ứng học cơ địa riêng của em để dự đoán ngày đèn đỏ, ngày rụng trứng và nhắc nhở 2 chiều.</p>', unsafe_allow_html=True)

        # Banner trạng thái trong cột chính
        if pred.get("has_data"):
            days_left = pred["days_left"]
            if days_left <= 0:
                st.error(f"💖 Hôm nay hoặc đã qua ngày dự kiến kỳ mới ({pred['predicted_next_date']}). Em nhớ cập nhật nhé!")
            elif days_left <= 3:
                st.warning(f"🌸 **PMS!** Còn **{days_left} ngày** đến kỳ mới ({pred['predicted_next_date']}). Giữ ấm bụng, uống nước ấm nhé! 🍵")
            elif days_left <= 4:
                st.warning(f"🌸 Sắp vào PMS! Còn **{days_left} ngày** đến kỳ mới ({pred['predicted_next_date']}). Chuẩn bị đồ dùng trước nhé!")
            else:
                st.success(f"✨ Bình thường — Còn **{days_left} ngày** đến chu kỳ tiếp theo ({pred['predicted_next_date']})")
        else:
            st.info("👋 Chưa có dữ liệu. Hãy bấm nút bên dưới để bắt đầu theo dõi!")

    with col_ck_cat:
        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        if pred.get("has_data") and pred.get("days_left", 99) <= 3:
            render_cat("worry_cat.jpg", "Ổn không bé iu? 🙀💕", width=160)
        else:
            render_cat("chating_cat.jpg", "Quan tâm bé iu từng chút một 🌸🐱", width=160)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns([1.3, 1])

    with col_a:
        st.markdown("""<div class="card">
            <div class="section-title">💖 Ghi Nhận Chu Kỳ Mới</div>
            <p style="font-size:.92rem;color:#555;margin-bottom:12px;">
            Mỗi lần bắt đầu kỳ mới, em chỉ cần bấm 1 nút. AI sẽ tự học cơ địa riêng của em!
            </p>
        </div>""", unsafe_allow_html=True)

        if st.button("💖 HÔM NAY BẮT ĐẦU KỲ MỚI", use_container_width=True, type="primary"):
            database.add_menstrual_record(date.today().strftime("%Y-%m-%d"))
            menstrual_ml.retrain_model()
            invalidate_cache()
            st.balloons()
            st.success("Đã ghi nhận! AI đã cập nhật cơ địa của em.")
            st.rerun()

        st.markdown('<p class="hint-text">Hoặc chọn ngày khác nếu quên ghi:</p>', unsafe_allow_html=True)
        with st.expander("📅 Chọn ngày bắt đầu khác"):
            cus_d   = st.date_input("Ngày bắt đầu thực tế:", value=date.today())
            cus_len = st.number_input("Độ dài chu kỳ lần này (ngày):", 21, 45, 28)
            if st.button("Lưu ngày này", use_container_width=True):
                database.add_menstrual_record(cus_d.strftime("%Y-%m-%d"), cycle_length=int(cus_len))
                menstrual_ml.retrain_model()
                invalidate_cache()
                st.success("Đã lưu và cập nhật AI!")
                st.rerun()

        if pred.get("has_data"):
            col_pi, col_pc = st.columns([2.5, 1.1])
            with col_pi:
                ovul_val   = pred.get("ovulation_date","Chưa rõ")
                fertile_val= pred.get("fertile_window",{}).get("text","Chưa rõ") if pred.get("fertile_window") else "Chưa rõ"
                algo_val   = pred.get("algorithm_used","Medical Baseline")
                st.markdown(f"""<div class="preview-box">
                    <b>🔮 AI Dự Đoán Cơ Địa Của Em:</b><br>
                    • Chu kỳ: <b>{pred['cycle_length']} ngày</b> (học từ {pred['history_count']} lần)<br>
                    • Thuật toán: <b>{algo_val}</b><br>
                    • Kỳ gần nhất: <b>{pred['latest_start_date']}</b> &nbsp;|&nbsp; Tiếp theo: <b>{pred['predicted_start_date']}</b><br>
                    • Ngày rụng trứng: <b>{ovul_val}</b><br>
                    • Cửa sổ thụ thai: <b>{fertile_val}</b><br>
                    • PMS bắt đầu: <b>{pred['pms_start_date']}</b> (còn {pred['days_remaining']} ngày)
                </div>""", unsafe_allow_html=True)
            with col_pc:
                st.markdown('<div class="cat-card">', unsafe_allow_html=True)
                render_cat("chating_cat.jpg","Đang tính... 👀", width=130)
                st.markdown('</div>', unsafe_allow_html=True)
            with st.expander("💌 Lời Khuyên Sức Khỏe Hôm Nay Cho Em"):
                st.info(pred.get("advice_for_her",""))

    with col_b:
        st.markdown("""<div class="card">
            <div class="section-title">🍓 Cơ Chế Thông Báo Kép</div>
            <p style="font-size:.9rem;color:#555;line-height:1.7;">
            <b>🌸 Nhắn cho Em (Telegram):</b><br>
            — Trước 3 ngày: Nhắc giữ ấm bụng, uống nước ấm<br>
            — Đúng ngày dự kiến: Nhắc chuẩn bị đồ dùng<br><br>
            <b>🍓 Nhắn BÍ MẬT cho Bạn:</b><br>
            — Trước 4 ngày: Bot tự nhắn riêng để nhường nhịn, chuẩn bị trà ấm!
            </p>
        </div>""", unsafe_allow_html=True)

        if pred.get("has_data"):
            with st.expander("🍓 [SECRET MODE] Lời Khuyên Bí Mật Cho Bạn", expanded=True):
                st.warning(pred.get("secret_advice_for_you",""))

        if st.button("🔄 Huấn Luyện Lại AI (Retrain)", use_container_width=True):
            menstrual_ml.retrain_model()
            invalidate_cache()
            st.success("AI đã được cập nhật theo thuật toán 3 lớp!")

    # ── Lịch sử ──
    st.divider()
    st.markdown("#### 📜 Lịch Sử Chu Kỳ Đã Ghi Nhận")
    records = get_cached_menstrual_records()
    if records:
        df_m = pd.DataFrame(records)[["id","start_date","cycle_length","period_length","notes"]]
        df_m.columns = ["ID","Ngày Bắt Đầu","Độ Dài CK (ngày)","Số Ngày Đèn Đỏ","Ghi Chú"]
        st.dataframe(df_m, use_container_width=True, hide_index=True)
        with st.expander("🗑️ Xóa bản ghi nhập nhầm"):
            del_ids  = [r["id"] for r in records]
            del_m_id = st.selectbox("Chọn ID cần xóa:", del_ids,
                format_func=lambda x: f"ID {x}: {next(r['start_date'] for r in records if r['id']==x)}")
            if st.button("Xóa bản ghi này", type="primary"):
                database.delete_menstrual_record(del_m_id)
                menstrual_ml.retrain_model()
                invalidate_cache()
                st.success("Đã xóa!")
                st.rerun()
    else:
        st.caption("Chưa có bản ghi nào.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — LỊCH UỐNG THUỐC & OCR
# ══════════════════════════════════════════════════════════════════════════════
elif selected_nav == "💊 Đơn Thuốc":
    today_str_m  = date.today().strftime("%Y-%m-%d")
    today_meds   = get_cached_today_meds(today_str_m)
    total_h      = len(today_meds)
    taken_h      = sum(1 for m in today_meds if m["taken"]) if today_meds else 0

    col_med_main, col_med_cat = st.columns([2.5, 1])
    with col_med_main:
        st.subheader("💊 Nhắc Lịch Uống Thuốc & Đọc Đơn Thuốc Bằng Ảnh")
        st.markdown('<p class="hint-text">Theo dõi lịch uống thuốc, quét đơn bằng AI và nhận nhắc nhở đúng giờ qua Telegram.</p>', unsafe_allow_html=True)
    with col_med_cat:
        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        if today_meds and taken_h == total_h:
            render_cat("smile-cat.png", "Uống đủ thuốc rồi! Bé ngoan! 😸💊", width=160)
        else:
            render_cat("doctor-cat.png", "Bác sĩ Meow nhắc nhớ uống thuốc! 🩺💊", width=160)
        st.markdown('</div>', unsafe_allow_html=True)

    med_t1, med_t2, med_t3 = st.tabs(["🔔 Lịch Hôm Nay", "➕ Thêm Lịch Thuốc", "📋 Danh Sách Thuốc"])

    # ── Lịch hôm nay ──
    with med_t1:
        if not today_meds:
            c_info, c_dc = st.columns([2.2, 1])
            with c_info:
                st.markdown("""<div class="card" style="padding:24px;">
                    <div class="section-title">😊 Hôm nay trống lịch thuốc!</div>
                    <p style="font-size:.93rem;color:#555;line-height:1.75;">
                    💖 Hôm nay em không có lịch uống thuốc nào.<br>
                    Mong em luôn khỏe mạnh và tràn đầy năng lượng! 🌸<br><br>
                    Nếu cần thêm thuốc mới, bấm tab <b>➕ Thêm Lịch Thuốc</b> hoặc dùng OCR đọc đơn thuốc bằng ảnh nhé!
                    </p>
                </div>""", unsafe_allow_html=True)
            with c_dc:
                st.markdown('<div class="cat-card">', unsafe_allow_html=True)
                render_cat("doctor-cat.png","Không có thuốc hôm nay, em khỏe rồi! 🩺😺", width=160)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            total       = len(today_meds)
            taken_count = sum(1 for m in today_meds if m["taken"])
            prog_col, mc_col = st.columns([2.2, 1])
            with prog_col:
                st.progress(taken_count/total, text=f"Đã uống {taken_count}/{total} liều hôm nay")
                if taken_count == total:
                    st.success("🎉 Tuyệt vời! Em đã uống đủ thuốc hôm nay rồi! Bé giỏi lắm! 🌸")
            with mc_col:
                st.markdown('<div class="cat-card">', unsafe_allow_html=True)
                if taken_count == total:
                    render_cat("smile-cat.png","Uống đủ rồi! Bé ngoan! 😸💊", width=130)
                else:
                    render_cat("doctor-cat.png",f"Còn {total-taken_count} liều nữa nha! 🩺", width=130)
                st.markdown('</div>', unsafe_allow_html=True)

            for item in today_meds:
                icon       = "✅" if item["taken"] else "⏳"
                badge      = "badge-safe" if item["taken"] else "badge-warn"
                status_txt = "Đã uống" if item["taken"] else "Chưa uống"
                with st.container():
                    st.markdown(f"""<div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                          <span style="font-weight:700;">{icon} {item['medicine_name']} — {item['time_slot']}</span>
                          <span class="{badge}">{status_txt}</span>
                        </div>
                        <div style="color:#666;font-size:.9rem;margin:5px 0;">
                          💊 Liều: <b>{item['dosage']}</b> &nbsp;|&nbsp; 📅 Ngày {item['day_number']}/{item['total_days']}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if not item["taken"]:
                        c_take, c_test = st.columns([3, 2])
                        with c_take:
                            if st.button(f"✅ Đánh dấu Đã uống lúc {item['time_slot']}",
                                         key=f"take_{item['medicine_id']}_{item['time_slot']}",
                                         use_container_width=True):
                                database.log_medicine_taken(item["medicine_id"], today_str_m, item["time_slot"])
                                invalidate_cache()
                                st.success("Bé giỏi quá! 🌸")
                                st.rerun()
                        with c_test:
                            if st.button(f"📲 Test nhắc Telegram",
                                         key=f"test_{item['medicine_id']}_{item['time_slot']}",
                                         use_container_width=True):
                                msg = (
                                    f"💊 <b>[TEST NHẮC UỐNG THUỐC]</b> 🌸\n\n"
                                    f"🏷️ Tên thuốc: <b>{item['medicine_name']}</b>\n"
                                    f"🥄 Liều lượng: <b>{item['dosage']}</b>\n"
                                    f"🕒 Khung giờ: <b>{item['time_slot']}</b> (Ngày {item['day_number']}/{item['total_days']})\n\n"
                                    f"<i>Uống đúng giờ để mau khỏe nha cô bé! 🍵</i>"
                                )
                                res = notifier.notify_her(msg, photo_path=item.get("image_path"))
                                st.success("✅ Đã gửi!") if res else st.error("❌ Gửi thất bại. Kiểm tra Bot Token & Chat ID!")

    # ── Thêm lịch thuốc ──
    with med_t2:
        form_med, tip_med = st.columns([2.2, 1])
        with form_med:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="hint-text">Nhập thông tin đơn thuốc. Tải ảnh lên để AI đọc tự động!</p>', unsafe_allow_html=True)
            ocr_data      = {"name":"","dosage":"1 viên (sau ăn)","times":"08:00, 19:30","days_count":5}
            saved_img_path= ""

            with st.expander("📷 Tải Ảnh Đơn Thuốc / Vỏ Thuốc (AI đọc tự động)"):
                uploaded = st.file_uploader("Chọn ảnh:", type=["jpg","jpeg","png"])
                if uploaded:
                    ci, cr = st.columns(2)
                    with ci:
                        st.image(uploaded, caption="Ảnh đã tải lên", use_container_width=True)
                    fname  = f"med_{int(config.get_now().timestamp())}_{uploaded.name}"
                    fpath  = config.UPLOADS_DIR / fname
                    with open(fpath,"wb") as f: f.write(uploaded.getbuffer())
                    saved_img_path = str(fpath)
                    with cr:
                        if st.button("🔍 AI đọc ảnh & điền tự động", use_container_width=True):
                            with st.spinner("AI đang nhận diện..."):
                                ocr_data = medicine_ocr.process_medicine_image(saved_img_path)
                            st.success("Đã nhận diện! Kiểm tra lại thông tin bên dưới.")
                            if ocr_data.get("raw_text"):
                                with st.expander("Xem văn bản thô"):
                                     st.text(ocr_data["raw_text"])

            st.markdown('<span class="step-label">1</span> <b>Thông tin thuốc</b>', unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            with m1:
                med_name   = st.text_input("Tên thuốc (*)", value=ocr_data.get("name",""),
                    placeholder="VD: Panadol Extra 500mg, Vitamin C...")
            with m2:
                med_dosage = st.text_input("Liều lượng (*)", value=ocr_data.get("dosage","1 viên (sau ăn)"),
                    placeholder="VD: 1 viên sau ăn, 5ml pha nước ấm...")

            st.markdown('<span class="step-label">2</span> <b>Lịch uống trong ngày</b>', unsafe_allow_html=True)
            st.markdown('<p class="hint-text">Nhập các khung giờ cách nhau bởi dấu phẩy. VD: 08:00, 12:30, 20:00</p>', unsafe_allow_html=True)
            preset_col = st.columns(4)
            preset_val = ocr_data.get("times","08:00, 19:30")
            if preset_col[0].button("1 lần/ngày\n(Sáng)",  use_container_width=True): preset_val="08:00"
            if preset_col[1].button("2 lần/ngày\n(S+T)",   use_container_width=True): preset_val="08:00, 20:00"
            if preset_col[2].button("3 lần/ngày\n(S+T+T)", use_container_width=True): preset_val="08:00, 13:00, 20:00"
            if preset_col[3].button("4 lần/ngày",          use_container_width=True): preset_val="07:30, 12:00, 17:00, 21:00"
            med_times = st.text_input("Các khung giờ uống (*)", value=preset_val)

            st.markdown('<span class="step-label">3</span> <b>Thời gian điều trị</b>', unsafe_allow_html=True)
            m3, m4 = st.columns(2)
            with m3:
                med_days  = st.number_input("Uống trong bao nhiêu ngày (*)", 1, 60, int(ocr_data.get("days_count",5)))
            with m4:
                med_start = st.date_input("Ngày bắt đầu uống (*)", value=date.today())

            if med_name.strip():
                st.markdown(f"""<div class="preview-box">
                    <b>👁️ Xem trước lịch uống thuốc:</b><br>
                    💊 <b>{med_name}</b> — {med_dosage}<br>
                    🕒 Giờ uống: <b>{med_times}</b><br>
                    📅 Từ <b>{med_start.strftime('%d/%m/%Y')}</b> trong <b>{med_days} ngày</b> liên tiếp<br>
                    📬 Bot Telegram sẽ nhắc em đúng giờ kèm ảnh thuốc (nếu có)
                </div>""", unsafe_allow_html=True)

            if st.button("💊 Lưu Lịch Uống Thuốc Này", use_container_width=True, type="primary"):
                if not med_name.strip():
                    st.error("Chưa nhập tên thuốc!")
                else:
                    database.add_medicine(med_name.strip(), med_dosage.strip(), med_times.strip(),
                                          int(med_days), med_start.strftime("%Y-%m-%d"), saved_img_path)
                    invalidate_cache()
                    st.success(f"✅ Đã lưu lịch uống '{med_name}'! Bot sẽ nhắc đúng giờ.")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        with tip_med:
            st.markdown('<div class="cat-card">', unsafe_allow_html=True)
            render_cat("doctor-cat.png", "Bác sĩ Meow luôn nhắc uống đúng giờ! 🩺💖", width=160)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("""<div class="card" style="margin-top:12px;">
                <div class="section-title">💊 Lưu ý khi dùng thuốc</div>
                <div style="font-size:.85rem;line-height:1.75;color:#555;">
                🕒 Uống đúng giờ để đảm bảo hiệu quả điều trị.<br><br>
                🍽️ Thuốc sau ăn: Uống sau khi ăn no 30 phút.<br><br>
                💧 Uống với đủ nước, không nằm ngay sau uống.<br><br>
                📸 Tải ảnh đơn thuốc để AI đọc tự động và điền tên thuốc!
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Danh sách thuốc ──
    with med_t3:
        all_meds = get_cached_medicines()
        if not all_meds:
            st.info("Chưa có thuốc nào được thêm.")
        else:
            for m in all_meds:
                end_date = datetime.strptime(m["start_date"],"%Y-%m-%d").date() + timedelta(days=m["days_count"])
                is_active = date.today() <= end_date and m["active"]
                badge = "badge-safe" if is_active else "badge-danger"
                label = "Đang điều trị" if is_active else "Đã kết thúc"
                st.markdown(f"""<div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                      <b>💊 {m['name']}</b>
                      <span class="{badge}">{label}</span>
                    </div>
                    <div style="color:#666;font-size:.9rem;margin-top:5px;">
                      Liều: {m['dosage']} &nbsp;|&nbsp; Giờ: {m['times']} &nbsp;|&nbsp; {m['days_count']} ngày từ {m['start_date']}
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"🗑️ Xóa '{m['name']}'", key=f"del_med_{m['id']}"):
                    database.delete_medicine(m["id"])
                    invalidate_cache()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB NHẬT KÝ & CẢM XÚC (MOOD TRACKER & 365 DAYS OF MOOD MATRIX)
# ══════════════════════════════════════════════════════════════════════════════
elif selected_nav in ["📖 Cảm Xúc", "📖 Nhật Ký"]:
    import calendar as _cal
    from collections import Counter

    # ─── MOOD CONSTANTS ───
    MOOD_OPTIONS = [
        ("Happy",    "😄 Vui vẻ",      "#A8E6CF", "smile-cat.png",   "😄"),
        ("Normal",   "🙂 Bình thường",  "#FFD3B6", "smile-cat.png",   "🙂"),
        ("Stressed", "😫 Stress",       "#D4A5FF", "burnOut_cat.jpg", "😫"),
        ("Sad",      "😔 Buồn",         "#A8D8EA", "cry-cat.jpg",     "😔"),
        ("Angry",    "😡 Bực bội",      "#FF8B94", "worry_cat.jpg",   "😡"),
        ("Tired",    "😴 Mệt mỏi",      "#DCD6F7", "huh-cat.jpg",     "😴"),
    ]
    MOOD_KEY_MAP = {k: (label, bg, cat, icon) for k, label, bg, cat, icon in MOOD_OPTIONS}
    MOOD_LABELS  = [label for _, label, *_ in MOOD_OPTIONS]
    MOOD_KEYS    = [k     for k, *_ in MOOD_OPTIONS]
    MOOD_COLORS  = {k: (bg, icon) for k, _, bg, _, icon in MOOD_OPTIONS}
    EMPTY_COLOR  = "#F3F4F6"

    AI_RESP_MAP = {
        "Happy":    "Tuyệt vời quá! Chúc em luôn giữ nụ cười tươi tắn này nhé! Mèo yêu em nhiều 🥰🌸",
        "Normal":   "Một ngày bình yên trôi qua cũng là điều tuyệt vời! Cứ từ từ tận hưởng nhé em 🌸",
        "Stressed": "Đừng quá sức nhé em bé! Nghỉ ngơi một chút, uống nước ấm và để Bác sĩ Mèo ôm cái nào 💖",
        "Sad":      "Thương em lắm! Có anh và Bác sĩ Mèo luôn ở bên cạnh em, mọi chuyện rồi sẽ ổn thôi 💫🧸",
        "Angry":    "Hít thở sâu một cái nào cô bé! Đừng để chuyện bực mình làm ảnh hưởng đến sức khỏe và nụ cười xinh nhé 🍵💖",
        "Tired":    "Hôm nay em vất vả nhiều rồi! Mau đi ngủ sớm sạc lại năng lượng nhé, ngoan nào 😴🛌🌙",
    }

    # ─── CSS RIÊNG CHO MODULE CẢM XÚC ───
    st.markdown("""
    <style>
    .cat-speech-bubble {
        background: #fff8fc;
        border-radius: 16px 16px 16px 4px;
        padding: 13px 16px;
        margin-top: 12px;
        border: 1.5px solid #ffd6e7;
        font-size: 0.86rem;
        color: #c0397c;
        line-height: 1.65;
        font-style: italic;
        position: relative;
    }
    .cat-speech-bubble::before {
        content: "";
        position: absolute;
        top: -10px; left: 18px;
        border: 5px solid transparent;
        border-bottom-color: #ffd6e7;
    }
    .mood-cal-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
        margin-top: 10px;
    }
    .mood-cal-container.is-single-month {
        max-width: 520px;
        margin-left: auto;
        margin-right: auto;
    }
    .mini-cal {
        background: #ffffff;
        border-radius: 12px;
        padding: 10px 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        border: 1px solid #f0f0f5;
    }
    .mini-cal-title {
        font-weight: 700;
        font-size: 0.88rem;
        color: #d81159;
        text-align: center;
        margin-bottom: 6px;
    }
    .mini-cal-header {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        text-align: center;
        font-size: 0.68rem;
        font-weight: 700;
        color: #999;
        margin-bottom: 4px;
    }
    .mini-cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 3px;
    }
    .mcell {
        aspect-ratio: 1;
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        user-select: none;
        min-height: 28px;
        border: 1px solid rgba(0,0,0,0.03);
    }
    .mcell:hover {
        transform: scale(1.15);
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        z-index: 5;
    }
    .mcell.is-today {
        box-shadow: 0 0 0 2px #d81159 !important;
    }
    .mcell .mcell-num {
        font-size: 0.64rem;
        font-weight: 700;
        line-height: 1;
    }
    .mcell .mcell-icon {
        font-size: 0.72rem;
        line-height: 1;
        margin-top: 1px;
    }
    .mcell .mtt {
        display: none;
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1a2e;
        color: #ffffff;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 0.7rem;
        white-space: nowrap;
        z-index: 999;
        pointer-events: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.22);
        min-width: 120px;
        text-align: center;
    }
    .mcell:hover .mtt {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    today_diary = config.get_now().date()
    today_str_d = today_diary.strftime("%Y-%m-%d")

    # Session states
    if "mood_sel_mood" not in st.session_state:
        st.session_state["mood_sel_mood"] = "Happy"
    if "mood_view_year" not in st.session_state:
        st.session_state["mood_view_year"] = today_diary.year
    if "mood_view_month" not in st.session_state:
        st.session_state["mood_view_month"] = today_diary.month
    if "mood_view_mode" not in st.session_state:
        st.session_state["mood_view_mode"] = "single"  # 'single' hoặc 'full_year'

    # ══════════════════════════════════════════════════════
    # ZONE 1: FORM CẬP NHẬT CẢM XÚC SIÊU TỐC  [2.5 : 1]
    # ══════════════════════════════════════════════════════
    col_form, col_cat_display = st.columns([2.5, 1], gap="medium")

    with col_form:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌸 Cập Nhật Cảm Xúc Nhanh (3s)</div>', unsafe_allow_html=True)

        # 1. Chọn ngày (Mặc định hôm nay, có thể chọn quá khứ để điền bù)
        c_date, c_quick_mood = st.columns([1.2, 2.8])
        with c_date:
            chosen_date = st.date_input(
                "📅 Ngày ghi nhận",
                value=today_diary,
                max_value=today_diary,
                key="diary_date_pick",
                help="Mặc định là hôm nay; có thể chọn ngày quá khứ để điền bù",
            )
            chosen_date_str = chosen_date.strftime("%Y-%m-%d")

        # 2. Chọn cảm xúc (1-Click Emoji Selection)
        mood_radio_val = st.radio(
            "🟡 Tâm trạng của em hôm nay:",
            options=MOOD_LABELS,
            index=MOOD_KEYS.index(st.session_state.get("mood_sel_mood", "Happy")),
            horizontal=True,
            key="diary_mood_radio",
        )
        sel_idx = MOOD_LABELS.index(mood_radio_val)
        sel_mood_key = MOOD_KEYS[sel_idx]
        st.session_state["mood_sel_mood"] = sel_mood_key

        # 3. Ghi chú ngắn
        mood_note_val = st.text_input(
            "📝 Ghi chú tâm sự (không bắt buộc):",
            placeholder="Hôm nay có điều gì làm em vui hay mệt mỏi không? Kể Bác sĩ Mèo nghe nhé...",
            key="diary_note",
        )

        # 4. Nút lưu
        save_btn_col, _ = st.columns([1.3, 2])
        with save_btn_col:
            save_clicked = st.button(
                "💖 Lưu Cảm Xúc",
                use_container_width=True,
                type="primary",
                key="diary_save_btn",
            )

        if save_clicked:
            ai_resp_val = AI_RESP_MAP.get(sel_mood_key, "Thương em nhiều! 💖")
            note_clean  = mood_note_val.strip() if mood_note_val.strip() else None
            try:
                database.upsert_mood_log(
                    date_str    = chosen_date_str,
                    mood_type   = sel_mood_key,
                    note        = note_clean,
                    ai_response = ai_resp_val,
                )
                st.success(f"✅ Đã ghi nhận cảm xúc **{mood_radio_val}** ngày {chosen_date_str}!")
                invalidate_cache()

                # 🤫 Secret Boy Mode: Nếu bạn gái buồn / stress / bực / mệt mỏi
                if sel_mood_key in ["Sad", "Stressed", "Angry", "Tired"]:
                    try:
                        _lbl = MOOD_KEY_MAP[sel_mood_key][0]
                        _note_txt = note_clean if note_clean else "Không có ghi chú"
                        notifier.notify_you_secret(
                            f"🤫 <b>[CẢNH BÁO TÂM LÝ BÍ MẬT]</b>\n\n"
                            f"Bạn gái vừa cập nhật cảm xúc: <b>{_lbl}</b> trên App.\n"
                            f"📝 <b>Ghi chú:</b> {_note_txt}\n\n"
                            f"👉 <i>Hãy nhắn tin hỏi thăm, động viên và chuẩn bị đồ ăn ngon cho cô ấy nhé! 🍫🧸💖</i>"
                        )
                    except Exception:
                        pass
                st.rerun()
            except Exception as e_save:
                st.error(f"❌ Lỗi khi lưu: {e_save}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_cat_display:
        _cur_mood_key = st.session_state["mood_sel_mood"]
        _mood_info    = MOOD_KEY_MAP.get(_cur_mood_key, MOOD_KEY_MAP["Happy"])
        _cat_label, _bg_color, _cat_file, _cat_icon = _mood_info
        _ai_msg       = AI_RESP_MAP.get(_cur_mood_key, "💖")

        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        render_cat(_cat_file, f"Bác sĩ Mèo đang lắng nghe {_cat_icon}", width=160)
        st.markdown(f"""
        <div class="cat-speech-bubble">
            🐱 {_ai_msg}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # ZONE 2: MA TRẬN LỊCH CẢM XÚC (MOOD CALENDAR MATRIX)
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="card" style="margin-top:18px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗓️ Lịch Theo Dõi Cảm Xúc (Mood Calendar Matrix)</div>', unsafe_allow_html=True)

    # Bộ điều khiển: Chọn Tháng, Năm, hoặc Cả năm
    ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([1.6, 1.4, 2.2, 1.8], vertical_alignment="center")

    VN_MONTH_NAME = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
                         "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]

    with ctrl_c1:
        # Chọn năm
        cur_yr = today_diary.year
        avail_years = list(range(cur_yr - 3, cur_yr + 2))
        sel_year = st.selectbox(
            "📅 Năm",
            options=avail_years,
            index=avail_years.index(st.session_state["mood_view_year"]) if st.session_state["mood_view_year"] in avail_years else 3,
            key="mood_sel_year_box",
            label_visibility="collapsed",
        )
        st.session_state["mood_view_year"] = sel_year

    with ctrl_c2:
        # Chế độ xem: 1 tháng hay Cả năm
        mode_label = "📆 Theo Tháng" if st.session_state["mood_view_mode"] == "single" else "🗓️ Cả Năm (12 Tháng)"
        mode_pick = st.selectbox(
            "Chế độ xem",
            options=["📆 Theo Tháng", "🗓️ Cả Năm (12 Tháng)"],
            index=0 if st.session_state["mood_view_mode"] == "single" else 1,
            key="mood_mode_selectbox",
            label_visibility="collapsed",
        )
        st.session_state["mood_view_mode"] = "single" if mode_pick == "📆 Theo Tháng" else "full_year"

    with ctrl_c3:
        if st.session_state["mood_view_mode"] == "single":
            sel_month = st.selectbox(
                "Chọn tháng",
                options=list(range(1, 13)),
                format_func=lambda m: f"{VN_MONTH_NAME[m]} / {st.session_state['mood_view_year']}",
                index=st.session_state["mood_view_month"] - 1,
                key="mood_sel_month_box",
                label_visibility="collapsed",
            )
            st.session_state["mood_view_month"] = sel_month
        else:
            st.markdown(f"<div style='font-weight:700;color:#d81159;padding-top:6px;'>🌈 365 Days of Mood — Năm {st.session_state['mood_view_year']}</div>", unsafe_allow_html=True)

    with ctrl_c4:
        if st.session_state["mood_view_mode"] == "single":
            btn_prev, btn_now, btn_next = st.columns(3)
            with btn_prev:
                if st.button("◀", key="mood_prev_m", help="Tháng trước", use_container_width=True):
                    m = st.session_state["mood_view_month"] - 1
                    if m < 1:
                        st.session_state["mood_view_month"] = 12
                        st.session_state["mood_view_year"] -= 1
                    else:
                        st.session_state["mood_view_month"] = m
                    st.rerun()
            with btn_now:
                if st.button("Nay", key="mood_cur_m", help="Tháng hiện tại", use_container_width=True):
                    st.session_state["mood_view_year"] = today_diary.year
                    st.session_state["mood_view_month"] = today_diary.month
                    st.rerun()
            with btn_next:
                if st.button("▶", key="mood_next_m", help="Tháng sau", use_container_width=True):
                    m = st.session_state["mood_view_month"] + 1
                    if m > 12:
                        st.session_state["mood_view_month"] = 1
                        st.session_state["mood_view_year"] += 1
                    else:
                        st.session_state["mood_view_month"] = m
                    st.rerun()

    view_year = st.session_state["mood_view_year"]
    view_mode = st.session_state["mood_view_mode"]

    if view_mode == "single":
        months_to_render = [st.session_state["mood_view_month"]]
    else:
        months_to_render = list(range(1, 13))

    # Query toàn bộ dữ liệu mood cho năm được chọn (1 lần duy nhất, có cache)
    yr_start = f"{view_year}-01-01"
    yr_end   = f"{view_year}-12-31"
    mood_rows_yr = get_cached_mood_range(yr_start, yr_end)
    mood_map_yr  = {r["date"]: r for r in mood_rows_yr}

    DAY_HEADERS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

    # ── Build HTML cho tất cả mini-calendar tháng ──
    cal_cls = "mood-cal-container is-single-month" if view_mode == "single" else "mood-cal-container"
    full_html = f'<div class="{cal_cls}">'

    for m in months_to_render:
        first_dow = date(view_year, m, 1).weekday()  # 0=Mon
        days_in   = _cal.monthrange(view_year, m)[1]

        month_html  = '<div class="mini-cal">'
        month_html += f'<div class="mini-cal-title">{VN_MONTH_NAME[m]} {view_year}</div>'

        # Header ngày trong tuần
        month_html += '<div class="mini-cal-header">'
        for dh in DAY_HEADERS:
            month_html += f'<span>{dh}</span>'
        month_html += '</div>'

        # Lưới ô ngày
        month_html += '<div class="mini-cal-grid">'

        # Ô trống đầu tháng
        for _ in range(first_dow):
            month_html += '<div class="mcell" style="background:transparent;border:none;"></div>'

        # Ô cho mỗi ngày trong tháng
        for day in range(1, days_in + 1):
            ds = f"{view_year}-{m:02d}-{day:02d}"
            d_obj = date(view_year, m, day)
            rec = mood_map_yr.get(ds)

            is_today = (d_obj == today_diary)
            today_cls = " is-today" if is_today else ""

            if rec:
                mk = rec.get("mood_type", "")
                bg, icon = MOOD_COLORS.get(mk, (EMPTY_COLOR, ""))
                _lbl = MOOD_KEY_MAP.get(mk, ("",))[0]
                _nt  = rec.get("note") or ""
                tooltip = f"{ds} — {_lbl}" + (f" — {_nt[:35]}" if _nt else "")
                month_html += (
                    f'<div class="mcell{today_cls}" style="background:{bg};">'
                    f'<span class="mcell-num">{day}</span>'
                    f'<span class="mcell-icon">{icon}</span>'
                    f'<span class="mtt">{tooltip}</span>'
                    f'</div>'
                )
            else:
                # Ô trống — chưa ghi cảm xúc (cho phép rỗng tự nhiên)
                tooltip = f"{ds} — Chưa ghi chép"
                future  = d_obj > today_diary
                cell_bg = "transparent" if future else EMPTY_COLOR
                num_color = "#ccc" if future else "#888"
                month_html += (
                    f'<div class="mcell{today_cls}" style="background:{cell_bg};">'
                    f'<span class="mcell-num" style="color:{num_color};">{day}</span>'
                    f'<span class="mtt">{tooltip}</span>'
                    f'</div>'
                )

        # Ô trống cuối tháng
        total_cells = first_dow + days_in
        remaining = (7 - total_cells % 7) % 7
        for _ in range(remaining):
            month_html += '<div class="mcell" style="background:transparent;border:none;"></div>'

        month_html += '</div>'  # .mini-cal-grid
        month_html += '</div>'  # .mini-cal
        full_html += month_html

    full_html += '</div>'  # .mood-cal-container

    st.markdown(full_html, unsafe_allow_html=True)

    # ── Chú thích màu sắc (Legend) ──
    _legend = '<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:16px;padding-top:10px;border-top:1px solid #f0f0f5;align-items:center;">'
    _legend += f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:16px;height:16px;border-radius:4px;background:{EMPTY_COLOR};border:1px solid #ddd;"></div><span style="font-size:.8rem;color:#777;">Chưa ghi chép (rỗng)</span></div>'
    for _mk, _lbl, _bg, _, _ic in MOOD_OPTIONS:
        _legend += f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:16px;height:16px;border-radius:4px;background:{_bg};border:1px solid rgba(0,0,0,.08);text-align:center;font-size:.7rem;line-height:16px;">{_ic}</div><span style="font-size:.8rem;color:#555;">{_lbl}</span></div>'
    _legend += '</div>'
    st.markdown(_legend, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # .card

    # ══════════════════════════════════════════════════════
    # ZONE 3: XEM CHI TIẾT NHẬT KÝ THEO NGÀY
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📌 Xem Chi Tiết Nhật Ký Ngày</div>', unsafe_allow_html=True)
    _dc_col, _ = st.columns([1.4, 3])
    with _dc_col:
        _detail_date = st.date_input(
            "Chọn ngày",
            value=today_diary,
            key="diary_detail_pick",
            label_visibility="collapsed",
        )
    _ds = _detail_date.strftime("%Y-%m-%d")
    _drec = mood_map_yr.get(_ds) or database.get_mood_log_by_date(_ds)
    if _drec:
        _mk2 = _drec.get("mood_type", "")
        _bg2, _icon2 = MOOD_COLORS.get(_mk2, (EMPTY_COLOR, "⚪"))
        _lbl2 = MOOD_KEY_MAP.get(_mk2, ("⚪","","",""))[0]
        _note2 = _drec.get("note") or "—"
        _upd2 = _drec.get("updated_at") or ""
        _ai2  = _drec.get("ai_response") or ""
        st.markdown(f"""
        <div style="background:{_bg2};border-radius:14px;padding:18px 22px;
                    display:flex;gap:20px;align-items:flex-start;">
            <div style="font-size:2.5rem;margin-top:2px;">{_icon2}</div>
            <div>
                <div style="font-weight:700;font-size:1.05rem;color:#333;">{_ds}</div>
                <div style="font-size:.9rem;color:#555;margin:4px 0;">Cảm xúc: <b>{_lbl2}</b></div>
                <div style="font-size:.86rem;color:#777;">Ghi chú: <i>{_note2}</i></div>
                {f'<div style="font-size:.84rem;color:#b05c8a;margin-top:6px;">🐱 {_ai2}</div>' if _ai2 else ""}
                <div style="font-size:.72rem;color:#aaa;margin-top:6px;">Cập nhật: {_upd2}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"⚪ Chưa có ghi chép cảm xúc nào cho ngày **{_ds}**.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # ZONE 4: THỐNG KÊ CẢM XÚC TRONG NĂM
    # ══════════════════════════════════════════════════════
    if mood_rows_yr:
        st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📊 Thống Kê Cảm Xúc Năm {view_year}</div>', unsafe_allow_html=True)
        _counts = Counter(r["mood_type"] for r in mood_rows_yr)
        _total  = len(mood_rows_yr)
        stat_html = '<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;">'
        for _mk, _lbl, _bg, _, _ic in MOOD_OPTIONS:
            _c = _counts.get(_mk, 0)
            _pct = round(_c / _total * 100, 1) if _total else 0
            stat_html += f'''
            <div style="background:{_bg};border-radius:12px;padding:12px 18px;min-width:120px;text-align:center;
                        border:1px solid rgba(0,0,0,.06);">
                <div style="font-size:1.5rem;">{_ic}</div>
                <div style="font-weight:700;font-size:1.1rem;color:#333;">{_c} ngày</div>
                <div style="font-size:.78rem;color:#666;">{_lbl}</div>
                <div style="font-size:.72rem;color:#999;">{_pct}%</div>
            </div>'''
        stat_html += f'''
        <div style="background:{EMPTY_COLOR};border-radius:12px;padding:12px 18px;min-width:120px;text-align:center;
                    border:1px solid rgba(0,0,0,.06);">
            <div style="font-size:1.5rem;">📋</div>
            <div style="font-weight:700;font-size:1.1rem;color:#333;">{_total} ngày</div>
            <div style="font-size:.78rem;color:#666;">Tổng đã ghi</div>
        </div>'''
        stat_html += '</div>'
        st.markdown(stat_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CÀI ĐẶT & TELEGRAM BOT
# ══════════════════════════════════════════════════════════════════════════════

elif selected_nav == "⚙️ Cài Đặt":
    col_cfg_main, col_cfg_cat = st.columns([2.5, 1])
    with col_cfg_main:
        st.subheader("⚙️ Cấu Hình Telegram Bot & Thông Báo")
        st.markdown('<p class="hint-text">Thiết lập kết nối Telegram Cloud 24/7 để Bot tự động gửi lời yêu thương và nhắc nhở đúng giờ.</p>', unsafe_allow_html=True)
    with col_cfg_cat:
        st.markdown('<div class="cat-card">', unsafe_allow_html=True)
        render_cat("chating_cat.jpg", "Bot luôn sẵn sàng trò chuyện! 🐱💬", width=160)
        st.markdown('</div>', unsafe_allow_html=True)

    cur = get_cached_settings()

    st.markdown("""<div class="card">
        <div class="section-title">📋 Hướng dẫn nhanh lấy Bot Token & Chat ID (chỉ 3 phút)</div>
        <div style="font-size:.91rem;line-height:1.75;">
        <b>Bước 1 — Tạo Bot Token:</b> Mở Telegram → tìm <b>@BotFather</b> → gửi <code>/newbot</code> → đặt tên bot → copy mã <b>HTTP API Token</b><br>
        <b>Bước 2 — Lấy Chat ID:</b> Tìm <b>@userinfobot</b> → bấm Start → bot trả về ID. Nhờ cô ấy làm tương tự để lấy ID của cô ấy.<br>
        <b>Bước 3 — Bấm Start với bot của bạn:</b> Cả hai cần vào bot và bấm <b>/start</b> một lần để bot được phép gửi tin.
        </div>
    </div>""", unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("#### 🤖 Telegram Bot")
        bot_token = st.text_input("Bot Token (*)",
            value=cur.get("telegram_bot_token",""),
            type="password", placeholder="VD: 7123456789:AAFxxx...")

        st.markdown("#### 💌 Chat ID")
        sc1, sc2 = st.columns(2)
        with sc1:
            her_chat   = st.text_input("Chat ID của Cô Ấy (*)",
                value=cur.get("telegram_her_chat_id",""), placeholder="VD: 987654321")
            her_name_v = st.text_input("Tên hiển thị của Cô Ấy",
                value=cur.get("her_name","Em bé 🌸"))
        with sc2:
            my_chat   = st.text_input("Chat ID của Bạn (Secret Mode)",
                value=cur.get("telegram_my_chat_id",""), placeholder="VD: 123456789")
            my_name_v = st.text_input("Tên hiển thị của Bạn",
                value=cur.get("my_name","Anh 💖"))

        secret_on = st.toggle("🍓 Kích hoạt Secret Mode",
            value=cur.get("secret_mode_enabled", True),
            help="Bot tự nhắn bí mật cho bạn trước 4 ngày chu kỳ của cô ấy")

        if st.form_submit_button("💾 Lưu Tất Cả Cài Đặt", use_container_width=True):
            cur.update({
                "telegram_bot_token":    bot_token.strip(),
                "telegram_her_chat_id":  her_chat.strip(),
                "telegram_my_chat_id":   my_chat.strip(),
                "her_name":              her_name_v.strip(),
                "my_name":               my_name_v.strip(),
                "secret_mode_enabled":   secret_on,
            })
            if config.save_settings(cur):
                invalidate_cache()
                st.success("✅ Đã lưu cấu hình!")
                st.rerun()

    st.divider()
    st.markdown("#### 🧪 Kiểm Tra Thông Báo Yêu Thương (Telegram)")
    tt1, tt2, tt3 = st.columns(3)
    with tt1:
        if st.button("📤 Gửi Test → Cô Ấy", use_container_width=True):
            res = notifier.notify_her("💖 Xin chào Em Bé! Trợ Lý Yêu Thương đang hoạt động và luôn ở bên em! 🌸")
            st.success("✅ Gửi thành công!") if res else st.error("❌ Gửi thất bại. Kiểm tra Bot Token & Chat ID, nhớ bấm /start!")
    with tt2:
        if st.button("🍓 Gửi Test Secret Mode", use_container_width=True):
            res2 = notifier.notify_you_secret("🍓 [SECRET MODE] Kênh bí mật hoạt động hoàn hảo!")
            st.success("✅ Secret Mode OK!") if res2 else st.error("❌ Thất bại. Kiểm tra Chat ID của Bạn!")
    with tt3:
        if st.button("🎉 Kích Hoạt Lời Chúc Mừng", use_container_width=True):
            cur2 = get_cached_settings()
            cur2["startup_greeting_sent"] = False
            config.save_settings(cur2)
            invalidate_cache()
            scheduler.check_and_send_startup_greeting()
            st.success("Đã bắn lời chúc ngọt ngào tới Cô Ấy!")

    tb1, tb2 = st.columns(2)
    with tb1:
        if st.button("☀️ Test Gửi Chào Buổi Sáng (7:00 AM)", use_container_width=True):
            morning_msg = scheduler.build_good_morning_message()
            res_m = notifier.notify_her(morning_msg)
            if res_m:
                st.success("✅ Đã gửi tin nhắn Chào Buổi Sáng tới Telegram của cô ấy!")
            else:
                st.error("❌ Gửi thất bại. Hãy kiểm tra cấu hình Bot Token & Chat ID!")
    with tb2:
        if st.button("🌙 Test Gửi Chúc Ngủ Ngon (22:30 PM - Theo Mood)", use_container_width=True):
            night_msg = scheduler.build_good_night_message()
            res_n = notifier.notify_her(night_msg)
            if res_n:
                st.success("✅ Đã gửi tin nhắn Chúc Ngủ Ngon (cá nhân hóa theo cảm xúc) tới Telegram của cô ấy!")
            else:
                st.error("❌ Gửi thất bại. Hãy kiểm tra cấu hình Bot Token & Chat ID!")

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-footer">
    Dự án <b>Trợ Lý Yêu Thương 💖</b> &nbsp;•&nbsp; Tự động đồng bộ Turso Cloud & Telegram 24/7 &nbsp;•&nbsp; Crafted with Love 🌸
</div>
""", unsafe_allow_html=True)
