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
from typing import Dict, List, Any

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
    1. HTML/CSS tinh gọn 100% trong st.markdown (không có script inline).
    2. Giữ nguyên tọa độ (x, y) xuyên suốt tất cả các trang bằng localStorage.
    3. Bộ lắng nghe kéo thả bằng Event Delegation trên window.parent.document,
       đảm bảo ở BẤT KỲ TRANG NÀO cũng kéo thả được mượt mà 100%.
    """
    settings = get_mascot_settings(st_module)
    if not settings.get("enabled", True):
        return

    size = int(settings.get("size", 95))
    speed = float(settings.get("speed", 3.2))
    gogo_enabled = bool(settings.get("gogo_enabled", True))
    auto_hide_sec = float(settings.get("auto_hide_seconds", 4.5))

    raw_dialogues = settings.get("dialogues", DEFAULT_SETTINGS["dialogues"])
    act_lines = raw_dialogues.get(action, raw_dialogues.get("idle", ["Xin chào! 🌸"]))
    selected_line = random.choice(act_lines).replace("{her_name}", her_name).replace("{my_name}", my_name)

    shy_raw_lines = raw_dialogues.get("shy", DEFAULT_SETTINGS["dialogues"]["shy"])
    formatted_shy_lines = [l.replace("{her_name}", her_name).replace("{my_name}", my_name) for l in shy_raw_lines]

    current_sprite_url = f"/app/static/mascot/jolyne_{action}.webp"
    idle_sprite_url = "/app/static/mascot/jolyne_idle.webp"
    gogo_display = "block" if gogo_enabled else "none"

    # PHẦN 1: CSS & HTML nguyên bản không chứa khoảng trắng thụt lề đầu dòng
    raw_css_html = f"""<style>
.jolyne-floating-container {{
position: fixed !important;
bottom: 24px !important;
right: 24px !important;
z-index: 9999999 !important;
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
box-shadow: 0 10px 30px rgba(216, 17, 89, 0.16) !important;
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
transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
position: relative !important;
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
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
}}

.jolyne-avatar-img {{
width: {size}px !important;
height: auto !important;
display: block !important;
filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.14)) !important;
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
z-index: 100001 !important;
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
z-index: 100002 !important;
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

