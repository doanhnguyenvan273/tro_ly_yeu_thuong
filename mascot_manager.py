"""
mascot_manager.py
=================
Quản lý nhân vật đồng hành Chibi Jolyne Kujo (JoJo Part 6: Stone Ocean)
- 12 hành động chuẩn định dạng WebP siêu nhẹ (/app/static/mascot/)
- Animation lơ lửng 100% Pure CSS (jolyneFloat) nhấp nhô mượt mà trên GPU
- Hiệu ứng Stand Menacing (ゴゴゴゴ) thuần CSS bay bổng bên phải nhân vật
- Giữ vị trí cố định XUYÊN SUỐT MỌI TRANG bằng localStorage (kéo ở đâu, mọi tab đều giữ nguyên ở đó)
- Kéo thả mượt mà trên TẤT CẢ CÁC TRANG bằng Event Delegation trên window.parent.document
- Tự động phản ứng thông minh theo các tab (Lịch học, Deadline, Chu kỳ, Đơn thuốc, Cảm xúc)
- Ăn mừng khi hoàn thành deadline (victory pose)
"""

import os
import json
import random
import time
import copy
import html
import base64
from pathlib import Path
from typing import Dict, List, Any

_MASCOT_BASE_DIR = Path(__file__).resolve().parent
_MASCOT_STATIC_DIR = _MASCOT_BASE_DIR / 'static' / 'mascot'
_SPRITE_B64_CACHE: Dict[str, str] = {}

def get_sprite_url(act: str) -> str:
    """Trả về Base64 Data URI cho sprite hành động của bé Jolyne, khắc phục triệt để lỗi ảnh vỡ trên Streamlit Cloud."""
    if act in _SPRITE_B64_CACHE:
        return _SPRITE_B64_CACHE[act]
    for ext in ('webp', 'png'):
        fpath = _MASCOT_STATIC_DIR / f'jolyne_{act}.{ext}'
        if fpath.exists():
            try:
                b64 = base64.b64encode(fpath.read_bytes()).decode('ascii')
                mime = 'image/webp' if ext == 'webp' else 'image/png'
                data_uri = f'data:{mime};base64,{b64}'
                _SPRITE_B64_CACHE[act] = data_uri
                return data_uri
            except Exception:
                pass
    fallback = f'/app/static/mascot/jolyne_{act}.webp'
    _SPRITE_B64_CACHE[act] = fallback
    return fallback

SETTINGS_PATH = os.path.join("data", "mascot_settings.json")
MASCOT_DIR = os.path.join("static", "mascot")

ACTION_LABELS = {
    "idle": ("✨", "Đứng Chờ (Mặc định)"),
    "med": ("💊", "Nhắc Uống Thuốc"),
    "water": ("🍵", "Nhắc Uống Nước"),
    "victory": ("🎉", "Xong Deadline"),
    "fight": ("👊", "Diệt Deadline (Quyết tâm)"),
    "panic": ("🙀", "Trễ Hạn Nani?!"),
    "study": ("📚", "Đi Học / Bài Vở"),
    "period": ("🌸", "Đèn Đỏ / Giữ Ấm"),
    "hug": ("🧸", "An Ủi / Ôm Gấu"),
    "morning": ("☀️", "Chào Buổi Sáng"),
    "sleep": ("🌙", "Chúc Ngủ Ngon"),
    "shy": ("👉👈", "Bị Chọc E Thẹn"),
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "size": 95,
    "speed": 3.2,
    "gogo_enabled": True,
    "auto_hide_seconds": 4.5,
    "dialogues": {
        "idle": [
            "Chào {her_name}! Tớ là Jolyne Kujo, người bạn bảo vệ cậu 24/7 nè! 🦋✨",
            "Hôm nay {her_name} thấy thế nào? Cần gì cứ gọi tớ nhé!",
            "{my_name} dặn tớ phải luôn ở đây trông chừng và chăm sóc cho {her_name} đó nha! 🥰"
        ],
        "med": [
            "{her_name} ơi, đến giờ uống thuốc rồi nè! Đừng quên uống đúng giờ để mau khỏe nha! 💊✨",
            "Uống thuốc xong nhớ uống thật nhiều nước ấm nhé {her_name}! {my_name} luôn lo cho cậu đó! 🌸",
            "Bé ngoan nào, uống thuốc đúng liều lượng nha! Tớ và {my_name} đang dõi theo cậu nè! 🧸"
        ],
        "water": [
            "{her_name} nhớ uống nước đều đặn nha! 1 ly nước ấm cho làn da luôn xinh đẹp nào! 🍵✨",
            "Uống nước đi nào {her_name} ơi! Cấp ẩm cho cơ thể để học tập thật hiệu quả nhé! 💧🌸",
            "Mỗi ngày 2 lít nước ấm nha {her_name}! {my_name} gửi lời nhắc yêu thương nè! 💖"
        ],
        "victory": [
            "YAYYY! Chúc mừng {her_name} đã xong deadline xuất sắc! Quá đỉnh luônnn! 🎉🥳",
            "Hoàn thành xong rồi nè! {her_name} của {my_name} giỏi nhất trên đời! Tự thưởng cho mình thôi nào! 💖🏆",
            "Deadline đã bị tiêu diệt sạch sẽ! Đi nghỉ ngơi thư giãn thôi {her_name} ơi! 🌸"
        ],
        "fight": [
            "ORA ORA ORA! Cố lên {her_name} ơi, deadline này không có cửa làm khó cậu đâu! 👊🔥",
            "Tiến lên nào {her_name}! Tập trung một chút là xong ngay, {my_name} luôn tin tưởng cậu! ✨",
            "Stand Stone Free xuất trận! Đập tan mọi bài tập khó nhằn nhé {her_name}! 🦋💥"
        ],
        "panic": [
            "NANI?! Deadline sát nút rồi sao {her_name}?! Mau tập trung nào, tớ sẽ đứng đây cổ vũ cậu hết mình! 🙀⏰",
            "Bình tĩnh nào {her_name} ơi! Hít một hơi thật sâu, tớ và Stand Stone Free sẽ hỗ trợ cậu! 💪✨",
            "Đừng hoảng loạn nha {her_name}! Chia nhỏ việc ra làm từng bước, cậu sẽ làm kịp thôi! 🔥"
        ],
        "study": [
            "Học bài chăm chỉ nào {her_name}! Tương lai rực rỡ đang chờ đón cậu đó! 📚✨",
            "Học tập thật tốt nha {her_name}, mệt thì nghỉ ngơi xíu chứ đừng cố quá nhé! ☕💖",
            "Kiến thức là sức mạnh! {my_name} luôn tự hào về sự chăm chỉ của {her_name} đó! 🌟"
        ],
        "period": [
            "Ngày dâu tới rồi... {her_name} nhớ giữ ấm bụng, chườm ấm và nghỉ ngơi thật nhiều nhé! 🌸🧸",
            "Những ngày này {her_name} đừng làm việc nặng nha, uống trà ấm và để {my_name} chăm sóc cậu nhé! 🍵💗",
            "Ngoan ngoãn nghỉ ngơi, giữ ấm chân tay nhé {her_name}! Có mệt mỏi cứ nhắn cho {my_name} liền nha! 💖"
        ],
        "hug": [
            "Có chuyện gì buồn hả {her_name}? Cho tớ ôm một cái thật chặt nàooo! 🧸💖",
            "Đừng lo lắng nhé {her_name}, mọi chuyện rồi sẽ ổn thôi vì luôn có {my_name} ở bên cậu mà! 🌸✨",
            "Gửi ngàn cái ôm ấm áp tới {her_name}! Cậu là điều tuyệt vời nhất! 💕"
        ],
        "morning": [
            "Chào buổi sáng {her_name}! Chúc cậu một ngày mới thật nhiều năng lượng và may mắn! ☀️🌸",
            "Dậy thôi nào {her_name} ơi! {my_name} vừa gửi lời chúc ngọt ngào nhất tới cậu đó! 💖✨",
            "Một ngày mới tuyệt vời lại bắt đầu! Chúc {her_name} luôn mỉm cười rạng rỡ nha! 🌻"
        ],
        "sleep": [
            "Khuya rồi, mau đi ngủ thôi {her_name} ơi! Ngủ một giấc thật sâu để mai nạp đầy năng lượng nhé! 😴🌙",
            "Chúc {her_name} ngủ thật ngon và có những giấc mơ tuyệt đẹp nha! Khò khò~ 💤🧸",
            "Đắp chăn ấm và nhắm mắt lại thôi nào, {my_name} chúc {her_name} ngủ ngoan nhé! 💫"
        ],
        "shy": [
            "Hì hì, {her_name} chọc tớ à? Ngại ghê á~ 👉👈🌸",
            "Sao cứ bấm vào tớ hoài thế nè? Nhớ tớ hay nhớ {my_name} thế? 🥰🦋",
            "{my_name} dặn tớ phải canh chừng {her_name} thật chu đáo đó nha! 🦋✨"
        ]
    }
}


