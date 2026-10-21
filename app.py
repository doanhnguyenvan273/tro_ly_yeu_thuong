import streamlit as st
from datetime import datetime, date, timedelta, time
import pandas as pd
import os
import base64
import re

import config
import database
import deadline_ml
import menstrual_ml
import medicine_ocr
import notifier
import scheduler
import telegram_listener
import mascot_manager

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
def init_background_services(cache_key: str = "v2.3_fast_bot"):
    scheduler.start_scheduler()
    return True

init_background_services("v2.3_fast_bot")

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

/* ── Nền tổng thể phong cách Soft Pink Aesthetic ── */
.stApp {
    background: radial-gradient(circle at 85% 15%, #ffb6c9 0%, #ffd6e5 35%, #fff0f5 70%, #fff8fa 100%) !important;
    background-attachment: fixed !important;
}

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
    padding-top: 14px !important;
    padding-bottom: 3rem !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    overflow: visible !important;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 10px !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
}

/* ══════════════════════════════════════════════════════
   TOP APP BAR (iOS Pink Glass Header)
   ══════════════════════════════════════════════════════ */
.top-nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 18px;
    background: rgba(255, 255, 255, 0.82);
    border: 1.5px solid rgba(255, 255, 255, 0.95);
    border-radius: 24px;
    box-shadow: 0 8px 24px rgba(230, 73, 128, 0.08);
    margin-bottom: 12px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}
.top-nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.brand-heart-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f783ac 0%, #e64980 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    color: white;
    box-shadow: 0 4px 12px rgba(230, 73, 128, 0.28);
}
.brand-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #c2255c;
    letter-spacing: -0.2px;
}
.brand-her {
    font-size: 0.88rem;
    font-weight: 600;
    color: #e64980;
    margin-left: 4px;
}
.ios-circle-btn {
    text-decoration: none !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #e64980 !important;
    background: #ffffff !important;
    border: 1.5px solid rgba(255, 209, 220, 0.9) !important;
    padding: 6px 14px !important;
    border-radius: 20px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    box-shadow: 0 3px 10px rgba(230, 73, 128, 0.08) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.ios-circle-btn:hover {
    background: #fff0f5 !important;
    transform: translateY(-1px) scale(1.02) !important;
    box-shadow: 0 6px 16px rgba(230, 73, 128, 0.16) !important;
}

@media (max-width: 600px) {
    .top-nav-bar {
        padding: 8px 14px;
        border-radius: 20px;
    }
    .brand-title {
        font-size: 1rem;
    }
    .brand-heart-circle {
        width: 32px;
        height: 32px;
        font-size: 0.95rem;
    }
}

/* ══════════════════════════════════════════════════════
   MASCOT COMPANION BANNER (Banner Mèo Đồng Hành Tinh Gọn)
   ══════════════════════════════════════════════════════ */
.mascot-companion-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    background: linear-gradient(135deg, #fff7f9 0%, #fff0f3 100%);
    border: 1.5px solid #ffccd5;
    border-radius: 16px;
    padding: 11px 16px;
    margin-top: 4px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(255, 182, 193, 0.14);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mascot-companion-banner:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(255, 182, 193, 0.22);
}
.mascot-img-wrap {
    flex-shrink: 0;
    width: 60px;
    height: 60px;
    border-radius: 14px;
    overflow: hidden;
    background: #ffffff;
    border: 1.5px solid #ffb3c6;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(255, 117, 140, 0.15);
}
.mascot-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}
.mascot-speech-wrap {
    flex: 1;
    min-width: 0;
}
.mascot-header-line {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 2px;
}
.mascot-name {
    font-size: 0.93rem;
    font-weight: 700;
    color: #d81159;
}
.mascot-badge {
    font-size: 0.74rem;
    font-weight: 600;
    background: #ffe0e6;
    color: #d81159;
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid #ffccd5;
    white-space: nowrap;
}
.mascot-quote {
    font-size: 0.86rem;
    color: #444444;
    line-height: 1.45;
}
@media (max-width: 600px) {
    .mascot-companion-banner {
        padding: 9px 12px;
        gap: 11px;
    }
    .mascot-img-wrap {
        width: 50px;
        height: 50px;
        border-radius: 12px;
    }
    .mascot-name {
        font-size: 0.86rem;
    }
    .mascot-quote {
        font-size: 0.8rem;
    }
}

/* ══════════════════════════════════════════════════════
   HORIZONTAL PILL NAVIGATION (Vuốt chạm mượt mà trên Mobile & Desktop)
   ══════════════════════════════════════════════════════ */