<div class="jolyne-floating-container" id="jolyneWidget">
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

                // A. Đọc và áp dụng tọa độ đã lưu vào CSS variables (--jolyne-x, --jolyne-y)
                function initSavedPos() {
                    try {
                        var s = JSON.parse(localStorage.getItem('jolyne_pos_v2'));
                        if (s && typeof s.x === 'number' && typeof s.y === 'number') {
                            document.documentElement.style.setProperty('--jolyne-x', s.x + 'px');
                            document.documentElement.style.setProperty('--jolyne-y', s.y + 'px');
                            var w = document.getElementById('jolyneWidget');
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
                    var curX = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    var curY = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-y')) || 0;
                    var c = clampPos(curX, curY);
                    if (c.x !== curX || c.y !== curY) {
                        document.documentElement.style.setProperty('--jolyne-x', c.x + 'px');
                        document.documentElement.style.setProperty('--jolyne-y', c.y + 'px');
                        try { localStorage.setItem('jolyne_pos_v2', JSON.stringify(c)); } catch(e) {}
                    }
                });

                // C. BỘ LẮNG NGHE KÉO THẢ TOÀN CỤC TRÊN DOCUMENT (MỌI TRANG / MỌI TAB ĐỀU HOẠT ĐỘNG 100%)
                var isDragging = false;
                var currentWidget = null;
                var currentWrap = null;
                var startX = 0, startY = 0;
                var initX = 0, initY = 0;
                var minDX = 0, maxDX = 0, minDY = 0, maxDY = 0;
                var moved = false;

                document.addEventListener('dragstart', function(e) {
                    if (e.target && e.target.closest && e.target.closest('#jolyneWrap')) {
                        e.preventDefault();
                    }
                }, true);

                document.addEventListener('pointerdown', function(e) {
                    if (e.button !== undefined && e.button !== 0) return;
                    var wrap = e.target && e.target.closest ? e.target.closest('#jolyneWrap') : null;
                    if (!wrap) return;

                    var widget = document.getElementById('jolyneWidget');
                    if (!widget) return;

                    currentWidget = widget;
                    currentWrap = wrap;
                    isDragging = true;
                    moved = false;
                    startX = e.clientX;
                    startY = e.clientY;

                    // Đọc tọa độ hiện tại từ CSS variables
                    initX = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    initY = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-y')) || 0;

                    // Đo kích thước thực tế để khóa biên an toàn
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

                document.addEventListener('pointermove', function(e) {
                    if (!isDragging || !currentWidget || !currentWrap) return;
                    var dx = e.clientX - startX;
                    var dy = e.clientY - startY;
                    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true;

                    var targetX = initX + dx;
                    var targetY = initY + dy;

                    var curX = Math.max(minDX, Math.min(maxDX, targetX));
                    var curY = Math.max(minDY, Math.min(maxDY, targetY));

                    document.documentElement.style.setProperty('--jolyne-x', curX + 'px');
                    document.documentElement.style.setProperty('--jolyne-y', curY + 'px');
                    currentWidget.style.transform = 'translate3d(' + curX + 'px, ' + curY + 'px, 0)';
                }, true);

                function onPointerEnd(e) {
                    if (!isDragging) return;
                    isDragging = false;
                    if (currentWidget) currentWidget.classList.remove('is-dragging');

                    var finalX = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-x')) || 0;
                    var finalY = parseFloat(document.documentElement.style.getPropertyValue('--jolyne-y')) || 0;

                    // Lưu vị trí vào localStorage để giữ nguyên xuyên suốt mọi trang và reload
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

                document.addEventListener('pointerup', onPointerEnd, true);
                document.addEventListener('pointercancel', onPointerEnd, true);

                // D. CLICK VÀO BÓNG THOẠI HOẶC AVATAR
                var shyDialogueList = __SHY_LINES__;

                document.addEventListener('click', function(e) {
                    // Click vào bóng thoại: ẩn bóng thoại và trở về pose idle
                    var bubbleClick = e.target && e.target.closest ? e.target.closest('#jolyneBubble') : null;
                    if (bubbleClick) {
                        bubbleClick.classList.add('hide-bubble');
                        var img = document.getElementById('jolyneImg');
                        if (img && window.__jolyne_idle_url) {
                            img.style.opacity = '0.5';
                            setTimeout(function() {
                                img.src = window.__jolyne_idle_url;
                                img.style.opacity = '1';
                            }, 100);
                        }
                        return;
                    }

                    // Click vào avatar: e thẹn với câu thoại tùy chỉnh
                    var wrapClick = e.target && e.target.closest ? e.target.closest('#jolyneWrap') : null;
                    if (!wrapClick || moved) return;

                    var img = document.getElementById('jolyneImg');
                    var b = document.getElementById('jolyneBubble');
                    if (img) {
                        img.style.opacity = '0.5';
                        setTimeout(function() {
                            img.src = '/app/static/mascot/jolyne_shy.webp';
                            img.style.opacity = '1';
                        }, 100);
                    }
                    if (b) {
                        var randShy = shyDialogueList[Math.floor(Math.random() * shyDialogueList.length)];
                        b.textContent = randShy;
                        b.classList.remove('hide-bubble');
                    }
                    if (window.__jolyne_timer) clearTimeout(window.__jolyne_timer);
                    window.__jolyne_timer = setTimeout(function() {
                        if (b) b.classList.add('hide-bubble');
                        if (img && window.__jolyne_idle_url) {
                            img.style.opacity = '0.5';
                            setTimeout(function() {
                                img.src = window.__jolyne_idle_url;
                                img.style.opacity = '1';
                            }, 100);
                        }
                    }, 4500);
                }, true);

                // E. ĐỒNG BỘ TRẠNG THÁI KHI STREAMLIT CHUYỂN TAB
                window.__jolyne_update_tab = function(cfg) {
                    window.__jolyne_idle_url = cfg.idleUrl;
                    window.__jolyne_her_name = cfg.herName;

                    // Giữ chắc chắn vị trí từ localStorage đồng bộ vào CSS variable
                    try {
                        var s = JSON.parse(localStorage.getItem('jolyne_pos_v2'));
                        if (s && typeof s.x === 'number' && typeof s.y === 'number') {
                            document.documentElement.style.setProperty('--jolyne-x', s.x + 'px');
                            document.documentElement.style.setProperty('--jolyne-y', s.y + 'px');
                            var w = document.getElementById('jolyneWidget');
                            if (w) w.style.transform = 'translate3d(' + s.x + 'px, ' + s.y + 'px, 0)';
                        }
                    } catch(e) {}

                    // Tự động thu bóng thoại và trở về pose mặc định sau autoHideSec
                    if (window.__jolyne_timer) clearTimeout(window.__jolyne_timer);
                    if (cfg.autoHideSec > 0) {
                        window.__jolyne_timer = setTimeout(function() {
                            var b = document.getElementById('jolyneBubble');
                            var i = document.getElementById('jolyneImg');
                            if (b) b.classList.add('hide-bubble');
                            if (cfg.action !== 'idle' && i && cfg.idleUrl) {
                                i.style.opacity = '0.5';
                                setTimeout(function() {
                                    i.src = cfg.idleUrl;
                                    i.style.opacity = '1';
                                }, 120);
                            }
                        }, Math.round(cfg.autoHideSec * 1000));
                    }
                };
            })();
            `;
            pDoc.head.appendChild(sc);
        }

        // 2. Kích hoạt cập nhật tab
        function syncTab() {
            if (pWin.__jolyne_update_tab) {
                pWin.__jolyne_update_tab({
                    action: '__ACTION__',
                    idleUrl: '__IDLE_URL__',
                    herName: __HER_NAME__,
                    autoHideSec: __AUTO_HIDE_SEC__
                });
            }
        }
        syncTab();
        setTimeout(syncTab, 60);
        setTimeout(syncTab, 200);

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
        .replace("__IDLE_URL__", idle_sprite_url)
        .replace("__HER_NAME__", json.dumps(her_name))
        .replace("__AUTO_HIDE_SEC__", str(auto_hide_sec))
        .replace("__SHY_LINES__", json.dumps(formatted_shy_lines, ensure_ascii=False))
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
    st_module.markdown("#### 🎭 Thử Nghiệm Hành Động Trực Tiếp")
    st_module.caption("Bấm nút bên dưới để đổi pose và nghe câu thoại thử nghiệm:")

    act_keys = list(ACTION_LABELS.keys())
    row1 = act_keys[:6]
    row2 = act_keys[6:]

    cols_r1 = st_module.columns(6)
    for i, k in enumerate(row1):
        icon, name = ACTION_LABELS[k]
        if cols_r1[i].button(f"{icon} {name}", key=f"btn_test_{k}", use_container_width=True):
            st_module.session_state["mascot_action"] = k
            st_module.rerun()

    cols_r2 = st_module.columns(6)
    for i, k in enumerate(row2):
        icon, name = ACTION_LABELS[k]
        if cols_r2[i].button(f"{icon} {name}", key=f"btn_test_{k}", use_container_width=True):
            st_module.session_state["mascot_action"] = k
            st_module.rerun()

    st_module.markdown("---")
    st_module.markdown("#### 💬 Chỉnh Sửa Lời Thoại Của Bé Jolyne")
    st_module.caption(
        "Mỗi dòng là một câu thoại khác nhau. Bé Jolyne sẽ chọn ngẫu nhiên 1 câu khi hành động kích hoạt. "
        "Bạn có thể dùng <code>{her_name}</code> hoặc <code>{my_name}</code> để chèn tên động."
    )

    dialogues = raw_saved.get("dialogues", DEFAULT_SETTINGS["dialogues"])

    sel_col1, sel_col2 = st_module.columns([3, 1.5])
    with sel_col1:
        selected_act = st_module.selectbox(
            "Chọn hành động muốn chỉnh sửa lời thoại:",
            options=act_keys,
            format_func=lambda k: f"{ACTION_LABELS[k][0]} {ACTION_LABELS[k][1]}",
            key="mascot_act_select",
        )
    with sel_col2:
        st_module.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st_module.button("▶️ Nghe Thử Pose Này", use_container_width=True, key="btn_preview_curr"):
            st_module.session_state["mascot_action"] = selected_act
            st_module.rerun()

    current_lines = dialogues.get(selected_act, DEFAULT_SETTINGS["dialogues"].get(selected_act, ["Xin chào! 🌸"]))
    current_text = "\n".join(current_lines)

    edited_text = st_module.text_area(
        f"Danh sách câu thoại cho [{ACTION_LABELS[selected_act][1]}]:",
        value=current_text,
        height=140,
        help="Mỗi dòng là một câu thoại riêng biệt",
        key=f"mascot_dialogue_input_{selected_act}",
    )

    st_module.markdown("<br>", unsafe_allow_html=True)
    save_col1, save_col2, save_col3 = st_module.columns([2, 1.5, 1.8])

    if save_col1.button(f"💾 Lưu Lời Thoại Cho [{ACTION_LABELS[selected_act][1]}]", type="primary", use_container_width=True):
        new_lines = [l.strip() for l in edited_text.splitlines() if l.strip()]
        if not new_lines:
            new_lines = DEFAULT_SETTINGS["dialogues"].get(selected_act, ["Xin chào! 🌸"])

        dialogues[selected_act] = new_lines
        raw_saved["dialogues"] = dialogues
        save_mascot_settings(raw_saved)
        # Thử nghiệm ngay hành động này để người dùng thấy câu thoại mới ngay lập tức
        st_module.session_state["mascot_action"] = selected_act
        st_module.toast(f"Đã lưu lời thoại cho {ACTION_LABELS[selected_act][1]}!", icon="✅")
        st_module.rerun()

    if save_col2.button("🔄 Khôi Phục Mặc Định", use_container_width=True):
        save_mascot_settings(DEFAULT_SETTINGS)
        # Xóa các key trong session_state để tải lại giá trị gốc
        for k in ["mascot_size_slider", "mascot_speed_slider", "mascot_enabled_toggle", "mascot_gogo_toggle"]:
            st_module.session_state.pop(k, None)
        for act in act_keys:
            st_module.session_state.pop(f"mascot_dialogue_input_{act}", None)
        st_module.toast("Đã khôi phục toàn bộ cài đặt gốc của bé Jolyne! 🌸", icon="🔄")
        st_module.rerun()

    if save_col3.button("📍 Đặt Lại Vị Trí Về Góc", use_container_width=True):
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