def get_mascot_settings(st_module=None) -> Dict[str, Any]:
    """Đọc cấu hình mascot từ file JSON, ưu tiên giá trị tương tác thời gian thực từ session_state."""
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            if "dialogues" in data:
                for dk, dv in DEFAULT_SETTINGS["dialogues"].items():
                    if dk not in data["dialogues"]:
                        data["dialogues"][dk] = dv
            settings = data
        except Exception:
            settings = DEFAULT_SETTINGS.copy()
    else:
        save_mascot_settings(DEFAULT_SETTINGS)

    # Ưu tiên các giá trị người dùng đang kéo trượt thời gian thực trong session_state
    if st_module is not None and hasattr(st_module, "session_state"):
        ss = st_module.session_state
        if "mascot_size_slider" in ss:
            settings["size"] = ss["mascot_size_slider"]
        if "mascot_speed_slider" in ss:
            settings["speed"] = ss["mascot_speed_slider"]
        if "mascot_enabled_toggle" in ss:
            settings["enabled"] = ss["mascot_enabled_toggle"]
        if "mascot_gogo_toggle" in ss:
            settings["gogo_enabled"] = ss["mascot_gogo_toggle"]

    return settings


def save_mascot_settings(settings: Dict[str, Any]) -> None:
    """Lưu cấu hình mascot vào data/mascot_settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def render_floating_mascot(
    st_module,
    her_name: str,
    my_name: str,
    action: str = "idle",
) -> None:
    """
    Render bé Jolyne Kujo lơ lửng:
    1. HTML/CSS với z-index: 2147483647 (cao nhất tuyệt đối).
    2. Teleport trực tiếp ra document.body để nằm trên tất cả card, tabs, modals.
    3. Giữ nguyên tọa độ (x, y) xuyên suốt tất cả các trang bằng localStorage & CSS vars.
    4. MỖI KHI ĐỔI ACTION/TAB: LUÔN CÓ BÓNG THOẠI HIỆN LÊN RỰC RỠ VỚI CÂU NÓI PHÙ HỢP.
    """
    settings = get_mascot_settings(st_module)
    if not settings.get("enabled", True):
        # Ẩn hoặc dọn dẹp widget nếu tắt bé Jolyne
        st_module.markdown(
            """<img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'></svg>" style="display:none!important;" onload="try{var w=window.parent.document.getElementById('jolyneWidget');if(w)w.style.display='none';}catch(e){}" />""",
            unsafe_allow_html=True,
        )
        return

    size = int(settings.get("size", 95))
    speed = float(settings.get("speed", 3.2))
    gogo_enabled = bool(settings.get("gogo_enabled", True))
    auto_hide_sec = float(settings.get("auto_hide_seconds", 4.5))

    raw_dialogues = settings.get("dialogues", {})
    act_lines = [l.strip() for l in raw_dialogues.get(action, []) if l and l.strip()]
    if not act_lines:
        act_lines = DEFAULT_SETTINGS["dialogues"].get(action, DEFAULT_SETTINGS["dialogues"]["idle"])

    selected_line = random.choice(act_lines).replace("{her_name}", her_name).replace("{my_name}", my_name)
    escaped_selected_line = html.escape(selected_line, quote=True)

    all_formatted_dialogues = {}
    for k_act, lines in raw_dialogues.items():
        all_formatted_dialogues[k_act] = [
            l.replace("{her_name}", her_name).replace("{my_name}", my_name)
            for l in lines if l and l.strip()
        ]
        if not all_formatted_dialogues[k_act]:
            all_formatted_dialogues[k_act] = [
                l.replace("{her_name}", her_name).replace("{my_name}", my_name)
                for l in DEFAULT_SETTINGS["dialogues"].get(k_act, ["Xin chào! 🌸"])
            ]

    sprite_map = {
        k_act: get_sprite_url(k_act)
        for k_act in ACTION_LABELS.keys()
    }

    current_sprite_url = get_sprite_url(action)
    idle_sprite_url = get_sprite_url("idle")
    gogo_display = "block" if gogo_enabled else "none"

    # PHẦN 1: CSS & HTML nguyên bản không chứa khoảng trắng thụt lề đầu dòng
    raw_css_html = f"""<style>
.jolyne-floating-container {{
position: fixed !important;
bottom: 24px !important;
right: 24px !important;
z-index: 2147483647 !important;
pointer-events: none !important;
display: flex !important;
flex-direction: column !important;
align-items: flex-end !important;
user-select: none !important;
-webkit-user-select: none !important;
will-change: transform !important;
transform: translate3d(var(--jolyne-x, 0px), var(--jolyne-y, 0px), 0) !important;
}}

.jolyne-floating-container.is-dragging,
.jolyne-floating-container.is-dragging .jolyne-avatar-wrap {{
cursor: grabbing !important;
}}

.jolyne-speech-bubble {{
background: rgba(255, 255, 255, 0.98) !important;
backdrop-filter: blur(16px) !important;
-webkit-backdrop-filter: blur(16px) !important;
border: 2px solid #ffd1dc !important;
border-radius: 18px 18px 4px 18px !important;
padding: 12px 16px !important;
box-shadow: 0 10px 30px rgba(216, 17, 89, 0.18) !important;
color: #9d174d !important;
font-size: 0.88rem !important;
line-height: 1.5 !important;
font-weight: 600 !important;
max-width: 260px !important;
margin-bottom: 8px !important;
margin-right: 14px !important;
opacity: 1 !important;
visibility: visible !important;
pointer-events: auto !important;
cursor: pointer !important;
transform-origin: bottom right !important;
transform: scale(1) translate3d(0, 0, 0) !important;
transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
position: relative !important;
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
z-index: 2147483647 !important;
}}

.jolyne-speech-bubble.hide-bubble {{
opacity: 0 !important;
visibility: hidden !important;
pointer-events: none !important;
transform: scale(0.6) translate3d(0, 10px, 0) !important;
}}

.jolyne-speech-bubble::after {{
content: "" !important;
position: absolute !important;
bottom: -8px !important;
right: 28px !important;
width: 12px !important;
height: 12px !important;
background: white !important;
border-right: 2px solid #ffd1dc !important;
border-bottom: 2px solid #ffd1dc !important;
transform: rotate(45deg) !important;
}}

.jolyne-avatar-wrap {{
position: relative !important;
pointer-events: auto !important;
cursor: grab !important;
touch-action: none !important;
transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
z-index: 2147483647 !important;
}}

.jolyne-avatar-img {{
width: {size}px !important;
height: auto !important;
display: block !important;
filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.16)) !important;
animation: jolyneFloat {speed}s ease-in-out infinite alternate !important;
will-change: transform !important;
transform-origin: bottom center !important;
transition: opacity 0.2s ease !important;
user-select: none !important;
-webkit-user-select: none !important;
-webkit-user-drag: none !important;
pointer-events: none !important;
}}

.drag-hint {{
position: absolute !important;
top: -24px !important;
left: 50% !important;
transform: translateX(-50%) scale(0) !important;
background: rgba(244, 63, 94, 0.90) !important;
color: white !important;
font-size: 0.68rem !important;
font-weight: 700 !important;
padding: 3px 10px !important;
border-radius: 20px !important;
white-space: nowrap !important;
pointer-events: none !important;
transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
z-index: 2147483647 !important;
font-family: sans-serif !important;
}}

.jolyne-avatar-wrap:hover .drag-hint {{
transform: translateX(-50%) scale(1) !important;
}}

@keyframes jolyneFloat {{
0%   {{ transform: translate3d(0, 0, 0) rotate(0deg); }}
50%  {{ transform: translate3d(0, -8px, 0) rotate(-1.5deg); }}
100% {{ transform: translate3d(0, -3px, 0) rotate(1.5deg); }}
}}

/* Stand Menacing Effect (ゴゴゴゴ) BÊN PHẢI NHÂN VẬT */
.gogo-container {{
position: absolute !important;
left: 100% !important;
bottom: 0 !important;
width: 60px !important;
height: 120% !important;
pointer-events: none !important;
z-index: 2147483647 !important;
overflow: visible !important;
display: {gogo_display} !important;
}}

.gogo-glyph {{
position: absolute !important;
font-family: 'Noto Sans JP', 'MS Gothic', sans-serif, serif !important;
font-weight: 900 !important;
font-style: italic !important;
background: linear-gradient(165deg, #e879f9 0%, #a855f7 35%, #6b21a8 75%, #3b0764 100%) !important;
-webkit-background-clip: text !important;
-webkit-text-fill-color: transparent !important;
background-clip: text !important;
filter: drop-shadow(0 0 5px rgba(216, 70, 239, 0.75))
        drop-shadow(1.5px 2.5px 0 rgba(0, 0, 0, 0.6)) !important;
will-change: transform, opacity !important;
user-select: none !important;
letter-spacing: -2px !important;
opacity: 0;
line-height: 1 !important;
}}

@keyframes gogoFloat0 {{
0%   {{ transform: translate3d(0, 0, 0) rotate(-10deg) scale(0.95); opacity: 0; }}
18%  {{ opacity: 0.95; }}
55%  {{ transform: translate3d(6px, -18px, 0) rotate(-14deg) scale(1.08); opacity: 0.85; }}
100% {{ transform: translate3d(12px, -36px, 0) rotate(-8deg) scale(0.80); opacity: 0; }}
}}
@keyframes gogoFloat1 {{
0%   {{ transform: translate3d(0, 0, 0) rotate(8deg) scale(0.90); opacity: 0; }}
15%  {{ opacity: 0.90; }}
50%  {{ transform: translate3d(8px, -14px, 0) rotate(12deg) scale(1.02); opacity: 0.80; }}
100% {{ transform: translate3d(4px, -32px, 0) rotate(6deg) scale(0.75); opacity: 0; }}
}}
@keyframes gogoFloat2 {{
0%   {{ transform: translate3d(0, 0, 0) rotate(-6deg) scale(1.10); opacity: 0; }}
20%  {{ opacity: 0.95; }}
55%  {{ transform: translate3d(10px, -12px, 0) rotate(-9deg) scale(1.18); opacity: 0.88; }}
100% {{ transform: translate3d(15px, -28px, 0) rotate(-4deg) scale(0.88); opacity: 0; }}
}}
@keyframes gogoFloat3 {{
0%   {{ transform: translate3d(0, 0, 0) rotate(14deg) scale(0.85); opacity: 0; }}
16%  {{ opacity: 0.85; }}
55%  {{ transform: translate3d(7px, -15px, 0) rotate(18deg) scale(0.96); opacity: 0.75; }}
100% {{ transform: translate3d(11px, -34px, 0) rotate(12deg) scale(0.70); opacity: 0; }}
}}
@keyframes gogoFloat4 {{
0%   {{ transform: translate3d(0, 0, 0) rotate(-16deg) scale(0.75); opacity: 0; }}
14%  {{ opacity: 0.80; }}
50%  {{ transform: translate3d(5px, -10px, 0) rotate(-20deg) scale(0.85); opacity: 0.70; }}
100% {{ transform: translate3d(8px, -24px, 0) rotate(-12deg) scale(0.60); opacity: 0; }}
}}

/* Ẩn hoàn toàn iframe controller */
iframe[height="0"] {{
display: none !important;
width: 0 !important;
height: 0 !important;
border: none !important;
position: absolute !important;
}}
</style>

<div class="jolyne-floating-container" id="jolyneWidget"
     data-action="{action}"
     data-line="{escaped_selected_line}"
     data-sprite="{current_sprite_url}"
     data-idle="{idle_sprite_url}"
     data-size="{size}"
     data-speed="{speed}"
     data-gogo="{gogo_display}"
     data-autohide="{auto_hide_sec}">
<div class="jolyne-speech-bubble" id="jolyneBubble" title="Bấm để ẩn thoại">
{selected_line}
</div>
<div class="jolyne-avatar-wrap" id="jolyneWrap">
<div class="drag-hint">✥ kéo để di chuyển</div>
<div class="gogo-container" id="gogoContainer">
<div class="gogo-glyph" style="font-size:2.1rem;bottom:78%;left:4px;animation:gogoFloat0 2.3s ease-in-out infinite 0s both;">ゴ</div>
<div class="gogo-glyph" style="font-size:1.6rem;bottom:60%;left:14px;animation:gogoFloat1 2.7s ease-in-out infinite 0.4s both;">ゴ</div>
<div class="gogo-glyph" style="font-size:1.3rem;bottom:43%;left:8px;animation:gogoFloat2 2.1s ease-in-out infinite 0.75s both;">ゴ</div>
<div class="gogo-glyph" style="font-size:1.05rem;bottom:27%;left:18px;animation:gogoFloat3 2.9s ease-in-out infinite 1.05s both;">ゴ</div>
<div class="gogo-glyph" style="font-size:0.82rem;bottom:12%;left:10px;animation:gogoFloat4 2.5s ease-in-out infinite 1.35s both;">ゴ</div>
</div>
<img src="{current_sprite_url}" id="jolyneImg" class="jolyne-avatar-img" alt="Jolyne Chibi" draggable="false" />
</div>
</div>
<img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'></svg>" style="display:none!important;" onload="try{{if(window.parent&&window.parent.__jolyne_fast_sync)window.parent.__jolyne_fast_sync(this);}}catch(e){{}}" />
"""

    clean_html = "\n".join(line.strip() for line in raw_css_html.splitlines() if line.strip())
    st_module.markdown(clean_html, unsafe_allow_html=True)

    # PHẦN 2: JAVASCRIPT RUNTIME & CONTROLLER (CHẠY TRỰC TIẾP TRÊN PARENT WINDOW)
    ts = int(time.time() * 1000)

    js_template = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