div[data-testid="stRadio"] {
    margin-bottom: 14px !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    justify-content: flex-start !important;
    align-items: center !important;
    gap: 6px !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: none !important;
    padding: 4px 2px !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar {
    display: none !important;
}

/* Ẩn triệt để hình tròn radio của Streamlit */
[data-testid="stRadioOption"] [class*="e1dm8mpf4"],
[data-testid="stRadioOption"] [class*="e1dm8mpf5"],
[data-testid="stRadioOption"] label > div:first-child,
[data-testid="stRadioOption"] > div > div:first-child,
[data-testid="stRadioOption"] input[type="radio"],
[data-testid="stRadioOption"] svg,
[data-testid="stRadioOption"] div[role="radio"],
[data-testid="stRadioOption"] div:has(> div[style*="border-radius: 50%"]),
[data-testid="stRadioOption"] div[style*="border-radius: 50%"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    position: absolute !important;
    pointer-events: none !important;
}

/* Định dạng từng Pill button menu */
[data-testid="stRadioOption"] {
    margin: 0 !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
}
[data-testid="stRadioOption"] > label,
[data-testid="stRadioOption"] > div {
    background: rgba(255, 245, 247, 0.85) !important;
    border: 1.2px solid rgba(255, 182, 193, 0.55) !important;
    border-radius: 20px !important;
    padding: 6px 13px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    user-select: none !important;
}
[data-testid="stRadioOption"]:hover > label,
[data-testid="stRadioOption"]:hover > div {
    background: #fff0f5 !important;
    border-color: #ff758c !important;
    transform: translateY(-1px) !important;
}
[data-testid="stRadioOption"] p,
[data-testid="stRadioOption"] span {
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    color: #555555 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}

/* Nút được chọn (Active) */
[data-testid="stRadioOption"]:has(input:checked) > label,
[data-testid="stRadioOption"]:has(input:checked) > div,
[data-testid="stRadioOption"][data-selected="true"] > label,
[data-testid="stRadioOption"][data-selected="true"] > div {
    background: linear-gradient(135deg, #ff758c, #ff7eb3) !important;
    border-color: transparent !important;
    box-shadow: 0 4px 12px rgba(255, 117, 140, 0.35) !important;
}
[data-testid="stRadioOption"]:has(input:checked) p,
[data-testid="stRadioOption"]:has(input:checked) span,
[data-testid="stRadioOption"][data-selected="true"] p,
[data-testid="stRadioOption"][data-selected="true"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ══════════════════════════════════════════════════════
   AESTHETIC FROSTED PINK HERO CARD (Inspired by Reference)
   ══════════════════════════════════════════════════════ */
.ios-hero-banner {
    background: rgba(255, 255, 255, 0.85);
    border: 1.5px solid rgba(255, 255, 255, 0.95);
    border-radius: 28px;
    padding: 24px 28px;
    color: #2b2b2b;
    box-shadow: 0 12px 32px rgba(230, 73, 128, 0.1);
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
}
/* Glowing Pink Heart Aura in background (like user reference music widget) */
.ios-hero-banner::before {
    content: '';
    position: absolute;
    top: -30px;
    right: 10px;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(255, 117, 140, 0.35) 0%, rgba(255, 182, 193, 0.18) 50%, transparent 70%);
    filter: blur(20px);
    border-radius: 50%;
    pointer-events: none;
}
.ios-hero-content {
    flex: 1;
    position: relative;
    z-index: 1;
}
.ios-hero-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #c2255c;
    margin: 0 0 6px 0;
    letter-spacing: -0.3px;
    line-height: 1.25;
}
.ios-hero-sub {
    font-size: 0.92rem;
    color: #495057;
    line-height: 1.55;
    margin: 0 0 12px 0;
    max-width: 620px;
    font-weight: 500;
}
.ios-hero-meta {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #ffffff;
    border: 1.2px solid rgba(255, 209, 220, 0.85);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #e64980;
    box-shadow: 0 2px 8px rgba(230, 73, 128, 0.08);
}
.ios-avatar-badge {
    width: 72px;
    height: 72px;
    background: linear-gradient(135deg, #f783ac 0%, #e64980 100%);
    border: 3px solid #ffffff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    box-shadow: 0 8px 20px rgba(230, 73, 128, 0.28);
    flex-shrink: 0;
    margin-left: 16px;
    position: relative;
    z-index: 1;
}
@media (max-width: 600px) {
    .ios-hero-banner {
        padding: 20px 18px;
        border-radius: 24px;
    }
    .ios-hero-title {
        font-size: 1.3rem;
    }
    .ios-hero-sub {
        font-size: 0.86rem;
    }
    .ios-avatar-badge {
        width: 56px;
        height: 56px;
        font-size: 1.7rem;
        margin-left: 10px;
    }
}

/* ══════════════════════════════════════════════════════
   AESTHETIC FROSTED PINK BENTO WIDGETS (Control Center style)
   ══════════════════════════════════════════════════════ */
.bento-widget {
    background: rgba(255, 255, 255, 0.88) !important;
    border-radius: 26px !important;
    padding: 18px 16px !important;
    position: relative !important;
    overflow: hidden !important;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    box-shadow: 0 6px 20px rgba(230, 73, 128, 0.06), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    min-height: 152px !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.95) !important;
    cursor: pointer !important;
}
.bento-widget:hover {
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 14px 28px rgba(230, 73, 128, 0.14) !important;
    border-color: #f783ac !important;
}
.bento-icon-badge {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}
/* Style A: Nền hồng đậm icon trắng (Control Center active toggle) */
.bento-icon-active {
    background: linear-gradient(135deg, #f783ac 0%, #e64980 100%);
    color: #ffffff;
    box-shadow: 0 5px 14px rgba(230, 73, 128, 0.3);
}
/* Style B: Nền trắng icon hồng (Control Center white pill) */
.bento-icon-white {
    background: #ffffff;
    color: #e64980;
    border: 1.5px solid #ffd1df;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
}
.bento-title {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #e64980;
    margin-bottom: 4px;
}
.bento-value {
    font-size: 1.25rem;
    font-weight: 800;
    color: #2b2b2b;
    line-height: 1.2;
    margin-bottom: 4px;
}
.bento-desc {
    font-size: 0.76rem;
    font-weight: 600;
    color: #868e96;
}

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
   TASK CARD & ACTION PILL BUTTONS (iOS Control Center Style)
   ══════════════════════════════════════════════════════ */
.task-card-item {
    background: rgba(255, 255, 255, 0.88) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.95) !important;
    border-radius: 24px !important;
    padding: 18px 18px 14px 18px !important;
    box-shadow: 0 8px 24px rgba(230, 73, 128, 0.08) !important;
    margin-bottom: 14px !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
}

/* Thanh 4 nút thao tác nằm gọn bên trong thẻ, luôn 1 hàng ngang trên cả Mobile & Desktop */
/* Thẻ task card item bo góc trên */
.task-card-item {
    background: #ffffff !important;
    border: 1.5px solid #ffe4e8 !important;
    border-top-left-radius: 18px !important;
    border-top-right-radius: 18px !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-bottom: 1px dashed #ffd6e0 !important;
    padding: 14px 16px 12px 16px !important;
    box-shadow: 0 4px 14px rgba(255, 182, 193, 0.08) !important;
    margin-bottom: 0 !important;
    box-sizing: border-box !important;
}

/* Khung 4 nút hành động Native Streamlit gắn liền dưới chân thẻ Task */
div[data-testid="stHorizontalBlock"]:has(button[key*="btn_p_"]) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    margin-top: -1px !important;
    margin-bottom: 0 !important;
    background: #ffffff !important;
    border: 1.5px solid #ffe4e8 !important;
    border-top: none !important;
    border-bottom-left-radius: 18px !important;
    border-bottom-right-radius: 18px !important;
    padding: 6px 10px 10px 10px !important;
    box-shadow: 0 4px 14px rgba(255, 182, 193, 0.08) !important;
}

div[data-testid="stHorizontalBlock"]:has(button[key*="btn_p_"]) > div {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(button[key*="btn_p_"]) button {
    border-radius: 20px !important;
    font-size: 0.74rem !important;
    font-weight: 700 !important;
    padding: 2px 4px !important;
    height: 32px !important;
    min-height: 32px !important;
    white-space: nowrap !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Nút xóa đỏ nhẹ nổi bật */
div[data-testid="stHorizontalBlock"]:has(button[key*="btn_p_"]) button[key*="btn_del_"] {
    background: #fff5f5 !important;
    border: 1.2px solid #ffc9c9 !important;
    color: #e03131 !important;
}
div[data-testid="stHorizontalBlock"]:has(button[key*="btn_p_"]) button[key*="btn_del_"]:hover {
    background: #ffe3e3 !important;
    border-color: #ffa8a8 !important;
    color: #c92a2a !important;
    transform: translateY(-1px) scale(1.02) !important;
}


/* ══════════════════════════════════════════════════════
   BENTO WIDGETS GRID (4 cột trên Desktop, 2x2 cân xứng trên Mobile)
   ══════════════════════════════════════════════════════ */
.bento-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
    width: 100% !important;
    margin-bottom: 14px !important;
    box-sizing: border-box !important;
}
.bento-link {
    text-decoration: none !important;
    color: inherit !important;
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

@media (max-width: 768px) {
    .bento-grid {
        grid-template-columns: 1fr 1fr !important;
        gap: 10px !important;
        width: 100% !important;
    }
    .bento-widget {
        min-height: 94px !important;
        padding: 12px 14px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 14px rgba(230, 73, 128, 0.06) !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .bento-icon-badge {
        width: 34px !important;
        height: 34px !important;
        margin-bottom: 6px !important;
    }
    .bento-icon-badge svg {
        width: 17px !important;
        height: 17px !important;
    }
    .bento-title {
        font-size: 0.70rem !important;
        margin-bottom: 2px !important;
    }
    .bento-value {
        font-size: 1.02rem !important;
        margin-bottom: 2px !important;
    }
    .bento-desc {
        font-size: 0.68rem !important;
    }
}

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
def get_cached_settings():
    return config.load_settings()

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_schedules():
    return database.get_all_schedules()

@st.cache_data(ttl=180, show_spinner=False)
def get_cached_tasks():
    return database.get_all_tasks()

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_medicines():
    return database.get_all_medicines()

@st.cache_data(ttl=120, show_spinner=False)
def get_cached_today_meds(today_str: str):
    return database.get_today_medicine_status(today_str)

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_attendance_stats():
    return database.get_all_attendance_stats()

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_single_attendance_stats(schedule_id: int):
    return database.get_attendance_stats(schedule_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_menstrual_records():
    return database.get_all_menstrual_records()

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_cycle_prediction():
    return menstrual_ml.predict_next_cycle()

@st.cache_data(ttl=180, show_spinner=False)
def get_cached_mood_range(start_date: str, end_date: str):
    """Cache mood logs theo khoảng ngày — TTL 180s để matrix luôn fresh."""
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

@st.cache_data(show_spinner=False)
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

def render_mascot_banner(filename: str, title: str, quote: str, badge: str = None):
    """Hiển thị Mascot Companion Banner tinh gọn, cân đối, không khoảng trống thừa."""
    b64 = get_cat_image_base64(filename)
    if not b64:
        return
    badge_html = f'<span class="mascot-badge">{badge}</span>' if badge else ''
    banner_html = (
        f'<div class="mascot-companion-banner">'
        f'<div class="mascot-img-wrap">'
        f'<img src="data:image/png;base64,{b64}" class="mascot-img" alt="{title}" />'
        f'</div>'
        f'<div class="mascot-speech-wrap">'
        f'<div class="mascot-header-line">'
        f'<span class="mascot-name">{title}</span>'
        f'{badge_html}'
        f'</div>'
        f'<div class="mascot-quote">"{quote}"</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

def strip_emojis(text: str) -> str:
    """Loại bỏ hoàn toàn mọi emoji màu mè, giữ lại văn bản tinh gọn thanh lịch."""
    if not text:
        return ""
    clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\ufe00-\ufe0f\u200d\u200c]', '', str(text))
    return re.sub(r'\s+', ' ', clean).strip()

settings = get_cached_settings()
her_name = settings.get("her_name", "Cậu 🌸")
my_name = settings.get("my_name", "Tớ 💫")
app_passcode = str(settings.get("app_passcode", "2010")).strip()

# ══════════════════════════════════════════════════════════════════════════════
# BẢO MẬT & XÁC THỰC: MÀN HÌNH KHÓA CẶP ĐÔI & MAGIC LINK 1-CHẠM
# ══════════════════════════════════════════════════════════════════════════════
# 1. Kiểm tra Magic Link từ Telegram (?key=... hoặc ?token=... hoặc ?passcode=...)
_provided_key = (
    st.query_params.get("key") or
    st.query_params.get("token") or
    st.query_params.get("passcode")
)
if _provided_key and str(_provided_key).strip() == app_passcode:
    st.session_state["is_authenticated"] = True

# Luôn duy trì key trong query_params khi đã xác thực để các thao tác chuyển tab/cập nhật không bị văng ra màn hình khóa
if st.session_state.get("is_authenticated", False):
    if "key" not in st.query_params:
        try:
            st.query_params["key"] = app_passcode
        except Exception:
            pass

# 2. Xử lý yêu cầu khóa ứng dụng / đăng xuất (?logout=1)
if "logout" in st.query_params:
    st.session_state["is_authenticated"] = False
    try:
        del st.query_params["logout"]
        for _pk in ["key", "token", "passcode"]:
            if _pk in st.query_params:
                del st.query_params[_pk]
    except Exception:
        pass
    st.rerun()

# 3. Chặn hoàn toàn và hiển thị Màn hình Khóa Mèo Bảo Vệ nếu chưa mở khóa
if not st.session_state.get("is_authenticated", False):
    st.markdown(f"""
    <div style="max-width: 440px; margin: 36px auto 16px; text-align: center;">
        <div style="background: white; border-radius: 24px; border: 2px solid #ffd6e0; box-shadow: 0 10px 30px rgba(255,107,139,0.12); padding: 26px 20px;">
            <div style="font-size: 3.2rem; margin-bottom: 6px;">🐱🔐</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #d81159; margin-bottom: 6px;">Khu Vườn Bí Mật Của {her_name} &amp; {my_name} 💖</div>
            <p style="font-size: 0.88rem; color: #666; line-height: 1.6; margin: 0 0 14px;">
                Không gian riêng tư được bảo vệ 24/7.<br>
                Vui lòng nhập mật mã hoặc mở qua Magic Link nhé! 🐾
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_pad_l, col_center_box, col_pad_r = st.columns([1, 2.2, 1])
    with col_center_box:
        with st.form("lock_screen_form"):
            user_pin_input = st.text_input(
                "🔑 Mã PIN / Mật mã mở khóa:",
                type="password",
                placeholder="Nhập mã mở khóa (VD: 2010)...",
                help="Mật mã bí mật do hai người quy định",
            )
            remember_device = st.checkbox("💖 Ghi nhớ mở khóa trên thiết bị này", value=True)
            submit_unlock = st.form_submit_button("Mở Khóa Khu Vườn 🌸", use_container_width=True, type="primary")

            if submit_unlock:
                if user_pin_input.strip() == app_passcode:
                    st.session_state["is_authenticated"] = True
                    if remember_device:
                        st.query_params["key"] = app_passcode
                    st.success(f"✨ Mở khóa thành công! Chào mừng {her_name} về nhà! 🌸")
                    st.rerun()
                else:
                    st.error(f"🐾 Mã mở khóa chưa đúng rồi nha! {her_name} thử lại xem nhé.")

        st.markdown(
            f'<div style="text-align: center; margin-top: 14px; font-size: 0.82rem; color: #888;">'
            f'💡 <i>Gợi ý: Nếu bấm link trực tiếp từ tin nhắn Telegram của Bot, {her_name} sẽ được vào thẳng không cần gõ mã!</i>'
            '</div>',
            unsafe_allow_html=True
        )

    st.stop()

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
    "Trang Chủ",
    "Lịch Học",
    "Deadline",
    "Chu Kỳ",
    "Đơn Thuốc",
    "Cảm Xúc",
    "Bé Jolyne 🦋",
    "Cài Đặt",
]

NAV_QUERY_MAP = {
    "TrangChu": "Trang Chủ",
    "LichHoc":  "Lịch Học",
    "Deadline": "Deadline",
    "ChuKy":    "Chu Kỳ",
    "DonThuoc": "Đơn Thuốc",
    "CamXuc":   "Cảm Xúc",
    "Jolyne":   "Bé Jolyne 🦋",
    "CaiDat":   "Cài Đặt",
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

# 1-Click cập nhật trạng thái / xóa task trực tiếp từ thẻ task (?task_act=...&tid=...)
if "task_act" in st.query_params:
    _t_act = st.query_params.get("task_act")
    try:
        _t_id = int(st.query_params.get("tid", 0))
    except Exception:
        _t_id = 0
    if _t_id > 0:
        if _t_act == "pending":
            database.update_task_status(_t_id, "Chưa làm")
        elif _t_act == "progress":
            database.update_task_status(_t_id, "Đang làm")
        elif _t_act == "done":
            database.update_task_status(_t_id, "Đã hoàn thành")
        elif _t_act == "del":
            database.delete_task(_t_id)
        invalidate_cache()
    try:
        del st.query_params["task_act"]
        if "tid" in st.query_params:
            del st.query_params["tid"]
    except Exception:
        pass
    st.session_state["active_nav"] = "Deadline"
    st.session_state["nav_desktop"] = "Deadline"
    st.session_state["nav_mobile"] = "Deadline"
    st.session_state["nav_radio_pills"] = "Deadline"
    st.rerun()

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

st.markdown(f"""
<div class="top-nav-bar">
    <div class="top-nav-brand">
        <div class="brand-heart-circle">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        </div>
        <div>
            <span class="brand-title">Trợ Lý Yêu Thương</span>
            <span class="brand-her">• {her_name}</span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <a href="?logout=1" target="_self" class="ios-circle-btn" title="Khóa ứng dụng (Đăng xuất)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#e64980" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="3" ry="3"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <span>Khóa</span>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

selected_nav = st.radio(
    "",
    options=NAV_OPTIONS,
    index=cur_idx,
    horizontal=True,
    label_visibility="collapsed",
    key="nav_radio_pills",
)
st.session_state["active_nav"] = selected_nav

# ── BÉ JOLYNE KUJO ĐỒNG HÀNH LƠ LỬNG TRÊN TOÀN BỘ WEB APP ──
mascot_manager.render_floating_mascot(st, her_name=her_name, my_name=my_name)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTING NỘI DUNG THEO NAVBAR
# ══════════════════════════════════════════════════════════════════════════════
if "Trang Chủ" in selected_nav:
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

    # Lời chào theo khung giờ trong ngày (ấm áp, tự nhiên như bạn trai nhắn)
    current_hour = datetime.now().hour
    if 5 <= current_hour < 11:
        greeting_time = f"Chào buổi sáng, {her_name} ☀️"
        sub_time = f"Chúc {her_name} ngày mới thật nhiều năng lượng! Đừng quên ăn sáng ấm bụng nhé 🌸"
    elif 11 <= current_hour < 14:
        greeting_time = f"Nghỉ trưa thôi nào, {her_name} 🍱"
        sub_time = f"Học cả buổi sáng vất vả rồi, {her_name} nhớ ăn cơm đúng giờ và chợp mắt xíu nha 💖"
    elif 14 <= current_hour < 18:
        greeting_time = f"Buổi chiều an lành nha, {her_name} ☕"
        sub_time = f"Cố gắng nốt buổi chiều rồi tối về nghỉ ngơi xả hơi nha {her_name} ✨"
    elif 18 <= current_hour < 23:
        greeting_time = f"Buổi tối ấm áp nha, {her_name} 🌙"
        sub_time = f"Hôm nay {her_name} làm tốt lắm rồi! Tối nay nghỉ ngơi, nghe nhạc cho thư giãn nhé 🍵"
    else:
        greeting_time = f"Khuya rồi, ngủ sớm thôi {her_name} 🧸"
        sub_time = f"Đừng thức khuya mệt người nha {her_name}, ngủ một giấc thật ngon để mai gặp lại nhé 💫"

    st.markdown(f"""
    <div class="ios-hero-banner">
        <div class="ios-hero-content">
            <div class="ios-hero-title">Trợ Lý Yêu Thương 💖</div>
            <div class="ios-hero-sub"><b>{greeting_time}</b> — {sub_time}</div>
            <div class="ios-hero-meta">
                <span>📅 {today_day_name}, {today_date.strftime("%d/%m")}</span>
                <span>•</span>
                <span>💖 Luôn đồng hành cùng {her_name}</span>
            </div>
        </div>
        <div class="ios-hero-side">
            <div class="ios-avatar-badge">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 0. Mảnh Giấy Nhớ Ghim Yêu Thương (Nếu có và chưa bấm đã đọc)
    pinned_note_txt = settings.get("pinned_note", "").strip()
    pinned_note_time = settings.get("pinned_note_time", "").strip()
    my_display_name = my_name

    if pinned_note_txt:
        time_tag = f" — <span style='font-size:0.75rem;opacity:0.8;'>{pinned_note_time}</span>" if pinned_note_time else ""
        col_note_box, col_note_ack = st.columns([3.8, 1.2])
        with col_note_box:
            st.markdown(f"""
            <div style="background:#fffcf0;border:1.5px solid #ffe58f;border-left:5px solid #faad14;border-radius:14px;padding:12px 16px;box-shadow:0 3px 12px rgba(250,173,20,0.12);margin-bottom:12px;">
                <div style="display:flex;align-items:center;gap:6px;font-weight:700;color:#d46b08;font-size:0.92rem;margin-bottom:4px;">
                    📌 Mảnh giấy nhớ từ {my_display_name}{time_tag}
                </div>
                <div style="font-size:0.93rem;color:#333;line-height:1.6;font-style:italic;">
                    "{pinned_note_txt}"
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_note_ack:
            if st.button("💌 Đã đọc 🌸", key="btn_ack_pinned_note", help="Bấm để xóa lời nhắn và giải phóng bộ nhớ", use_container_width=True):
                cur_st = config.load_settings()
                cur_st["pinned_note"] = ""
                cur_st["pinned_note_time"] = ""
                config.save_settings(cur_st)
                invalidate_cache()
                try:
                    notifier.notify_you_secret(
                        f"💌 <b>[{her_name.upper()} ĐÃ ĐỌC LỜI NHẮN]</b> 🌸\n\n"
                        f"{her_name} vừa đọc và xóa lời nhắn ghim của {my_name}:\n"
                        f"<i>\"{pinned_note_txt}\"</i>"
                    )
                except Exception:
                    pass
                st.toast(f"✨ {her_name} đã đọc lời nhắn rồi! Chúc {her_name} một ngày thật vui vẻ! 💖")
                st.rerun()

    # 1. Bốn Thẻ Bento Widgets Monochromatic Pink Aesthetic (Click để chuyển tab)
    sch_val = f"{len(today_scheds)} ca học" if today_scheds else "Hôm nay nghỉ 🎉"
    sch_desc = f"{today_day_name} ({today_date.strftime('%d/%m')})"

    task_val = f"{len(pending_tasks)} bài tập" if pending_tasks else "Đã xong hết ✨"
    task_desc = "Cần hoàn thành" if pending_tasks else "Thảnh thơi nghỉ ngơi nha 🏖️"

    if pred_home.get("has_data"):
        ck_val = f"Còn {pred_home['days_left']} ngày"
        ck_desc = f"Dự kiến: {pred_home.get('predicted_next_date', '---')}"
    else:
        ck_val = "Chưa có kỳ"
        ck_desc = "Theo dõi chu kỳ"

    if total_meds_home:
        med_val = f"{taken_meds_home}/{total_meds_home} liều"
        med_desc = "Đã uống đủ! 💖" if taken_meds_home == total_meds_home else f"Còn {total_meds_home - taken_meds_home} liều nữa nha"
    else:
        med_val = "Trống lịch"
        med_desc = "Khỏe mạnh mỗi ngày ✨"

    st.markdown(f"""
    <div class="bento-grid">
        <a href="?nav=LichHoc&key={app_passcode}" target="_self" class="bento-link">
            <div class="bento-widget">
                <div class="bento-icon-badge bento-icon-active">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                        <line x1="9" y1="7" x2="15" y2="7"/>
                        <line x1="9" y1="11" x2="13" y2="11"/>
                    </svg>
                </div>
                <div>
                    <div class="bento-title">Lịch Học</div>
                    <div class="bento-value">{sch_val}</div>
                    <div class="bento-desc">{sch_desc}</div>
                </div>
            </div>
        </a>
        <a href="?nav=Deadline&key={app_passcode}" target="_self" class="bento-link">
            <div class="bento-widget">
                <div class="bento-icon-badge bento-icon-white">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                </div>
                <div>
                    <div class="bento-title">Deadline</div>
                    <div class="bento-value">{task_val}</div>
                    <div class="bento-desc">{task_desc}</div>
                </div>
            </div>
        </a>
        <a href="?nav=ChuKy&key={app_passcode}" target="_self" class="bento-link">
            <div class="bento-widget">
                <div class="bento-icon-badge bento-icon-active">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                </div>
                <div>
                    <div class="bento-title">Chu Kỳ</div>
                    <div class="bento-value">{ck_val}</div>
                    <div class="bento-desc">{ck_desc}</div>
                </div>
            </div>
        </a>
        <a href="?nav=DonThuoc&key={app_passcode}" target="_self" class="bento-link">
            <div class="bento-widget">
                <div class="bento-icon-badge bento-icon-white">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/>
                        <path d="m8.5 8.5 7 7"/>
                    </svg>
                </div>
                <div>
                    <div class="bento-title">Uống Thuốc</div>
                    <div class="bento-value">{med_val}</div>
                    <div class="bento-desc">{med_desc}</div>
                </div>
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 2. Lời Nhắn Yêu Thương & Chăm Sóc Hôm Nay
    render_mascot_banner(
        "smile-cat.png",
        "Bác Sĩ Mèo 🐾",
        f"{her_name} nhớ uống đủ nước ấm, ăn đúng bữa và giữ tinh thần thật thoải mái nhé! {my_name} luôn ở đây cùng {her_name} nè ✨💖",
        badge=f"{today_day_name}"
    )

    # 3. Lịch học & Deadline chi tiết (Bố cục 2 cột cân đối 50/50 tràn viền hoàn hảo)
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
            sch_body_html = f'<div style="color:#888;font-size:0.88rem;margin-top:8px;line-height:1.6;">🎉 Hôm nay không có môn học nào! {her_name} thoải mái nghỉ ngơi hoặc ôn bài nhé.</div>'

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

elif "Lịch Học" in selected_nav:
    all_scheds = get_cached_schedules()
    has_conflict, c_s1, c_s2 = check_schedule_conflicts(all_scheds)

    st.subheader("🎒 Lịch Học & Điểm Danh Chuyên Cần")
    st.markdown('<p class="hint-text">Theo dõi lịch học cả tuần, quản lý số buổi vắng và tự động tính chuyên cần.</p>', unsafe_allow_html=True)
    if has_conflict:
        st.warning(f"⚠️ **HUH? Phát hiện trùng lịch:** Môn **{c_s1['subject_name']}** và **{c_s2['subject_name']}** bị đè giờ nhau vào {c_s1['day_name']} ({c_s1['start_time']}-{c_s1['end_time']} & {c_s2['start_time']}-{c_s2['end_time']})!")
        render_mascot_banner("huh-cat.jpg", "Mèo Giật Mình 🙀", f"HUH? Có môn bị đè giờ nhau kìa! {her_name} kiểm tra và điều chỉnh lại lịch nhé!", badge="Cảnh báo trùng lịch")
    else:
        render_mascot_banner("study-cat.jpg", "Mèo Chăm Học 📚", f"Học chăm chỉ mỗi ngày để tương lai rạng ngời nha {her_name}! 🌸✨", badge="Bạn đồng hành")

    # ── Sub-tabs ──
    sub_add, sub_att, sub_view = st.tabs(["➕ Thêm Môn Học", "📝 Điểm Danh Hôm Nay", "📊 Toàn Bộ Lịch Học"])

    # ────────────────────── THÊM MÔN HỌC ──────────────────────
    with sub_add:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="hint-text">Điền thông tin bên dưới để lưu một môn học vào lịch tuần. (*) là bắt buộc.</p>', unsafe_allow_html=True)

        fa, fb = st.columns([1.8, 1])
        with fa:
            st.markdown('<span class="step-label">1</span> <b>Tên môn học (*)</b>', unsafe_allow_html=True)
            subj_name = st.text_input("ten_mon", placeholder="VD: Lập trình Web, Tiếng Anh B2...",
                label_visibility="collapsed",
                help=f"Nhập đúng tên môn học trên thời khóa biểu của {her_name}")
        with fb:
            day_opts  = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"]
            day_select = st.selectbox("📅 Ngày học (*)", day_opts,
                help="Chọn thứ mà môn này được dạy mỗi tuần")

        # Khởi tạo trạng thái giờ học linh hoạt (cho phép chọn bất kỳ giờ phút nào)
        if "sch_start_val" not in st.session_state:
            st.session_state["sch_start_val"] = time(7, 30)
        if "sch_end_val" not in st.session_state:
            st.session_state["sch_end_val"] = time(11, 0)

        # Lối tắt chọn ca học nhanh (tùy chọn bấm nhanh, không giới hạn)
        st.markdown('<p class="hint-text">⚡ <b>Lối tắt ca học nhanh</b> (hoặc tự do chỉnh giờ:phút bất kỳ bên dưới):</p>', unsafe_allow_html=True)
        qc1, qc2, qc3, qc4, qc5 = st.columns(5)
        if qc1.button("Ca 1\n07:30-11:00", use_container_width=True, key="btn_sch_ca1"):
            st.session_state["sch_start_val"] = time(7, 30); st.session_state["sch_end_val"] = time(11, 0); st.rerun()
        if qc2.button("Ca 2\n11:30-15:00", use_container_width=True, key="btn_sch_ca2"):
            st.session_state["sch_start_val"] = time(11, 30); st.session_state["sch_end_val"] = time(15, 0); st.rerun()
        if qc3.button("Ca 3\n13:00-16:30", use_container_width=True, key="btn_sch_ca3"):
            st.session_state["sch_start_val"] = time(13, 0); st.session_state["sch_end_val"] = time(16, 30); st.rerun()
        if qc4.button("Ca 4\n15:30-19:00", use_container_width=True, key="btn_sch_ca4"):
            st.session_state["sch_start_val"] = time(15, 30); st.session_state["sch_end_val"] = time(19, 0); st.rerun()
        if qc5.button("Ca Tối\n18:00-21:00", use_container_width=True, key="btn_sch_cat"):
            st.session_state["sch_start_val"] = time(18, 0); st.session_state["sch_end_val"] = time(21, 0); st.rerun()

        fc, fd, fe = st.columns(3)
        with fc:
            category = st.selectbox("🏷️ Loại môn",
                ["Môn lý thuyết","Môn đồ án/bài tập lớn","Môn ngoại ngữ"])
        with fd:
            cur_start = st.time_input("🕗 Giờ bắt đầu (*mọi giờ:phút*)", value=st.session_state["sch_start_val"], key="sch_start_input")
            st.session_state["sch_start_val"] = cur_start
            start_str = cur_start.strftime("%H:%M")
        with fe:
            cur_end = st.time_input("🕙 Giờ kết thúc (*mọi giờ:phút*)", value=st.session_state["sch_end_val"], key="sch_end_input")
            st.session_state["sch_end_val"] = cur_end
            end_str = cur_end.strftime("%H:%M")

        fg, fh, fi = st.columns(3)
        with fg:
            room = st.text_input("📍 Phòng học", placeholder="VD: A2-301, Zoom...",
                help="Có thể bỏ trống")
        with fh:
            total_sess = st.number_input("📋 Tổng số buổi (*)", min_value=1, max_value=100, value=10, step=1)
        with fi:
            max_allowed_limit = max(0, int(total_sess)-1)
            default_calc = min(max(1, int(round(total_sess * 0.2))), max_allowed_limit)
            max_abs = st.number_input(f"🚨 Buổi được nghỉ (Gợi ý 20% = {default_calc}) (*)",
                min_value=0, max_value=max_allowed_limit, value=default_calc, step=1,
                help=f"Tự động tính mức 20%: {default_calc} buổi. Bạn có thể tăng giảm tùy quy chế trường.")

        notes = ""
        with st.expander("📝 Ghi chú dặn dò (không bắt buộc)"):
            notes = st.text_area("Ghi chú", placeholder="VD: Nhớ sạc laptop, chuẩn bị slide thuyết trình...", height=70, label_visibility="collapsed")

        if subj_name.strip():
            pct = round((max_abs/total_sess)*100, 1) if total_sess else 0
            st.markdown(f"""<div class="preview-box">
                <b>👁️ Xem trước thẻ môn học:</b><br>
                📚 <b>{subj_name}</b> &nbsp;|&nbsp; 🏷️ {category}<br>
                📅 <b>{day_select}</b> &nbsp;|&nbsp; 🕒 <b>{start_str} → {end_str}</b> &nbsp;|&nbsp; 📍 {room or "(Chưa điền)"}<br>
                📋 Tổng <b>{int(total_sess)} buổi</b> &nbsp;|&nbsp; 🚨 Cho phép nghỉ: <b>{int(max_abs)} buổi</b> ({pct}%)
            </div>""", unsafe_allow_html=True)

        if st.button("💖 Lưu Môn Học Này Vào Lịch", use_container_width=True, type="primary"):
            err = []
            if not subj_name.strip(): err.append("Chưa nhập tên môn học")
            if max_abs >= total_sess:
                err.append(f"Số buổi nghỉ ({int(max_abs)}) phải nhỏ hơn tổng buổi ({int(total_sess)})!")
            if err:
                for e in err: st.error(f"⚠️ {e}")
            else:
                day_idx = day_opts.index(day_select)
                database.add_schedule(subj_name.strip(), day_idx, day_select, start_str, end_str,
                                      room.strip(), category, notes.strip() if notes else "",
                                      int(total_sess), int(max_abs))
                invalidate_cache()
                st.success(f"✅ Đã lưu môn '{subj_name}' ({start_str} - {end_str})!")
                st.balloons()
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="card" style="margin-top:14px;">
            <div class="section-title">💡 Mẹo nhỏ & Lưu ý chuyên cần</div>
            <div style="font-size:.87rem;line-height:1.75;color:#555;">
            🎯 Nhập đúng tên môn sẽ giúp Bot nhắc lịch chính xác hơn!<br>
            ⏰ Số buổi nghỉ = 20% tổng buổi là mức phổ biến tại đa số trường.<br>
            📱 Sau khi lưu, Bot Telegram sẽ nhắc {her_name} <b>30 phút trước</b> giờ học!<br>
            🚨 Khi số buổi vắng vượt giới hạn → Hệ thống tự gửi cảnh báo CẤM THI!
            </div>
        </div>""", unsafe_allow_html=True)

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
elif "Deadline" in selected_nav:
    # ── Header row ──
    st.subheader("Quản Lý Deadline & AI Dự Đoán Rủi Ro")
    st.markdown('<p class="hint-text">Thêm bài tập, AI tự tính xác suất trễ hạn và hệ thống nhắc nhở đúng các mốc thời gian.</p>', unsafe_allow_html=True)

    tasks = get_cached_tasks()
    all_scheds = get_cached_schedules()
    now_dt = config.get_now()
    today_wd = now_dt.weekday()
    classes_today = len([s for s in all_scheds if s.get("day_of_week") == today_wd])

    _has_overdue_p = any(
        t["status"] != "Đã hoàn thành" and datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M") < now_dt
        for t in tasks
    ) if tasks else False
    _has_pending_p = any(t["status"] != "Đã hoàn thành" for t in tasks) if tasks else False

    if not tasks or not _has_pending_p:
        render_mascot_banner("smile-cat.png", "Mèo Thảnh Thơi", f"Không có deadline nào đang chờ! {her_name} thoải mái tận hưởng ngày mới nhé!", badge="0 Deadline")
    elif _has_overdue_p:
        render_mascot_banner("cry-cat.jpg", "Mèo Hốt Hoảng", f"Huhu có bài tập bị quá hạn rồi! Hoàn thành sớm để nhẹ đầu nha {her_name}!", badge="Có task trễ hạn")
    else:
        render_mascot_banner("burnOut_cat.jpg", "Mèo Nước Rút", f"Deadline đang dí sát nút rùi! {her_name} tập trung hoàn thành từng bài một nha!", badge="Đang có deadline")

    sub_list_t, sub_add_t, sub_ai_t = st.tabs(["📋 Danh Sách Task", "➕ Thêm Deadline", "🤖 Kiểm Tra AI Nhanh"])

    # ── 1. Danh sách task (Tab chính mặc định) ──
    with sub_list_t:
        if not tasks:
            st.markdown(f"""<div class="card" style="padding:24px;">
                <div class="section-title">Trống deadline</div>
                <p style="color:#555;line-height:1.75;">{her_name} không có deadline nào đang chờ. Được nghỉ ngơi rồi, an tâm thư giãn nhé.</p>
            </div>""", unsafe_allow_html=True)
        else:
            filter_status = st.selectbox("Lọc trạng thái:", ["Tất cả","Chưa làm","Đang làm","Đã hoàn thành"], key="filter_deadline_status")

            for t in tasks:
                if filter_status and filter_status != "Tất cả" and t["status"] != filter_status:
                    continue
                d_dt   = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                diff_h = (d_dt - now_dt).total_seconds() / 3600.0
                pred   = deadline_ml.predict_deadline_risk(t["task_name"], classes_today, max(0.1,diff_h), t["estimated_hours"])
                
                # Làm sạch dữ liệu, triệt tiêu hoàn toàn emoji
                clean_name = strip_emojis(t['task_name'])
                clean_subj = strip_emojis(t['subject_name'])
                clean_msg  = strip_emojis(pred['warning_message'])

                # Style huy hiệu trạng thái theo chuẩn Monochromatic Pink (iOS Control Center)
                if t["status"] == "Đã hoàn thành":
                    badge_html = """<span style="background:rgba(255,227,236,0.95);color:#c2255c;border:1px solid #fcc2d7;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:20px;display:inline-flex;align-items:center;gap:4px;">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#c2255c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        Hoàn thành
                    </span>"""
                elif t["status"] == "Đang làm":
                    badge_html = """<span style="background:rgba(255,240,246,0.95);color:#d6336c;border:1px solid #faa2c1;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:20px;display:inline-flex;align-items:center;gap:4px;">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#d6336c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        Đang làm
                    </span>"""
                else:
                    badge_html = """<span style="background:rgba(248,249,250,0.95);color:#868e96;border:1px solid #e9ecef;font-size:0.75rem;font-weight:600;padding:3px 10px;border-radius:20px;display:inline-flex;align-items:center;gap:4px;">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#868e96" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>
                        Chưa làm
                    </span>"""

                st.markdown(f"""
                <div class="task-card-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <div style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg, #f783ac, #e64980);display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(230,73,128,0.25);flex-shrink:0;">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                            </div>
                            <span style="font-weight:700;font-size:0.98rem;color:#2b2b2b;">{clean_name}</span>
                        </div>
                        {badge_html}
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:0.83rem;color:#495057;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid rgba(255,228,232,0.6);">
                        <span style="display:inline-flex;align-items:center;gap:5px;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#e64980" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                            <b>{clean_subj}</b>
                        </span>
                        <span style="display:inline-flex;align-items:center;gap:5px;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#e64980" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            Hạn: <b>{t['deadline']}</b> (còn <b>{max(0,diff_h):.1f}h</b>)
                        </span>
                        <span style="display:inline-flex;align-items:center;gap:5px;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#e64980" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="7"/><polyline points="12 9 12 12 13.5 13.5"/><path d="M16.51 17.35l-.85-.85"/><path d="M9 5h6"/><path d="M12 2v3"/></svg>
                            Dự kiến: <b>{t['estimated_hours']}h</b>
                        </span>
                    </div>
                    <div style="background:rgba(255,240,243,0.7);border:1px solid rgba(255,209,220,0.85);border-radius:14px;padding:8px 12px;font-size:0.82rem;line-height:1.5;color:#495057;">
                        <div style="display:inline-flex;align-items:center;gap:4px;font-size:0.75rem;font-weight:700;color:#c2255c;background:#ffffff;border:1px solid #ffd1df;border-radius:12px;padding:1px 8px;margin-bottom:4px;">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#e64980" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                            AI Rủi ro: {pred['risk_percentage']}%
                        </div>
                        <div>{clean_msg}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Nút hành động Native của Streamlit gắn liền dưới thẻ
                c_p, c_w, c_d, c_del = st.columns([1, 1, 1.25, 0.75])
                with c_p:
                    is_p = (t["status"] == "Chưa làm")
                    if st.button("○ Chưa làm", key=f"btn_p_{t['id']}", use_container_width=True, type="primary" if is_p else "secondary"):
                        database.update_task_status(t['id'], "Chưa làm")
                        invalidate_cache()
                        st.rerun()
                with c_w:
                    is_w = (t["status"] == "Đang làm")
                    if st.button("◐ Đang làm", key=f"btn_w_{t['id']}", use_container_width=True, type="primary" if is_w else "secondary"):
                        database.update_task_status(t['id'], "Đang làm")
                        invalidate_cache()
                        st.rerun()
                with c_d:
                    is_d = (t["status"] == "Đã hoàn thành")
                    if st.button("✓ Hoàn thành", key=f"btn_d_{t['id']}", use_container_width=True, type="primary" if is_d else "secondary"):
                        database.update_task_status(t['id'], "Đã hoàn thành")
                        invalidate_cache()
                        st.rerun()
                with c_del:
                    if st.button("🗑️ Xóa", key=f"btn_del_{t['id']}", use_container_width=True):
                        database.delete_task(t['id'])
                        invalidate_cache()
                        st.toast(f"Đã xóa vĩnh viễn bài tập '{clean_name}'!")
                        st.rerun()

                st.markdown('<div style="margin-bottom:14px;"></div>', unsafe_allow_html=True)

    # ── 2. Thêm deadline ──
    with sub_add_t:
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
        if "dl_time_val" not in st.session_state:
            st.session_state["dl_time_val"] = time(23, 59)

        st.markdown('<p class="hint-text"><b>Lối tắt mốc giờ phổ biến</b> (hoặc tự do chỉnh mọi giờ:phút bên dưới):</p>', unsafe_allow_html=True)
        dq1, dq2, dq3, dq4 = st.columns(4)
        if dq1.button("23:59\n(Cuối ngày)", use_container_width=True, key="btn_dl_night"):
            st.session_state["dl_time_val"] = time(23, 59); st.rerun()
        if dq2.button("12:00\n(Nghỉ trưa)", use_container_width=True, key="btn_dl_noon"):
            st.session_state["dl_time_val"] = time(12, 0); st.rerun()
        if dq3.button("17:00\n(Cuối chiều)", use_container_width=True, key="btn_dl_eve"):
            st.session_state["dl_time_val"] = time(17, 0); st.rerun()
        if dq4.button("08:00\n(Đầu sáng)", use_container_width=True, key="btn_dl_morn"):
            st.session_state["dl_time_val"] = time(8, 0); st.rerun()

        tb1, tb2 = st.columns(2)
        with tb1:
            due_date = st.date_input("Ngày hết hạn (*bất kỳ ngày nào*)", value=date.today() + timedelta(days=3))
        with tb2:
            due_time_pick = st.time_input("Giờ hết hạn (*mọi giờ:phút*)", value=st.session_state["dl_time_val"], key="dl_time_input")
            st.session_state["dl_time_val"] = due_time_pick
            due_hour = due_time_pick.strftime("%H:%M")

        st.markdown('<span class="step-label">3</span> <b>Khối lượng công việc dự kiến</b>', unsafe_allow_html=True)
        est_hours = st.number_input("Cần khoảng bao nhiêu giờ để hoàn thành? (*mọi số giờ*)",
            min_value=0.5, max_value=120.0, value=3.0, step=0.5,
            help="Gợi ý: Bài tập nhỏ 1-2h, Tiểu luận 3-5h, Đồ án lớn 8-20h...")

        if task_name.strip():
            deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
            deadline_dt  = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            diff_h       = (deadline_dt - config.get_now()).total_seconds() / 3600.0
            if diff_h > 0:
                quick_ai   = deadline_ml.predict_deadline_risk(task_name, classes_today, diff_h, est_hours)
                risk_color = "#c2255c" if quick_ai["risk_percentage"] >= 70 else ("#d97706" if quick_ai["risk_percentage"] >= 40 else "#0d8a52")
                clean_t_name = strip_emojis(task_name)
                clean_s_task = strip_emojis(subj_task)
                st.markdown(f"""<div class="preview-box">
                    <b>Xem trước:</b><br>
                    <b>{clean_t_name}</b> &nbsp;•&nbsp; Môn: {clean_s_task}<br>
                    Deadline: <b>{due_date.strftime('%d/%m/%Y')} lúc {due_hour}</b> (còn <b>{diff_h:.1f} giờ</b>)<br>
                    Ước tính: <b>{est_hours}h</b><br>
                    AI rủi ro hôm nay: <b style="color:{risk_color};">{quick_ai['risk_percentage']}% — {quick_ai['warning_level']}</b>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("Ngày deadline đã qua rồi! Hãy chọn lại ngày đúng nhé.")

        if st.button("Lưu Task & Bắt Đầu Theo Dõi", use_container_width=True, type="primary"):
            if not task_name.strip():
                st.error("Chưa nhập tên bài tập!")
            elif not subj_task or not str(subj_task).strip():
                st.error("Chưa chọn môn học!")
            else:
                deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
                database.add_task(task_name.strip(), str(subj_task), deadline_str, float(est_hours), "Chưa làm")
                invalidate_cache()
                st.success(f"Đã lưu task '{task_name}'! Hệ thống sẽ nhắc đúng các mốc thời gian.")
                st.rerun()

        st.markdown("""<div class="card" style="margin-top:14px;">
            <div class="section-title">Mẹo Quản Lý Deadline</div>
            <div style="font-size:.87rem;line-height:1.8;color:#555;">
            • AI phân tích dựa trên số ca học hôm đó & giờ rảnh thực tế.<br>
            • <b>Rủi ro ≥70%:</b> Nên làm ngay hôm nay!<br>
            • <b>Rủi ro 40–70%:</b> Ưu tiên làm sớm.<br>
            • <b>Rủi ro &lt;40%:</b> Còn thời gian thoải mái.<br>
            • Hệ thống tự động nhắc trước <b>24h, 6h và 1h</b> deadline.
            </div>
        </div>""", unsafe_allow_html=True)


    # ── AI nhanh ──
    with sub_ai_t:
        col_ai_form, col_ai_tip = st.columns([2.2, 1])
        with col_ai_form:
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

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CHU KỲ SINH LÝ
# ══════════════════════════════════════════════════════════════════════════════
elif "Chu Kỳ" in selected_nav:
    pred = get_cached_cycle_prediction()

    # ── Mascot Banner Trạng Thái Chu Kỳ ──
    st.subheader("🌸 Theo Dõi & AI Dự Đoán Chu Kỳ Kinh Nguyệt")
    st.markdown(f'<p class="hint-text">Hệ thống AI thích ứng học cơ địa riêng của {her_name} để dự đoán ngày đèn đỏ, ngày rụng trứng và nhắc nhở 2 chiều.</p>', unsafe_allow_html=True)

    if pred.get("has_data"):
        days_left = pred["days_left"]
        if days_left <= 0:
            render_mascot_banner("worry_cat.jpg", "Mèo Bác Sĩ 🩺", f"Hôm nay hoặc đã qua ngày dự kiến ({pred['predicted_next_date']}). {her_name} nhớ giữ ấm bụng, uống nước ấm và cập nhật nhé! 💖", badge="Đến kỳ rồi")
        elif days_left <= 3:
            render_mascot_banner("worry_cat.jpg", "Mèo Bác Sĩ 🩺", f"Giai đoạn PMS: Còn {days_left} ngày đến kỳ mới ({pred['predicted_next_date']}). Giữ ấm bụng, uống nước ấm nha {her_name}! 🍵", badge=f"Còn {days_left} ngày")
        elif days_left <= 5:
            render_mascot_banner("chating_cat.jpg", "Mèo Chu Đáo 🌸", f"Sắp vào kỳ PMS: Còn {days_left} ngày ({pred['predicted_next_date']}). Chuẩn bị đồ dùng và tâm lý thoải mái nhé!", badge=f"Còn {days_left} ngày")
        else:
            render_mascot_banner("smile-cat.png", "Mèo Vui Vẻ ✨", f"Cơ địa bình thường — Còn {days_left} ngày đến chu kỳ tiếp theo ({pred['predicted_next_date']}). Cứ yên tâm học tập vui chơi nha!", badge="An tâm")
    else:
        render_mascot_banner("chating_cat.jpg", "Mèo Hướng Dẫn 🌸", "Chưa có dữ liệu chu kỳ. Hãy bấm nút 'HÔM NAY BẮT ĐẦU KỲ MỚI' bên dưới để bắt đầu theo dõi nhé!", badge="Bắt đầu")

    st.divider()
    col_a, col_b = st.columns([1.3, 1])

    with col_a:
        st.markdown(f"""<div class="card">
            <div class="section-title">💖 Ghi Nhận Chu Kỳ Mới</div>
            <p style="font-size:.92rem;color:#555;margin-bottom:12px;">
            Mỗi lần bắt đầu kỳ mới, {her_name} chỉ cần bấm 1 nút. AI sẽ tự học cơ địa riêng của {her_name}!
            </p>
        </div>""", unsafe_allow_html=True)

        if st.button("💖 HÔM NAY BẮT ĐẦU KỲ MỚI", use_container_width=True, type="primary"):
            database.add_menstrual_record(date.today().strftime("%Y-%m-%d"))
            menstrual_ml.retrain_model()
            invalidate_cache()
            st.balloons()
            st.success(f"Đã ghi nhận! AI đã cập nhật cơ địa của {her_name}.")
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
            ovul_val   = pred.get("ovulation_date","Chưa rõ")
            fertile_val= pred.get("fertile_window",{}).get("text","Chưa rõ") if pred.get("fertile_window") else "Chưa rõ"
            algo_val   = pred.get("algorithm_used","Medical Baseline")
            st.markdown(f"""<div class="preview-box">
                <b>🔮 AI Dự Đoán Cơ Địa Của {her_name}:</b><br>
                • Chu kỳ: <b>{pred['cycle_length']} ngày</b> (học từ {pred['history_count']} lần)<br>
                • Thuật toán: <b>{algo_val}</b><br>
                • Kỳ gần nhất: <b>{pred['latest_start_date']}</b> &nbsp;|&nbsp; Tiếp theo: <b>{pred['predicted_start_date']}</b><br>
                • Ngày rụng trứng: <b>{ovul_val}</b><br>
                • Cửa sổ thụ thai: <b>{fertile_val}</b><br>
                • PMS bắt đầu: <b>{pred['pms_start_date']}</b> (còn {pred['days_remaining']} ngày)
            </div>""", unsafe_allow_html=True)
            with st.expander(f"💌 Lời Khuyên Sức Khỏe Hôm Nay Cho {her_name}"):
                st.info(pred.get("advice_for_her",""))

    with col_b:
        st.markdown(f"""<div class="card">
            <div class="section-title">🍓 Cơ Chế Thông Báo Kép</div>
            <p style="font-size:.9rem;color:#555;line-height:1.7;">
            <b>🌸 Nhắn cho {her_name} (Telegram):</b><br>
            — Trước 3 ngày: Nhắc giữ ấm bụng, uống nước ấm<br>
            — Đúng ngày dự kiến: Nhắc chuẩn bị đồ dùng<br><br>
            <b>🍓 Nhắn BÍ MẬT cho {my_name}:</b><br>
            — Trước 4 ngày: Bot tự nhắn riêng để {my_name} nhường nhịn, chuẩn bị trà ấm!
            </p>
        </div>""", unsafe_allow_html=True)

        if pred.get("has_data"):
            with st.expander(f"🍓 [SECRET MODE] Lời Khuyên Bí Mật Cho {my_name}", expanded=True):
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
elif "Đơn Thuốc" in selected_nav:
    today_str_m  = date.today().strftime("%Y-%m-%d")
    today_meds   = get_cached_today_meds(today_str_m)
    total_h      = len(today_meds)
    taken_h      = sum(1 for m in today_meds if m["taken"]) if today_meds else 0

    # ── Mascot Banner Bác Sĩ Meow ──
    st.subheader("💊 Nhắc Lịch Uống Thuốc & Đọc Đơn Bằng AI")
    st.markdown('<p class="hint-text">Theo dõi lịch uống thuốc, quét đơn bằng AI và nhận nhắc nhở đúng giờ qua Telegram.</p>', unsafe_allow_html=True)

    if not today_meds:
        render_mascot_banner("doctor-cat.png", "Bác Sĩ Meow 🩺", f"Hôm nay {her_name} không có lịch thuốc nào. Chúc {her_name} luôn dồi dào sức khỏe, luôn vui tươi nhé! 🌸", badge="Khỏe mạnh")
    elif taken_h == total_h:
        render_mascot_banner("smile-cat.png", "Bác Sĩ Meow 🩺", f"Tuyệt vời quá! {her_name} đã uống đủ {taken_h}/{total_h} liều hôm nay rồi! {her_name} giỏi lắm! 💖", badge="Hoàn thành 100%")
    else:
        render_mascot_banner("doctor-cat.png", "Bác Sĩ Meow 🩺", f"Hôm nay có {total_h} liều thuốc, {her_name} đã uống {taken_h}/{total_h} liều. Nhớ uống đúng giờ để mau khỏe nhé! 🍵", badge=f"Còn {total_h - taken_h} liều")

    med_t1, med_t2, med_t3 = st.tabs(["🔔 Lịch Hôm Nay", "➕ Thêm Lịch Thuốc", "📋 Danh Sách Thuốc"])

    # ── Lịch hôm nay ──
    with med_t1:
        if not today_meds:
            st.markdown(f"""<div class="card" style="padding:22px;text-align:center;">
                <div style="font-size:2rem;margin-bottom:8px;">🌸</div>
                <div class="section-title" style="justify-content:center;">Hôm nay trống lịch uống thuốc!</div>
                <p style="font-size:.92rem;color:#666;line-height:1.7;margin:8px 0 16px;">
                💖 {her_name} không có liều thuốc nào cần uống trong ngày hôm nay.<br>
                Mong {her_name} luôn khỏe mạnh, tràn đầy sức sống và tươi vui! ✨<br>
                Nếu cần thêm thuốc mới, bấm tab <b>➕ Thêm Lịch Thuốc</b> hoặc dùng AI quét ảnh đơn thuốc nhé!
                </p>
            </div>""", unsafe_allow_html=True)
        else:
            total       = len(today_meds)
            taken_count = sum(1 for m in today_meds if m["taken"])
            st.progress(taken_count/total, text=f"Tiến độ hôm nay: Đã uống {taken_count}/{total} liều ({int(taken_count/total*100)}%)")
            if taken_count == total:
                st.success(f"🎉 Tuyệt vời! {her_name} đã uống đủ tất cả các liều thuốc hôm nay rồi! {her_name} giỏi lắm! 🌸")

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
                                st.success(f"{her_name} giỏi quá! 🌸")
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
                                    f"<i>Uống đúng giờ để mau khỏe nha {her_name}! 🍵</i>"
                                )
                                res = notifier.notify_her(msg, photo_path=item.get("image_path"))
                                st.success("✅ Đã gửi!") if res else st.error("❌ Gửi thất bại. Kiểm tra Bot Token & Chat ID!")

    # ── Thêm lịch thuốc ──
    with med_t2:
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

        if "med_dosage_val" not in st.session_state:
            st.session_state["med_dosage_val"] = ocr_data.get("dosage", "1 viên (sau ăn)")
        if "med_times_val" not in st.session_state:
            st.session_state["med_times_val"] = ocr_data.get("times", "08:00, 19:30")

        st.markdown('<span class="step-label">1</span> <b>Thông tin thuốc</b>', unsafe_allow_html=True)
        st.markdown('<p class="hint-text">Gợi ý liều dùng phổ biến (bấm nhanh hoặc tự nhập tùy ý):</p>', unsafe_allow_html=True)
        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        if d_col1.button("1 viên (sau ăn)", use_container_width=True, key="btn_dose_1"):
            st.session_state["med_dosage_val"] = "1 viên (sau ăn)"; st.rerun()
        if d_col2.button("2 viên (sau ăn)", use_container_width=True, key="btn_dose_2"):
            st.session_state["med_dosage_val"] = "2 viên (sau ăn)"; st.rerun()
        if d_col3.button("1 gói (trước ăn)", use_container_width=True, key="btn_dose_3"):
            st.session_state["med_dosage_val"] = "1 gói (trước ăn)"; st.rerun()
        if d_col4.button("1 viên (khi đau/sốt)", use_container_width=True, key="btn_dose_4"):
            st.session_state["med_dosage_val"] = "1 viên (khi đau/sốt)"; st.rerun()

        m1, m2 = st.columns(2)
        with m1:
            med_name   = st.text_input("Tên thuốc (*)", value=ocr_data.get("name",""),
                placeholder="VD: Panadol Extra 500mg, Vitamin C...")
        with m2:
            med_dosage = st.text_input("Liều lượng (*tùy ý chỉnh sửa mọi dạng liều*)", value=st.session_state["med_dosage_val"],
                placeholder="VD: 1 viên sau ăn, 5ml pha nước ấm...", key="med_dosage_text_input")
            st.session_state["med_dosage_val"] = med_dosage

        st.markdown('<span class="step-label">2</span> <b>Lịch uống trong ngày</b>', unsafe_allow_html=True)
        st.markdown('<p class="hint-text">⚡ <b>Lối tắt tần suất uống</b> (hoặc tự do gõ mọi khung giờ bất kỳ bên dưới):</p>', unsafe_allow_html=True)
        preset_col = st.columns(4)
        if preset_col[0].button("🌅 1 lần/ngày\n(08:00)", use_container_width=True, key="pmed_1"):
            st.session_state["med_times_val"] = "08:00"; st.rerun()
        if preset_col[1].button("☀️🌙 2 lần/ngày\n(08:00, 19:30)", use_container_width=True, key="pmed_2"):
            st.session_state["med_times_val"] = "08:00, 19:30"; st.rerun()
        if preset_col[2].button("☀️🌤️🌙 3 lần\n(8:00, 12:30, 19:30)", use_container_width=True, key="pmed_3"):
            st.session_state["med_times_val"] = "08:00, 12:30, 19:30"; st.rerun()
        if preset_col[3].button("💊 4 lần/ngày\n(7:30,12:00,17:00,21:00)", use_container_width=True, key="pmed_4"):
            st.session_state["med_times_val"] = "07:30, 12:00, 17:00, 21:00"; st.rerun()

        med_times = st.text_input("Các khung giờ uống (*nhập mọi giờ tùy thích, cách nhau bởi dấu phẩy*)", 
                                  value=st.session_state["med_times_val"], key="med_times_text_input")
        st.session_state["med_times_val"] = med_times

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
                📬 Bot Telegram sẽ nhắc {her_name} đúng giờ kèm ảnh thuốc (nếu có)
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

        st.markdown("""<div class="card" style="margin-top:14px;">
            <div class="section-title">💡 Lưu ý quan trọng khi dùng thuốc</div>
            <div style="font-size:.88rem;line-height:1.75;color:#555;">
            🕒 <b>Đúng giờ:</b> Uống đúng khung giờ đã đặt để thuốc phát huy hiệu quả tốt nhất.<br>
            🍽️ <b>Bữa ăn:</b> Thuốc sau ăn nên uống sau bữa ăn no 15-30 phút.<br>
            💧 <b>Nước uống:</b> Uống cùng 1 ly nước lọc ấm đầy đủ, tránh nằm ngay sau khi vừa uống thuốc.<br>
            📸 <b>AI Quét Đơn:</b> Dùng ảnh chụp đơn thuốc hoặc vỏ thuốc để AI tự động điền tên và liều lượng.
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
elif "Cảm Xúc" in selected_nav or "Nhật Ký" in selected_nav:
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
        "Happy":    f"Tuyệt vời quá! Chúc {her_name} luôn giữ nụ cười tươi tắn này nhé! Mèo quý {her_name} nhiều 🥰🌸",
        "Normal":   f"Một ngày bình yên trôi qua cũng là điều tuyệt vời! Cứ từ từ tận hưởng nhé {her_name} 🌸",
        "Stressed": f"Đừng quá sức nhé {her_name}! Nghỉ ngơi một chút, uống nước ấm và để Bác sĩ Mèo ôm cái nào 💖",
        "Sad":      f"Thương {her_name} lắm! Có {my_name} và Bác sĩ Mèo luôn ở bên cạnh {her_name}, mọi chuyện rồi sẽ ổn thôi 💫🧸",
        "Angry":    f"Hít thở sâu một cái nào {her_name}! Đừng để chuyện bực mình làm ảnh hưởng đến sức khỏe và nụ cười xinh nhé 🍵💖",
        "Tired":    f"Hôm nay {her_name} vất vả nhiều rồi! Mau đi ngủ sớm sạc lại năng lượng nhé, nghỉ ngơi thôi nào 😴🛌🌙",
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
    # ZONE 1: MASCOT BANNER & FORM CẬP NHẬT CẢM XÚC
    # ══════════════════════════════════════════════════════
    _cur_mood_key = st.session_state["mood_sel_mood"]
    _mood_info    = MOOD_KEY_MAP.get(_cur_mood_key, MOOD_KEY_MAP["Happy"])
    _cat_label, _bg_color, _cat_file, _cat_icon = _mood_info
    _ai_msg       = AI_RESP_MAP.get(_cur_mood_key, f"Thương {her_name} nhiều! 💖")

    st.subheader("📖 Nhật Ký & Cảm Xúc Yêu Thương")
    st.markdown(f'<p class="hint-text">Ghi lại cảm xúc mỗi ngày trong 3 giây. AI và {my_name} sẽ luôn lắng nghe, đồng hành cùng {her_name}.</p>', unsafe_allow_html=True)

    render_mascot_banner(_cat_file, f"Bác Sĩ Mèo {_cat_icon}", _ai_msg, badge=_cat_label)

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

    # 2. Chọn cảm xúc (1-Chạm Sinh Động)
    st.markdown('<p class="hint-text">⚡ <b>Chạm nhanh cảm xúc hôm nay</b>:</p>', unsafe_allow_html=True)
    mb1, mb2, mb3, mb4, mb5 = st.columns(5)
    if mb1.button("😄\nVui vẻ", use_container_width=True, key="mbtn_happy"):
        st.session_state["mood_sel_mood"] = "Happy"; st.rerun()
    if mb2.button("🌸\nBình yên", use_container_width=True, key="mbtn_normal"):
        st.session_state["mood_sel_mood"] = "Normal"; st.rerun()
    if mb3.button("😫\nStress", use_container_width=True, key="mbtn_stress"):
        st.session_state["mood_sel_mood"] = "Stressed"; st.rerun()
    if mb4.button("🥺\nBuồn", use_container_width=True, key="mbtn_sad"):
        st.session_state["mood_sel_mood"] = "Sad"; st.rerun()
    if mb5.button("😴\nMệt mỏi", use_container_width=True, key="mbtn_tired"):
        st.session_state["mood_sel_mood"] = "Tired"; st.rerun()

    # Radio hỗ trợ chọn chính xác
    mood_radio_val = st.radio(
        "Tâm trạng đang chọn:",
        options=MOOD_LABELS,
        index=MOOD_KEYS.index(st.session_state.get("mood_sel_mood", "Happy")),
        horizontal=True,
        key="diary_mood_radio",
        label_visibility="collapsed",
    )
    sel_idx = MOOD_LABELS.index(mood_radio_val)
    sel_mood_key = MOOD_KEYS[sel_idx]
    st.session_state["mood_sel_mood"] = sel_mood_key

    # 3. Ghi chú tâm sự
    mood_note_val = st.text_area(
        f"📝 Sổ nhật ký tâm sự cùng Bác sĩ Mèo & {my_name} (không bắt buộc):",
        placeholder=f"Hôm nay của {her_name} thế nào? Có điều gì làm {her_name} vui, mệt mỏi hay áp lực không? Hãy viết ra đây để nhẹ lòng nhé, {my_name} luôn lắng nghe {her_name}... 🌸",
        key="diary_note",
        height=85,
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
        ai_resp_val = AI_RESP_MAP.get(sel_mood_key, f"Thương {her_name} nhiều! 💖")
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

            # 🤫 Secret Boy Mode: Nếu cậu ấy buồn / stress / bực / mệt mỏi
            if sel_mood_key in ["Sad", "Stressed", "Angry", "Tired"]:
                try:
                    _lbl = MOOD_KEY_MAP[sel_mood_key][0]
                    _note_txt = note_clean if note_clean else "Không có ghi chú"
                    notifier.notify_you_secret(
                        f"🤫 <b>[CẢNH BÁO TÂM LÝ BÍ MẬT DÀNH CHO {my_name.upper()}]</b>\n\n"
                        f"{her_name} vừa cập nhật cảm xúc: <b>{_lbl}</b> trên App.\n"
                        f"📝 <b>Ghi chú:</b> {_note_txt}\n\n"
                        f"👉 <i>{my_name} hãy nhắn tin hỏi thăm, động viên và chuẩn bị đồ ăn ngon cho {her_name} nhé! 🍫🧸💖</i>"
                    )
                except Exception:
                    pass
            st.rerun()
        except Exception as e_save:
            st.error(f"❌ Lỗi khi lưu: {e_save}")

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
        st.markdown(stat_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CÀI ĐẶT & TELEGRAM BOT
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# TAB TÙY CHỈNH BÉ JOLYNE KUJO 🦋
# ══════════════════════════════════════════════════════════════════════════════
elif "Bé Jolyne" in selected_nav:
    mascot_manager.render_mascot_tab_ui(st, her_name=her_name, my_name=my_name)

elif "Cài Đặt" in selected_nav:
    st.subheader("⚙️ Cài Đặt Không Gian Riêng & Kết Nối")
    render_mascot_banner("chating_cat.jpg", "Góc Nhỏ Cài Đặt 🐾", f"Nơi tùy chỉnh thông tin, mật mã và kết nối tin nhắn riêng của {her_name} &amp; {my_name}!", badge="Cài đặt")

    cur = get_cached_settings()

    st.markdown(f"""<div class="card">
        <div class="section-title">📋 Hướng dẫn nhanh lấy Bot Token & Chat ID (chỉ 3 phút)</div>
        <div style="font-size:.91rem;line-height:1.75;">
        <b>Bước 1 — Tạo Bot Token:</b> Mở Telegram → tìm <b>@BotFather</b> → gửi <code>/newbot</code> → đặt tên bot → copy mã <b>HTTP API Token</b><br>
        <b>Bước 2 — Lấy Chat ID:</b> Tìm <b>@userinfobot</b> → bấm Start → bot trả về ID. Nhờ {her_name} làm tương tự để lấy ID của {her_name}.<br>
        <b>Bước 3 — Bấm Start với bot:</b> Cả hai ({her_name} và {my_name}) cần vào bot và bấm <b>/start</b> một lần để bot được phép gửi tin.
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
            her_chat   = st.text_input(f"Chat ID của {her_name} (*)",
                value=cur.get("telegram_her_chat_id",""), placeholder="VD: 987654321")
            her_name_v = st.text_input("Tên hiển thị của Cậu Ấy",
                value=cur.get("her_name","Cậu 🌸"))
        with sc2:
            my_chat   = st.text_input(f"Chat ID của {my_name} (Secret Mode)",
                value=cur.get("telegram_my_chat_id",""), placeholder="VD: 123456789")
            my_name_v = st.text_input("Tên hiển thị của Tớ",
                value=cur.get("my_name","Tớ 💫"))

        secret_on = st.toggle("🍓 Kích hoạt Secret Mode",
            value=cur.get("secret_mode_enabled", True),
            help=f"Bot tự nhắn bí mật cho {my_name} trước 4 ngày chu kỳ của {her_name}")

        st.markdown("#### 🔒 Bảo Mật & Magic Link 1-Chạm")
        sec_col1, sec_col2 = st.columns(2)
        with sec_col1:
            passcode_v = st.text_input("Mật Mã / Mã PIN Mở Khóa (*)",
                value=cur.get("app_passcode", "2010"),
                help="Mã PIN 4 số hoặc mật khẩu riêng tư để mở khóa app")
        with sec_col2:
            web_url_v = st.text_input("Địa Chỉ Web Public (Nếu có)",
                value=cur.get("web_app_url", ""),
                placeholder="VD: https://duanbimat.streamlit.app",
                help="Dùng để tự động tạo Magic Link 1-chạm gửi qua Telegram")

        st.markdown("#### 🌤️ Dự Báo Thời Tiết Buổi Sáng (Open-Meteo)")
        CITY_COORDS = {
            "Hà Nội": (21.0285, 105.8542),
            "TP. Hồ Chí Minh": (10.8231, 106.6297),
            "Đà Nẵng": (16.0544, 108.2022),
            "Hải Phòng": (20.8449, 106.6881),
            "Cần Thơ": (10.0452, 105.7469),
            "Huế": (16.4637, 107.5909),
            "Nha Trang": (12.2388, 109.1967),
            "Đà Lạt": (11.9404, 108.4583),
        }
        current_city = cur.get("weather_city", "Hà Nội")
        city_list = list(CITY_COORDS.keys())
        city_idx = city_list.index(current_city) if current_city in city_list else 0
        wt_col1, wt_col2 = st.columns(2)
        with wt_col1:
            sel_city = st.selectbox("Tỉnh / Thành phố dự báo (*)", city_list, index=city_idx,
                help=f"Chọn thành phố của {her_name} để nhận lời chúc chuẩn theo thời tiết")
        with wt_col2:
            st.markdown(f'<div style="font-size:0.85rem;color:#666;margin-top:28px;">📍 Tọa độ: <b>{CITY_COORDS[sel_city][0]}, {CITY_COORDS[sel_city][1]}</b> (0MB ổ cứng, 0% CPU)</div>', unsafe_allow_html=True)

        st.markdown(f"#### 📌 Ghim Mảnh Giấy Nhớ Cho {her_name} (Sticky Note)")
        pinned_input_val = st.text_area(
            f"Nội dung lời nhắn ghim lên đầu trang chủ của {her_name}:",
            value=cur.get("pinned_note", ""),
            placeholder=f"VD: Chiều nay đi học về {my_name} qua đón {her_name} đi ăn kem nhé!...",
            help=f"Lời nhắn này sẽ hiện nổi bật ở đầu trang chủ cho đến khi {her_name} bấm 'Đã đọc' mới biến mất và giải phóng bộ nhớ.",
            height=70
        )

        if st.form_submit_button("💾 Lưu Tất Cả Cài Đặt", use_container_width=True):
            _old_pinned = cur.get("pinned_note", "").strip()
            _new_pinned = pinned_input_val.strip()
            _pin_time = cur.get("pinned_note_time", "")
            if _new_pinned and _new_pinned != _old_pinned:
                _pin_time = config.get_now().strftime("%d/%m %H:%M")
            elif not _new_pinned:
                _pin_time = ""

            cur.update({
                "telegram_bot_token":    bot_token.strip(),
                "telegram_her_chat_id":  her_chat.strip(),
                "telegram_my_chat_id":   my_chat.strip(),
                "her_name":              her_name_v.strip(),
                "my_name":               my_name_v.strip(),
                "secret_mode_enabled":   secret_on,
                "app_passcode":          passcode_v.strip() if passcode_v.strip() else "2010",
                "web_app_url":           web_url_v.strip(),
                "weather_city":          sel_city,
                "weather_latitude":      CITY_COORDS[sel_city][0],
                "weather_longitude":     CITY_COORDS[sel_city][1],
                "pinned_note":           _new_pinned,
                "pinned_note_time":      _pin_time,
            })
            if config.save_settings(cur):
                invalidate_cache()
                st.success("✅ Đã lưu cấu hình!")
                st.rerun()

    # ── Hộp hiển thị Magic Link tiện lợi ──
    _cur_passcode = cur.get("app_passcode", "2010")
    _cur_web_url = cur.get("web_app_url", "").strip()
    _sample_base = _cur_web_url if _cur_web_url else "https://your-domain.streamlit.app"
    _magic_link_full = f"{_sample_base.rstrip('/')}/?key={_cur_passcode}"

    st.markdown(f"""
    <div class="card" style="margin-top: 14px; background: #fffcfd; border: 1.5px solid #ffccd5;">
        <div class="section-title">✨ Magic Link 1-Chạm Dành Cho {her_name}</div>
        <p style="font-size: 0.88rem; color: #555; line-height: 1.6; margin-bottom: 8px;">
            Gửi đường link này cho {her_name} (hoặc lưu vào Bookmark / Màn hình chính điện thoại). Khi bấm vào, web sẽ <b>tự động mở khóa ngay lập tức</b> mà không bao giờ bị hỏi mật khẩu:
        </p>
        <div style="background: white; border: 1px dashed #ff758c; padding: 10px 14px; border-radius: 10px; font-family: monospace; font-size: 0.88rem; color: #d81159; word-break: break-all; margin-bottom: 10px;">
            {_magic_link_full}
        </div>
        <p style="font-size: 0.8rem; color: #888; margin: 0;">
            🔒 <i>Người ngoài truy cập link gốc không có <code>?key={_cur_passcode}</code> sẽ lập tức bị chặn ở màn hình khóa Mèo bảo vệ!</i>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🧪 Kiểm Tra Thông Báo Yêu Thương (Telegram)")
    tt1, tt2, tt3 = st.columns(3)
    with tt1:
        if st.button(f"📤 Gửi Test → {her_name}", use_container_width=True):
            res = notifier.notify_her(f"💖 Xin chào {her_name}! Trợ Lý Yêu Thương đang hoạt động và luôn ở bên {her_name}! 🌸")
            st.success("✅ Gửi thành công!") if res else st.error("❌ Gửi thất bại. Kiểm tra Bot Token & Chat ID, nhớ bấm /start!")
    with tt2:
        if st.button(f"🍓 Gửi Test Secret Mode ({my_name})", use_container_width=True):
            res2 = notifier.notify_you_secret(f"🍓 [SECRET MODE] Kênh bí mật của {my_name} hoạt động hoàn hảo!")
            st.success("✅ Secret Mode OK!") if res2 else st.error(f"❌ Thất bại. Kiểm tra Chat ID của {my_name}!")
    with tt3:
        if st.button("🎉 Kích Hoạt Lời Chúc Mừng", use_container_width=True):
            cur2 = get_cached_settings()
            cur2["startup_greeting_sent"] = False
            config.save_settings(cur2)
            invalidate_cache()
            scheduler.check_and_send_startup_greeting()
            st.success(f"Đã bắn lời chúc ngọt ngào tới {her_name}!")

    tb1, tb2 = st.columns(2)
    with tb1:
        if st.button("☀️ Test Gửi Chào Buổi Sáng (7:00 AM)", use_container_width=True):
            morning_msg = scheduler.build_good_morning_message()
            res_m = notifier.notify_her(morning_msg)
            if res_m:
                st.success(f"✅ Đã gửi tin nhắn Chào Buổi Sáng tới Telegram của {her_name}!")
            else:
                st.error("❌ Gửi thất bại. Hãy kiểm tra cấu hình Bot Token & Chat ID!")
    with tb2:
        if st.button("🌙 Test Gửi Chúc Ngủ Ngon (22:30 PM - Theo Mood)", use_container_width=True):
            night_msg = scheduler.build_good_night_message()
            res_n = notifier.notify_her(night_msg)
            if res_n:
                st.success(f"✅ Đã gửi tin nhắn Chúc Ngủ Ngon (cá nhân hóa theo cảm xúc) tới Telegram của {her_name}!")
            else:
                st.error("❌ Gửi thất bại. Hãy kiểm tra cấu hình Bot Token & Chat ID!")

    tb3, tb4 = st.columns(2)
    with tb3:
        if st.button("📊 Test Báo Cáo Tuần (Chủ Nhật 20:00)", use_container_width=True):
            recap_msg = scheduler.build_weekly_recap_message()
            res_rc = notifier.notify_her(recap_msg)
            if res_rc:
                st.success(f"✅ Đã gửi Báo Cáo Tuần sinh động tới Telegram của {her_name}!")
            else:
                st.error("❌ Gửi thất bại. Kiểm tra Bot Token & Chat ID!")
    with tb4:
        if st.button(f"💾 Test Sao Lưu CSDL & Gửi về Telegram {my_name}", use_container_width=True):
            res_bk = scheduler.backup_database_to_telegram()
            if res_bk:
                st.success(f"✅ Đã sao lưu dữ liệu CSDL và gửi file về Telegram của {my_name}!")
            else:
                st.error(f"❌ Sao lưu thất bại. Hãy kiểm tra Chat ID của {my_name} (Secret Mode)!")

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-footer">
    <b>Trợ Lý Yêu Thương</b> &nbsp;•&nbsp; Luôn đồng hành cùng {her_name} mỗi ngày
</div>
""", unsafe_allow_html=True)
