"""
mascot_manager.py
=================
Quản lý nhân vật đồng hành Chibi Jolyne Kujo (JoJo Part 6: Stone Ocean)
- 12 hành động chuẩn định dạng WebP tĩnh siêu nhẹ (~50KB/ảnh, phục vụ qua /app/static/mascot/)
- Tích hợp chuẩn qua st.components.v1.html gắn trực tiếp vào window.parent.document.body
  => 100% không bị lỗi tràn chữ Base64 ra màn hình
  => Không bị gián đoạn hay reset vị trí khi Streamlit chuyển tab
- Kéo thả an toàn bằng Pointer Events (chỉ di chuyển khi giữ chuột, buông là dừng)
- Khóa chặt biên màn hình (không trôi khỏi khung hình)
- Tự động quay về pose mặc định sau 4.5s khi đóng thoại
- Tab điều hướng "Bé Jolyne 🦋" trên Navbar Streamlit để tùy chỉnh
"""

import os
import json
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


def get_mascot_settings() -> Dict[str, Any]:
    """Đọc cấu hình mascot từ file JSON."""
    if not os.path.exists(SETTINGS_PATH):
        save_mascot_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
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
        return data
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_mascot_settings(settings: Dict[str, Any]) -> None:
    """Lưu cấu hình mascot vào data/mascot_settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def render_floating_mascot(st_module, her_name: str, my_name: str) -> None:
    """
    Nhúng bé Jolyne vào trang Streamlit bằng components.v1.html.
    Tự động gắn trực tiếp vào window.parent.document.body:
    - Sử dụng URL ảnh tĩnh WebP (/app/static/mascot/...) cực nhẹ (~5KB payload)
    - KHÔNG đưa chuỗi Base64 vào markdown, triệt tiêu 100% lỗi in chữ thô
    - Widget sống độc lập, không bị giật lag khi Streamlit reload các widget khác
    """
    settings = get_mascot_settings()
    enabled = settings.get("enabled", True)

    if not enabled:
        # Nếu người dùng tắt, dọn dẹp widget khỏi DOM nếu đang tồn tại
        cleanup_html = """
        <script>
        try {
            const pDoc = window.parent.document;
            const w = pDoc.getElementById('jolyneWidget');
            if (w) w.remove();
            const s = pDoc.getElementById('jolyneStyles');
            if (s) s.remove();
            window.parent.__jolyne_initialized = false;
        } catch(e) {}
        </script>
        """
        st_module.components.v1.html(cleanup_html, height=0)
        return

    size = int(settings.get("size", 95))
    speed = float(settings.get("speed", 3.2))
    gogo_enabled = bool(settings.get("gogo_enabled", True))
    auto_hide_sec = float(settings.get("auto_hide_seconds", 4.5))

    # Định dạng các câu thoại với tên riêng
    raw_dialogues = settings.get("dialogues", DEFAULT_SETTINGS["dialogues"])
    formatted_dialogues: Dict[str, List[str]] = {}
    for act, lines in raw_dialogues.items():
        fmt_lines = []
        for line in lines:
            fmt_lines.append(line.replace("{her_name}", her_name).replace("{my_name}", my_name))
        formatted_dialogues[act] = fmt_lines

    # Đường dẫn URL tĩnh WebP qua Streamlit static file handler
    sprites_urls = {
        k: f"app/static/mascot/jolyne_{k}.webp"
        for k in ACTION_LABELS.keys()
    }

    sprites_json = json.dumps(sprites_urls, ensure_ascii=False)
    dialogues_json = json.dumps(formatted_dialogues, ensure_ascii=False)
    gogo_display = "block" if gogo_enabled else "none"

    injection_script = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;">
    <script>
    (function() {{
        try {{
            const pDoc = window.parent.document;
            const pWin = window.parent;
            if (!pDoc || !pDoc.body) return;

            const SPRITES = {sprites_json};
            const DIALOGUES = {dialogues_json};
            const AUTO_HIDE_MS = {int(auto_hide_sec * 1000)};
            const SIZE_PX = {size};
            const SPEED_SEC = {speed};
            const GOGO_DISPLAY = "{gogo_display}";

            // 1. Cập nhật CSS vào head của parent window
            let styleEl = pDoc.getElementById('jolyneStyles');
            const cssContent = `
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
                    transform: translate3d(0, 0, 0);
                }}

                .jolyne-floating-container.is-dragging {{
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
                    opacity: 0 !important;
                    visibility: hidden !important;
                    pointer-events: auto !important;
                    cursor: pointer !important;
                    transform-origin: bottom right !important;
                    transform: scale(0.6) translate3d(0, 10px, 0) !important;
                    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
                    position: relative !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                }}

                .jolyne-speech-bubble.show {{
                    opacity: 1 !important;
                    visibility: visible !important;
                    transform: scale(1) translate3d(0, 0, 0) !important;
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
                    width: ${{SIZE_PX}}px !important;
                    height: auto !important;
                    display: block !important;
                    filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.14)) !important;
                    animation: jolyneFloat ${{SPEED_SEC}}s ease-in-out infinite alternate !important;
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
                    50%  {{ transform: translate3d(0, -7px, 0) rotate(-1.5deg); }}
                    100% {{ transform: translate3d(0, -3px, 0) rotate(1.5deg); }}
                }}

                @keyframes jolyneHappyBounce {{
                    0%   {{ transform: scale(1) translate3d(0, 0, 0); }}
                    30%  {{ transform: scale(1.18, 0.85) translate3d(0, 4px, 0); }}
                    60%  {{ transform: scale(0.9, 1.15) translate3d(0, -22px, 0) rotate(3deg); }}
                    80%  {{ transform: scale(1.05, 0.95) translate3d(0, -4px, 0); }}
                    100% {{ transform: scale(1) translate3d(0, 0, 0); }}
                }}

                @keyframes jolynePoseShake {{
                    0%, 100% {{ transform: translate3d(0, 0, 0) rotate(0); }}
                    20%      {{ transform: translate3d(-5px, 0, 0) rotate(-4deg); }}
                    40%      {{ transform: translate3d(5px, 0, 0) rotate(4deg); }}
                    60%      {{ transform: translate3d(-3px, 0, 0) rotate(-2deg); }}
                    80%      {{ transform: translate3d(3px, 0, 0) rotate(2deg); }}
                }}

                .animate-bounce {{
                    animation: jolyneHappyBounce 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
                }}
                .animate-shake {{
                    animation: jolynePoseShake 0.45s ease-in-out !important;
                }}

                .sparkle-particle {{
                    position: absolute !important;
                    font-size: 1.15rem !important;
                    pointer-events: none !important;
                    opacity: 0 !important;
                    animation: particleFly 1s ease-out forwards !important;
                    z-index: 100000 !important;
                }}

                @keyframes particleFly {{
                    0% {{ opacity: 1; transform: translate3d(0, 0, 0) scale(0.5); }}
                    100% {{ opacity: 0; transform: translate3d(var(--tx), var(--ty), 0) scale(1.4) rotate(var(--rot)); }}
                }}

                /* Stand Menacing Effect BÊN PHẢI NHÂN VẬT */
                .gogo-container {{
                    position: absolute !important;
                    left: 100% !important;
                    bottom: 0 !important;
                    width: 70px !important;
                    height: 120% !important;
                    pointer-events: none !important;
                    z-index: 100002 !important;
                    overflow: visible !important;
                    display: ${{GOGO_DISPLAY}} !important;
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
                    opacity: 0 !important;
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
            `;

            if (!styleEl) {{
                styleEl = pDoc.createElement('style');
                styleEl.id = 'jolyneStyles';
                styleEl.textContent = cssContent;
                pDoc.head.appendChild(styleEl);
            }} else {{
                styleEl.textContent = cssContent;
            }}

            // 2. Cập nhật DOM của Mascot Widget
            let widget = pDoc.getElementById('jolyneWidget');
            if (!widget) {{
                widget = pDoc.createElement('div');
                widget.id = 'jolyneWidget';
                widget.className = 'jolyne-floating-container';
                widget.innerHTML = `
                    <div class="jolyne-speech-bubble" id="jolyneBubble" title="Bấm để ẩn thoại">
                        Chào {her_name}! Tớ là Jolyne Kujo nè! 🦋✨
                    </div>
                    <div class="jolyne-avatar-wrap" id="jolyneWrap">
                        <div class="drag-hint">✥ kéo để di chuyển</div>
                        <div class="gogo-container" id="gogoContainer"></div>
                        <img src="${{SPRITES['idle']}}" id="jolyneImg" class="jolyne-avatar-img" alt="Jolyne Chibi" draggable="false" />
                    </div>
                `;
                pDoc.body.appendChild(widget);

                // Khởi tạo các ký tự Menacing
                const gogoBox = widget.querySelector('#gogoContainer');
                if (gogoBox) {{
                    const glyphData = [
                        {{ text: 'ゴ', fs: '2.1rem',  b: '78%', l: '4px',  anim: 'gogoFloat0', delay: 0.00, dur: 2.3 }},
                        {{ text: 'ゴ', fs: '1.6rem',  b: '60%', l: '14px', anim: 'gogoFloat1', delay: 0.40, dur: 2.7 }},
                        {{ text: 'ゴ', fs: '1.3rem',  b: '43%', l: '8px',  anim: 'gogoFloat2', delay: 0.75, dur: 2.1 }},
                        {{ text: 'ゴ', fs: '1.05rem', b: '27%', l: '18px', anim: 'gogoFloat3', delay: 1.05, dur: 2.9 }},
                        {{ text: 'ゴ', fs: '0.82rem', b: '12%', l: '10px', anim: 'gogoFloat4', delay: 1.35, dur: 2.5 }},
                    ];
                    glyphData.forEach(g => {{
                        const el = pDoc.createElement('div');
                        el.className = 'gogo-glyph';
                        el.textContent = g.text;
                        el.style.fontSize = g.fs;
                        el.style.bottom = g.b;
                        el.style.left = g.l;
                        el.style.animationName = g.anim;
                        el.style.animationDuration = g.dur + 's';
                        el.style.animationDelay = g.delay + 's';
                        el.style.animationTimingFunction = 'ease-in-out';
                        el.style.animationIterationCount = 'infinite';
                        el.style.animationFillMode = 'both';
                        gogoBox.appendChild(el);
                    }});
                }}

                // Kéo thả bằng Pointer Events (chuẩn hiện đại, không dính chuột)
                (function setupDrag() {{
                    const wrap = widget.querySelector('#jolyneWrap');
                    if (!wrap) return;

                    let isDragging = false;
                    let dragX = 0, dragY = 0;
                    let startX = 0, startY = 0;
                    let initX = 0, initY = 0;
                    let moved = false;

                    wrap.addEventListener('dragstart', e => e.preventDefault());

                    function onDown(e) {{
                        if (e.button !== undefined && e.button !== 0) return;
                        isDragging = true;
                        moved = false;
                        startX = e.clientX;
                        startY = e.clientY;
                        initX = dragX;
                        initY = dragY;
                        widget.classList.add('is-dragging');
                        try {{ wrap.setPointerCapture(e.pointerId); }} catch(err) {{}}
                        e.preventDefault();
                    }}

                    function onMove(e) {{
                        if (!isDragging) return;
                        const dx = e.clientX - startX;
                        const dy = e.clientY - startY;
                        if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved = true;

                        const boundary = {{
                            left: 0,
                            top: 0,
                            right: pWin.innerWidth,
                            bottom: pWin.innerHeight
                        }};

                        const wrapRect = wrap.getBoundingClientRect();
                        const pad = 8;
                        const targetDX = initX + dx;
                        const targetDY = initY + dy;

                        const minDX = initX - (wrapRect.left - (boundary.left + pad));
                        const maxDX = initX + ((boundary.right - pad) - wrapRect.right);
                        const minDY = initY - (wrapRect.top - (boundary.top + pad));
                        const maxDY = initY + ((boundary.bottom - pad) - wrapRect.bottom);

                        dragX = Math.max(minDX, Math.min(maxDX, targetDX));
                        dragY = Math.max(minDY, Math.min(maxDY, targetDY));

                        widget.style.transform = `translate3d(${{dragX}}px, ${{dragY}}px, 0)`;
                    }}

                    function onUp(e) {{
                        if (!isDragging) return;
                        isDragging = false;
                        widget.classList.remove('is-dragging');
                        try {{ wrap.releasePointerCapture(e.pointerId); }} catch(err) {{}}

                        if (moved) {{
                            const stopClick = ev => {{
                                ev.stopPropagation();
                                ev.preventDefault();
                                wrap.removeEventListener('click', stopClick, true);
                            }};
                            wrap.addEventListener('click', stopClick, true);
                        }}
                    }}

                    wrap.addEventListener('pointerdown', onDown);
                    wrap.addEventListener('pointermove', onMove);
                    wrap.addEventListener('pointerup', onUp);
                    wrap.addEventListener('pointercancel', onUp);
                }})();
            }}

            // 3. Đăng ký hàm điều khiển toàn cục trên window.parent
            let hideTimeout = null;
            let returnTimeout = null;

            pWin.jolyneResetToIdle = function() {{
                const img = pDoc.getElementById('jolyneImg');
                if (img && SPRITES['idle']) {{
                    img.style.opacity = '0.5';
                    setTimeout(() => {{
                        img.src = SPRITES['idle'];
                        img.style.opacity = '1';
                    }}, 100);
                }}
            }};

            pWin.jolyneTrigger = function(actionKey) {{
                const dataLines = DIALOGUES[actionKey] || DIALOGUES['idle'] || [];
                const img = pDoc.getElementById('jolyneImg');
                const bubble = pDoc.getElementById('jolyneBubble');
                if (!img || !bubble) return;

                if (hideTimeout) clearTimeout(hideTimeout);
                if (returnTimeout) clearTimeout(returnTimeout);

                if (SPRITES[actionKey]) {{
                    img.style.opacity = '0.4';
                    setTimeout(() => {{
                        img.src = SPRITES[actionKey];
                        img.style.opacity = '1';
                    }}, 100);
                }}

                if (dataLines.length > 0) {{
                    const line = dataLines[Math.floor(Math.random() * dataLines.length)];
                    bubble.innerHTML = line;
                    bubble.classList.add('show');
                }}

                img.classList.remove('animate-bounce', 'animate-shake');
                void img.offsetWidth;
                if (actionKey === 'panic' || actionKey === 'fight') {{
                    img.classList.add('animate-shake');
                }} else {{
                    img.classList.add('animate-bounce');
                }}

                // Tự động trở về pose mặc định sau khi hết thoại
                hideTimeout = setTimeout(() => {{
                    bubble.classList.remove('show');
                    if (actionKey !== 'idle') {{
                        returnTimeout = setTimeout(pWin.jolyneResetToIdle, 300);
                    }}
                }}, AUTO_HIDE_MS);
            }};

            // Gán sự kiện click vào bubble và avatar
            const bubbleEl = pDoc.getElementById('jolyneBubble');
            if (bubbleEl) {{
                bubbleEl.onclick = function() {{
                    this.classList.remove('show');
                    pWin.jolyneResetToIdle();
                }};
            }}

            const wrapEl = pDoc.getElementById('jolyneWrap');
            if (wrapEl) {{
                wrapEl.onclick = function() {{
                    const pool = ['shy', 'hug', 'water', 'idle'];
                    const act = pool[Math.floor(Math.random() * pool.length)];
                    pWin.jolyneTrigger(act);
                }};
            }}

            // Lần đầu tải trang -> chào nhẹ
            if (!pWin.__jolyne_greeting_done) {{
                pWin.__jolyne_greeting_done = true;
                setTimeout(() => pWin.jolyneTrigger('idle'), 1000);
            }}

        }} catch(err) {{
            console.error("Jolyne widget init error:", err);
        }}
    }})();
    </script>
    </body>
    </html>
    """

    st_module.components.v1.html(injection_script, height=0)