(function() {
    try {
        var pDoc = window.parent.document;
        var pWin = window.parent;
        if (!pDoc || !pWin) return;

        // 1. Khởi tạo Script Runtime vĩnh viễn trên pDoc (sống độc lập với iframe của Streamlit)
        if (!pDoc.getElementById('jolyne-runtime-core')) {
            var sc = pDoc.createElement('script');
            sc.id = 'jolyne-runtime-core';
            sc.textContent = `
            (function() {
                if (window.__jolyne_core_initialized) return;
                window.__jolyne_core_initialized = true;

                var pDoc = window.document;

                // Inject style toàn cục vào head với z-index cao nhất
                if (!pDoc.getElementById('jolyne-global-style')) {
                    var gs = pDoc.createElement('style');
                    gs.id = 'jolyne-global-style';
                    gs.textContent = '#jolyneWidget { position: fixed !important; z-index: 2147483647 !important; pointer-events: none !important; bottom: 24px !important; right: 24px !important; } #jolyneWidget * { box-sizing: border-box !important; } #jolyneWidget .jolyne-avatar-wrap, #jolyneWidget .jolyne-speech-bubble { pointer-events: auto !important; } [data-testid="manage-app-button"], .viewerBadge, [class*="viewerBadge"], [class*="ManageApp"], [class*="FloatingActionButton"], [class*="floatingActionButton"], iframe[title*="manage" i] { display: none !important; opacity: 0 !important; visibility: hidden !important; pointer-events: none !important; }';
                    pDoc.head.appendChild(gs);
                }

                // A. Đọc và áp dụng tọa độ đã lưu vào CSS variables (--jolyne-x, --jolyne-y)
                function hideStreamlitCloudBadges() {
                    try {
                        var sels = ['[data-testid="manage-app-button"]', '.viewerBadge', '[class*="viewerBadge"]', '[class*="ManageApp"]', '[class*="FloatingActionButton"]', '[class*="floatingActionButton"]', 'iframe[title*="manage" i]'];
                        sels.forEach(function(s) {
                            var els = pDoc.querySelectorAll(s);
                            els.forEach(function(el) {
                                el.style.setProperty('display', 'none', 'important');
                                el.style.setProperty('visibility', 'hidden', 'important');
                                el.style.setProperty('opacity', '0', 'important');
                                el.style.setProperty('pointer-events', 'none', 'important');
                            });
                        });
                    } catch(e) {}
                }
                hideStreamlitCloudBadges();
                setInterval(hideStreamlitCloudBadges, 2000);

                function initSavedPos() {
                    try {
                        var s = JSON.parse(localStorage.getItem('jolyne_pos_v2'));
                        if (s && typeof s.x === 'number' && typeof s.y === 'number') {
                            pDoc.documentElement.style.setProperty('--jolyne-x', s.x + 'px');
                            pDoc.documentElement.style.setProperty('--jolyne-y', s.y + 'px');
                            var w = pDoc.getElementById('jolyneWidget');
                            if (w) w.style.transform = 'translate3d(' + s.x + 'px, ' + s.y + 'px, 0)';
                        }
                    } catch(e) {}
                }
                initSavedPos();

                // B. Đảm bảo vị trí luôn trong khung nhìn khi co giãn cửa sổ
                function clampPos(x, y) {
                    var winW = window.innerWidth || 1024;
                    var winH = window.innerHeight || 768;
                    var minX = -(winW - 80);
                    var maxX = 16;
                    var minY = -(winH - 80);
                    var maxY = 16;
                    return {
                        x: Math.max(minX, Math.min(maxX, x)),
                        y: Math.max(minY, Math.min(maxY, y))
                    };
                }

                window.addEventListener('resize', function() {
                    var curX = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    var curY = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-y')) || 0;
                    var c = clampPos(curX, curY);
                    if (c.x !== curX || c.y !== curY) {
                        pDoc.documentElement.style.setProperty('--jolyne-x', c.x + 'px');
                        pDoc.documentElement.style.setProperty('--jolyne-y', c.y + 'px');
                        try { localStorage.setItem('jolyne_pos_v2', JSON.stringify(c)); } catch(e) {}
                    }
                });

                // C. MASTER SYNC FUNCTION: ĐẢM BẢO NHÂN VẬT LUÔN Ở LỚP TRÊN CÙNG (pDoc.body) & CÓ THOẠI KHI ĐỔI ACTION
                window.__jolyne_sync = function(cfg) {
                    if (!pDoc || !pDoc.body) return;

                    // 1. Tìm hoặc dịch chuyển #jolyneWidget trực tiếp ra pDoc.body
                    var bodyWidget = null;
                    var allWidgets = pDoc.querySelectorAll('#jolyneWidget');

                    for (var i = 0; i < allWidgets.length; i++) {
                        if (allWidgets[i].parentElement === pDoc.body) {
                            bodyWidget = allWidgets[i];
                            break;
                        }
                    }

                    var innerWidget = null;
                    for (var j = 0; j < allWidgets.length; j++) {
                        if (allWidgets[j].parentElement !== pDoc.body) {
                            innerWidget = allWidgets[j];
                            break;
                        }
                    }

                    var targetWidget = bodyWidget;
                    if (!bodyWidget) {
                        if (innerWidget) {
                            pDoc.body.appendChild(innerWidget);
                            targetWidget = innerWidget;
                        }
                    } else {
                        if (innerWidget) {
                            // Đã có widget cố định trên body, dọn bản sao bên trong Streamlit container
                            try { innerWidget.parentElement.removeChild(innerWidget); } catch(e) {}
                        }
                    }

                    if (!targetWidget) return;

                    // Ép z-index cao nhất tuyệt đối (2147483647) và cố định trên màn hình
                    targetWidget.style.setProperty('z-index', '2147483647', 'important');
                    targetWidget.style.setProperty('position', 'fixed', 'important');
                    targetWidget.style.setProperty('pointer-events', 'none', 'important');
                    targetWidget.style.setProperty('display', 'flex', 'important');

                    // Đồng bộ tọa độ transform
                    try {
                        var s = JSON.parse(localStorage.getItem('jolyne_pos_v2'));
                        if (s && typeof s.x === 'number' && typeof s.y === 'number') {
                            pDoc.documentElement.style.setProperty('--jolyne-x', s.x + 'px');
                            pDoc.documentElement.style.setProperty('--jolyne-y', s.y + 'px');
                            targetWidget.style.transform = 'translate3d(' + s.x + 'px, ' + s.y + 'px, 0)';
                        }
                    } catch(e) {}

                    if (!cfg) return;

                    if (cfg.action) window.__jolyne_current_action = cfg.action;
                    if (cfg.dialogues) window.__jolyne_all_dialogues = cfg.dialogues;
                    if (cfg.idleUrl) window.__jolyne_idle_url = cfg.idleUrl;
                    if (cfg.spriteMap) window.__jolyne_sprite_map = cfg.spriteMap;
                    if (cfg.autoHideSec) window.__jolyne_auto_hide_sec = cfg.autoHideSec;

                    // Cập nhật sprite ảnh
                    var img = targetWidget.querySelector('#jolyneImg');
                    if (img && cfg.spriteUrl) {
                        img.src = cfg.spriteUrl;
                        if (cfg.size) img.style.width = cfg.size + 'px';
                        if (cfg.speed) img.style.animationDuration = cfg.speed + 's';
                    }

                    // Cập nhật hiệu ứng Menacing GoGo
                    var gogo = targetWidget.querySelector('#gogoContainer');
                    if (gogo && cfg.gogoDisplay) {
                        gogo.style.display = cfg.gogoDisplay;
                    }

                    // LUÔN LUÔN BẬT BÓNG THOẠI KHI CÓ HÀNH ĐỘNG MỚI
                    var bubble = targetWidget.querySelector('#jolyneBubble');
                    if (bubble) {
                        var line = cfg.line;
                        if (!line || !line.trim()) {
                            var act = cfg.action || window.__jolyne_current_action || 'idle';
                            var allD = window.__jolyne_all_dialogues || {};
                            var pool = allD[act] || allD['idle'] || ['Xin chào! 🌸'];
                            line = pool[Math.floor(Math.random() * pool.length)];
                        }
                        bubble.innerHTML = line;
                        bubble.classList.remove('hide-bubble');
                        bubble.style.setProperty('display', 'block', 'important');
                        bubble.style.setProperty('opacity', '1', 'important');
                        bubble.style.setProperty('visibility', 'visible', 'important');
                        bubble.style.setProperty('transform', 'scale(1) translate3d(0, 0, 0)', 'important');

                        if (window.__jolyne_timer) clearTimeout(window.__jolyne_timer);
                        var hideSec = cfg.autoHideSec || window.__jolyne_auto_hide_sec || 4.5;
                        var hideMs = Math.max(3500, Math.round(hideSec * 1000));
                        window.__jolyne_timer = setTimeout(function() {
                            if (bubble) bubble.classList.add('hide-bubble');
                            if (cfg.action !== 'idle' && img && (cfg.idleUrl || window.__jolyne_idle_url)) {
                                img.style.opacity = '0.5';
                                setTimeout(function() {
                                    img.src = cfg.idleUrl || window.__jolyne_idle_url;
                                    img.style.opacity = '1';
                                }, 120);
                            }
                        }, hideMs);
                    }
                };

                // Fast sync hook gọi từ inline image onload khi st.markdown vừa mount
                window.__jolyne_fast_sync = function(imgEl) {
                    try {
                        var container = imgEl ? (imgEl.previousElementSibling || imgEl.parentElement.querySelector('#jolyneWidget')) : null;
                        if (!container || container.id !== 'jolyneWidget') return;
                        var cfg = {
                            action: container.getAttribute('data-action') || 'idle',
                            line: container.getAttribute('data-line') || '',
                            spriteUrl: container.getAttribute('data-sprite') || '',
                            idleUrl: container.getAttribute('data-idle') || '',
                            size: container.getAttribute('data-size') || '',
                            speed: container.getAttribute('data-speed') || '',
                            gogoDisplay: container.getAttribute('data-gogo') || 'block',
                            autoHideSec: parseFloat(container.getAttribute('data-autohide')) || 4.5
                        };
                        window.__jolyne_sync(cfg);
                    } catch(e) {
                        console.error('Fast sync error:', e);
                    }
                };

                // MutationObserver: bắt ngay tức khắc các thay đổi DOM của Streamlit trước khi paint
                try {
                    var obs = new MutationObserver(function() {
                        var inner = pDoc.querySelector('#root #jolyneWidget, div[data-testid="stApp"] #jolyneWidget');
                        if (inner) {
                            var cfg = {
                                action: inner.getAttribute('data-action') || 'idle',
                                line: inner.getAttribute('data-line') || '',
                                spriteUrl: inner.getAttribute('data-sprite') || '',
                                idleUrl: inner.getAttribute('data-idle') || '',
                                size: inner.getAttribute('data-size') || '',
                                speed: inner.getAttribute('data-speed') || '',
                                gogoDisplay: inner.getAttribute('data-gogo') || 'block',
                                autoHideSec: parseFloat(inner.getAttribute('data-autohide')) || 4.5
                            };
                            window.__jolyne_sync(cfg);
                        }
                    });
                    obs.observe(pDoc.body, { childList: true, subtree: true });
                } catch(err) {}

                // D. BỘ LẮNG NGHE KÉO THẢ TOÀN CỤC TRÊN DOCUMENT (MỌI TRANG / MỌI TAB)
                var isDragging = false;
                var currentWidget = null;
                var currentWrap = null;
                var startX = 0, startY = 0;
                var initX = 0, initY = 0;
                var minDX = 0, maxDX = 0, minDY = 0, maxDY = 0;
                var moved = false;

                pDoc.addEventListener('dragstart', function(e) {
                    if (e.target && e.target.closest && e.target.closest('#jolyneWrap')) {
                        e.preventDefault();
                    }
                }, true);

                pDoc.addEventListener('pointerdown', function(e) {
                    if (e.button !== undefined && e.button !== 0) return;
                    var wrap = e.target && e.target.closest ? e.target.closest('#jolyneWrap') : null;
                    if (!wrap) return;

                    var widget = pDoc.getElementById('jolyneWidget');
                    if (!widget) return;

                    currentWidget = widget;
                    currentWrap = wrap;
                    isDragging = true;
                    moved = false;
                    startX = e.clientX;
                    startY = e.clientY;

                    initX = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    initY = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-y')) || 0;

                    var wrapRect = wrap.getBoundingClientRect();
                    var pad = 8;
                    var winW = window.innerWidth || 1024;
                    var winH = window.innerHeight || 768;

                    minDX = initX - (wrapRect.left - pad);
                    maxDX = initX + ((winW - pad) - wrapRect.right);
                    minDY = initY - (wrapRect.top - pad);
                    maxDY = initY + ((winH - pad) - wrapRect.bottom);

                    widget.classList.add('is-dragging');
                    try { wrap.setPointerCapture(e.pointerId); } catch(err) {}
                    e.preventDefault();
                }, true);

                pDoc.addEventListener('pointermove', function(e) {
                    if (!isDragging || !currentWidget || !currentWrap) return;
                    var dx = e.clientX - startX;
                    var dy = e.clientY - startY;
                    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true;

                    var targetX = initX + dx;
                    var targetY = initY + dy;

                    var curX = Math.max(minDX, Math.min(maxDX, targetX));
                    var curY = Math.max(minDY, Math.min(maxDY, targetY));

                    pDoc.documentElement.style.setProperty('--jolyne-x', curX + 'px');
                    pDoc.documentElement.style.setProperty('--jolyne-y', curY + 'px');
                    currentWidget.style.transform = 'translate3d(' + curX + 'px, ' + curY + 'px, 0)';
                }, true);

                function onPointerEnd(e) {
                    if (!isDragging) return;
                    isDragging = false;
                    if (currentWidget) currentWidget.classList.remove('is-dragging');

                    var finalX = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    var finalY = parseFloat(pDoc.documentElement.style.getPropertyValue('--jolyne-y')) || 0;

                    try {
                        localStorage.setItem('jolyne_pos_v2', JSON.stringify({ x: finalX, y: finalY }));
                    } catch(err) {}

                    if (currentWrap) {
                        try { currentWrap.releasePointerCapture(e.pointerId); } catch(err) {}
                        if (moved) {
                            var stopClick = function(ev) {
                                ev.stopPropagation();
                                ev.preventDefault();
                                currentWrap.removeEventListener('click', stopClick, true);
                            };
                            currentWrap.addEventListener('click', stopClick, true);
                        }
                    }
                    currentWidget = null;
                    currentWrap = null;
                }

                pDoc.addEventListener('pointerup', onPointerEnd, true);
                pDoc.addEventListener('pointercancel', onPointerEnd, true);

                // E. CLICK VÀO BÓNG THOẠI HOẶC AVATAR
                pDoc.addEventListener('click', function(e) {
                    // Click vào bóng thoại: ẩn bóng thoại và trở về pose idle
                    var bubbleClick = e.target && e.target.closest ? e.target.closest('#jolyneBubble') : null;
                    if (bubbleClick) {
                        bubbleClick.classList.add('hide-bubble');
                        var img = pDoc.getElementById('jolyneImg');
                        if (img && window.__jolyne_idle_url) {
                            img.style.opacity = '0.5';
                            setTimeout(function() {
                                img.src = window.__jolyne_idle_url;
                                img.style.opacity = '1';
                            }, 100);
                        }
                        return;
                    }

                    // Click vào avatar: nói câu thoại theo ngữ cảnh hoặc e thẹn
                    var wrapClick = e.target && e.target.closest ? e.target.closest('#jolyneWrap') : null;
                    if (!wrapClick || moved) return;

                    var act = window.__jolyne_current_action || 'idle';
                    var allD = window.__jolyne_all_dialogues || {};
                    var pool = allD[act];
                    if (!pool || pool.length === 0) pool = allD['idle'] || ['Xin chào! 🌸'];

                    if (Math.random() < 0.30 && allD['shy'] && allD['shy'].length > 0) {
                        pool = allD['shy'];
                        act = 'shy';
                    }

                    var randLine = pool[Math.floor(Math.random() * pool.length)];
                    window.__jolyne_sync({
                        action: act,
                        line: randLine,
                        spriteUrl: (window.__jolyne_sprite_map && window.__jolyne_sprite_map[act]) || '',
                        idleUrl: window.__jolyne_idle_url || '',
                        autoHideSec: window.__jolyne_auto_hide_sec || 4.5,
                        dialogues: allD,
                        spriteMap: window.__jolyne_sprite_map || {}
                    });
                }, true);

                // F. CẬP NHẬT KHI ĐỔI TAB (TƯƠNG THÍCH TẤT CẢ GỌI CŨ)
                window.__jolyne_update_tab = function(cfg) {
                    window.__jolyne_sync(cfg);
                };
            })();
            `;
            pDoc.head.appendChild(sc);
        }

        // 2. Kích hoạt cập nhật tab ngay lập tức
        function syncTab() {
            var fn = pWin.__jolyne_sync || pWin.__jolyne_update_tab;
            if (fn) {
                fn({
                    action: '__ACTION__',
                    line: __LINE__,
                    spriteUrl: '__SPRITE_URL__',
                    idleUrl: '__IDLE_URL__',
                    herName: __HER_NAME__,
                    myName: __MY_NAME__,
                    dialogues: __ALL_DIALOGUES__,
                    spriteMap: __SPRITE_MAP__,
                    autoHideSec: __AUTO_HIDE_SEC__,
                    size: '__SIZE__',
                    speed: '__SPEED__',
                    gogoDisplay: '__GOGO_DISPLAY__'
                });
            }
        }
        syncTab();
        setTimeout(syncTab, 40);
        setTimeout(syncTab, 160);

    } catch(err) {
        console.error('Jolyne loader error:', err);
    }
})();
</script>
<!-- ts: __TS__ -->
</body>
</html>"""

    js_controller = (
        js_template
        .replace("__ACTION__", action)
        .replace("__LINE__", json.dumps(selected_line, ensure_ascii=False))
        .replace("__SPRITE_URL__", current_sprite_url)
        .replace("__IDLE_URL__", idle_sprite_url)
        .replace("__HER_NAME__", json.dumps(her_name, ensure_ascii=False))
        .replace("__MY_NAME__", json.dumps(my_name, ensure_ascii=False))
        .replace("__AUTO_HIDE_SEC__", str(auto_hide_sec))
        .replace("__SIZE__", str(size))
        .replace("__SPEED__", str(speed))
        .replace("__GOGO_DISPLAY__", gogo_display)
        .replace("__ALL_DIALOGUES__", json.dumps(all_formatted_dialogues, ensure_ascii=False))
        .replace("__SPRITE_MAP__", json.dumps(sprite_map, ensure_ascii=False))
        .replace("__TS__", str(ts))
    )
    st_module.components.v1.html(js_controller, height=0)


def render_mascot_tab_ui(st_module, her_name: str, my_name: str) -> None:
    """Vẽ giao diện tùy chỉnh mascot trong tab Navbar Streamlit."""
    settings = get_mascot_settings(st_module)

    st_module.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #fff0f5 0%, #fff5f8 50%, #f0fdf4 100%);
                    border: 1.5px solid #ffd6e0; border-radius: 20px; padding: 20px; margin-bottom: 20px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <span style="font-size:2rem;">🦋</span>
                <div>
                    <h3 style="margin:0;color:#be185d;font-weight:800;">Tùy Chỉnh Trợ Lý Bé Jolyne Kujo</h3>
                    <div style="font-size:0.85rem;color:#64748b;">
                        Người bạn bảo vệ dễ thương luôn đồng hành cùng <b>{her_name}</b> 24/7
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st_module.columns(2)

    with col1:
        st_module.markdown("#### ⚙️ Cài Đặt Hiển Thị")
        mascot_enabled = st_module.toggle(
            "Bật bé Jolyne đồng hành 🦋",
            value=settings.get("enabled", True),
            key="mascot_enabled_toggle",
            help="Hiển thị nhân vật lơ lửng ở góc màn hình",
        )
        gogo_enabled = st_module.toggle(
            "Hiệu ứng Stand Menacing (ゴゴゴゴ) ⚡",
            value=settings.get("gogo_enabled", True),
            key="mascot_gogo_toggle",
            help="Hiệu ứng chữ JoJo bay bổng bên phải nhân vật",
        )

    with col2:
        st_module.markdown("#### 📏 Kích Thước & Tốc Độ (Thay đổi trực tiếp)")
        mascot_size = st_module.slider(
            "Kích thước nhân vật (pixel)",
            min_value=65,
            max_value=160,
            value=int(settings.get("size", 95)),
            step=5,
            key="mascot_size_slider",
            help="Kéo để thay đổi độ lớn của bé Jolyne trực tiếp trên màn hình",
        )
        mascot_speed = st_module.slider(
            "Tốc độ lơ lửng (giây)",
            min_value=1.5,
            max_value=5.0,
            value=float(settings.get("speed", 3.2)),
            step=0.1,
            key="mascot_speed_slider",
            help="Thời gian một chu kỳ nhấp nhô lơ lửng (thay đổi trực tiếp)",
        )

    # Tự động lưu cấu hình thanh trượt & toggle khi người dùng điều chỉnh
    raw_saved = get_mascot_settings()
    if (
        mascot_enabled != raw_saved.get("enabled", True)
        or gogo_enabled != raw_saved.get("gogo_enabled", True)
        or mascot_size != raw_saved.get("size", 95)
        or abs(mascot_speed - raw_saved.get("speed", 3.2)) > 0.05
    ):
        raw_saved["enabled"] = mascot_enabled
        raw_saved["gogo_enabled"] = gogo_enabled
        raw_saved["size"] = mascot_size
        raw_saved["speed"] = mascot_speed
        save_mascot_settings(raw_saved)

    st_module.markdown("---")
    st_module.markdown("#### 💬 Chỉnh Sửa Lời Thoại Bé Jolyne")
    st_module.caption(
        "Mỗi dòng là một câu thoại khác nhau. Bé Jolyne sẽ chọn ngẫu nhiên 1 câu khi kích hoạt. "
        "Bạn có thể dùng <code>{her_name}</code> hoặc <code>{my_name}</code> để chèn tên động."
    )

    dialogues = copy.deepcopy(raw_saved.get("dialogues", DEFAULT_SETTINGS["dialogues"]))

    # Chia nhóm danh mục rõ ràng
    category_groups = {
        "🌸 Hàng Ngày": [
            ("idle", "✨", "Đứng Chờ (Mặc định)"),
            ("morning", "☀️", "Chào Buổi Sáng"),
            ("sleep", "🌙", "Chúc Ngủ Ngon"),
            ("shy", "👉👈", "Bị Chọc E Thẹn"),
        ],
        "📚 Học Tập & Deadline": [
            ("study", "📚", "Đi Học / Bài Vở"),
            ("fight", "👊", "Diệt Deadline (Quyết tâm)"),
            ("victory", "🎉", "Xong Deadline (Ăn mừng)"),
            ("panic", "🙀", "Trễ Hạn Nani?!"),
        ],
        "💖 Sức Khỏe & Chăm Sóc": [
            ("med", "💊", "Nhắc Uống Thuốc"),
            ("water", "🍵", "Nhắc Uống Nước"),
            ("period", "🌸", "Đèn Đỏ / Giữ Ấm"),
            ("hug", "🧸", "An Ủi / Ôm Gấu"),
        ]
    }

    tab_titles = list(category_groups.keys())
    tabs = st_module.tabs(tab_titles)

    for tab_idx, cat_name in enumerate(tab_titles):
        with tabs[tab_idx]:
            act_list = category_groups[cat_name]
            for act_key, act_icon, act_name in act_list:
                col_h1, col_h2 = st_module.columns([3, 1])
                with col_h1:
                    st_module.markdown(f"##### {act_icon} {act_name}")
                with col_h2:
                    if st_module.button("▶️ Thử nghe", key=f"btn_preview_{act_key}", use_container_width=True):
                        # Cập nhật lời thoại hiện tại đang gõ trước khi thử
                        k_state = f"mascot_txt_{act_key}"
                        if k_state in st_module.session_state:
                            lines = [l.strip() for l in st_module.session_state[k_state].splitlines() if l.strip()]
                            if lines:
                                dialogues[act_key] = lines
                                raw_saved["dialogues"] = dialogues
                                save_mascot_settings(raw_saved)
                        st_module.session_state["mascot_action"] = act_key
                        st_module.rerun()

                existing_lines = dialogues.get(act_key, DEFAULT_SETTINGS["dialogues"].get(act_key, []))
                default_text = "\n".join(existing_lines)

                st_module.text_area(
                    label=f"Lời thoại {act_name}",
                    value=default_text,
                    height=85,
                    key=f"mascot_txt_{act_key}",
                    label_visibility="collapsed",
                    help="Mỗi dòng là một câu thoại riêng biệt",
                )
                st_module.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st_module.markdown("<br>", unsafe_allow_html=True)
    save_col1, save_col2, save_col3 = st_module.columns([2, 1.5, 1.8])

    if save_col1.button("💾 Lưu Toàn Bộ Lời Thoại", type="primary", use_container_width=True, key="btn_save_all_dialogues"):
        for k in ACTION_LABELS.keys():
            key_name = f"mascot_txt_{k}"
            if key_name in st_module.session_state:
                lines = [l.strip() for l in st_module.session_state[key_name].splitlines() if l.strip()]
                if lines:
                    dialogues[k] = lines
        raw_saved["dialogues"] = dialogues
        save_mascot_settings(raw_saved)
        st_module.session_state["mascot_action"] = "idle"
        st_module.toast("✅ Đã lưu toàn bộ lời thoại bé Jolyne thành công!", icon="💾")
        st_module.rerun()

    if save_col2.button("🔄 Khôi Phục Mặc Định", use_container_width=True, key="btn_reset_defaults"):
        save_mascot_settings(DEFAULT_SETTINGS)
        for k in ["mascot_size_slider", "mascot_speed_slider", "mascot_enabled_toggle", "mascot_gogo_toggle"]:
            st_module.session_state.pop(k, None)
        for act in ACTION_LABELS.keys():
            st_module.session_state.pop(f"mascot_txt_{act}", None)
        st_module.toast("Đã khôi phục toàn bộ cài đặt gốc của bé Jolyne! 🌸", icon="🔄")
        st_module.rerun()

    if save_col3.button("📍 Đặt Lại Vị Trí Về Góc", use_container_width=True, key="btn_reset_position"):
        st_module.components.v1.html("""
        <script>
        try {
            var pWin = window.parent;
            var pDoc = window.parent.document;
            pWin.localStorage.removeItem('jolyne_pos_v2');
            pDoc.documentElement.style.setProperty('--jolyne-x', '0px');
            pDoc.documentElement.style.setProperty('--jolyne-y', '0px');
            var w = pDoc.getElementById('jolyneWidget');
            if (w) w.style.transform = 'translate3d(0, 0, 0)';
        } catch(e) {}
        </script>
        """, height=0)
        st_module.toast("Đã đặt lại vị trí bé Jolyne về góc phải dưới! 🦋", icon="📍")