def render_mascot_tab_ui(st_module, her_name: str, my_name: str) -> None:
    """Vẽ giao diện tùy chỉnh mascot trong tab Navbar Streamlit."""
    settings = get_mascot_settings()

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
            help="Hiển thị nhân vật lơ lửng ở góc màn hình",
        )
        gogo_enabled = st_module.toggle(
            "Hiệu ứng Stand Menacing (ゴゴゴゴ) ⚡",
            value=settings.get("gogo_enabled", True),
            help="Hiệu ứng chữ JoJo bay bổng bên phải nhân vật",
        )

    with col2:
        st_module.markdown("#### 📏 Kích Thước & Tốc Độ")
        mascot_size = st_module.slider(
            "Kích thước nhân vật (pixel)",
            min_value=65,
            max_value=150,
            value=int(settings.get("size", 95)),
            step=5,
            help="Điều chỉnh độ lớn của bé Jolyne trên màn hình",
        )
        mascot_speed = st_module.slider(
            "Tốc độ lơ lửng (giây)",
            min_value=1.5,
            max_value=5.0,
            value=float(settings.get("speed", 3.2)),
            step=0.1,
            help="Thời gian một chu kỳ nhấp nhô lơ lửng",
        )

    st_module.markdown("---")
    st_module.markdown("#### 🎭 Thử Nghiệm Hành Động Trực Tiếp")
    st_module.caption("Bấm nút bên dưới để bé Jolyne đổi pose và nói thử ngay trên màn hình:")

    act_keys = list(ACTION_LABELS.keys())
    row1 = act_keys[:6]
    row2 = act_keys[6:]

    cols_r1 = st_module.columns(6)
    for i, k in enumerate(row1):
        icon, name = ACTION_LABELS[k]
        if cols_r1[i].button(f"{icon} {name}", key=f"btn_test_{k}", use_container_width=True):
            st_module.components.v1.html(
                f"<script>window.parent.jolyneTrigger && window.parent.jolyneTrigger('{k}');</script>",
                height=0,
            )

    cols_r2 = st_module.columns(6)
    for i, k in enumerate(row2):
        icon, name = ACTION_LABELS[k]
        if cols_r2[i].button(f"{icon} {name}", key=f"btn_test_{k}", use_container_width=True):
            st_module.components.v1.html(
                f"<script>window.parent.jolyneTrigger && window.parent.jolyneTrigger('{k}');</script>",
                height=0,
            )

    st_module.markdown("---")
    st_module.markdown("#### 💬 Chỉnh Sửa Lời Thoại Của Bé Jolyne")
    st_module.caption(
        "Mỗi dòng là một câu thoại khác nhau. Bé Jolyne sẽ chọn ngẫu nhiên 1 câu khi hành động kích hoạt. "
        "Bạn có thể dùng <code>{her_name}</code> hoặc <code>{my_name}</code> để chèn tên động."
    )

    dialogues = settings.get("dialogues", DEFAULT_SETTINGS["dialogues"])

    selected_act = st_module.selectbox(
        "Chọn hành động muốn chỉnh sửa lời thoại:",
        options=act_keys,
        format_func=lambda k: f"{ACTION_LABELS[k][0]} {ACTION_LABELS[k][1]}",
    )

    current_lines = dialogues.get(selected_act, [])
    current_text = "\n".join(current_lines)

    edited_text = st_module.text_area(
        f"Danh sách câu thoại cho [{ACTION_LABELS[selected_act][1]}]:",
        value=current_text,
        height=140,
        help="Mỗi dòng là một câu thoại riêng biệt",
    )

    st_module.markdown("<br>", unsafe_allow_html=True)
    save_col1, save_col2, _ = st_module.columns([1.5, 1.5, 3])

    if save_col1.button("💾 Lưu Cài Đặt Mascot", type="primary", use_container_width=True):
        new_lines = [l.strip() for l in edited_text.splitlines() if l.strip()]
        if not new_lines:
            new_lines = DEFAULT_SETTINGS["dialogues"].get(selected_act, ["Xin chào! 🌸"])

        dialogues[selected_act] = new_lines

        new_settings = {
            "enabled": mascot_enabled,
            "size": mascot_size,
            "speed": mascot_speed,
            "gogo_enabled": gogo_enabled,
            "auto_hide_seconds": settings.get("auto_hide_seconds", 4.5),
            "dialogues": dialogues,
        }
        save_mascot_settings(new_settings)
        st_module.success("✅ Đã lưu cấu hình bé Jolyne thành công! Cài đặt sẽ có hiệu lực ngay.")
        st_module.rerun()

    if save_col2.button("🔄 Khôi Phục Mặc Định", use_container_width=True):
        save_mascot_settings(DEFAULT_SETTINGS)
        st_module.info("Đã khôi phục cài đặt gốc của bé Jolyne!")
        st_module.rerun()
