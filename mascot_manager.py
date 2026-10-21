"""
mascot_manager.py
=================
Quản lý nhân vật đồng hành Chibi Jolyne Kujo (JoJo Part 6: Stone Ocean)
- 12 hành động chuẩn định dạng WebP siêu nhẹ (~50KB/ảnh, tổng ~640KB)
- Lưu trữ cấu hình: Bật/Tắt, kích thước, hiệu ứng Menacing, lời thoại tùy chỉnh
- Widget lơ lửng điều khiển bằng GPU (0% lag/reflow), kéo thả PointerEvents an toàn
- Tab điều hướng tùy chỉnh trên Navbar Streamlit
"""

import os
import json
import base64
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

# Cache Base64 sprites trong bộ nhớ
_SPRITES_CACHE: Dict[str, str] = {}


def get_mascot_settings() -> Dict[str, Any]:
    """Đọc cấu hình mascot, nếu chưa có thì khởi tạo mặc định."""
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


def get_sprite_base64(action_key: str) -> str:
    """Đọc và cache file WebP tương ứng dưới dạng data URI Base64."""
    if action_key in _SPRITES_CACHE:
        return _SPRITES_CACHE[action_key]
    
    webp_path = os.path.join(MASCOT_DIR, f"jolyne_{action_key}.webp")
    if not os.path.exists(webp_path):
        webp_path = os.path.join(MASCOT_DIR, f"jolyne_{action_key}.png")
    
    if os.path.exists(webp_path):
        mime = "image/webp" if webp_path.endswith(".webp") else "image/png"
        with open(webp_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        uri = f"data:{mime};base64,{b64}"
        _SPRITES_CACHE[action_key] = uri
        return uri
    return ""


def get_all_sprites() -> Dict[str, str]:
    """Lấy toàn bộ 12 sprite base64."""
    return {k: get_sprite_base64(k) for k in ACTION_LABELS.keys()}


def build_floating_mascot_html(her_name: str, my_name: str) -> str:
    """
    Sinh mã HTML, CSS và JavaScript cho bé Jolyne lơ lửng trên toàn bộ Web App.
    - GPU-accelerated: translate3d
    - Kéo thả an toàn với setPointerCapture, không trôi khỏi màn hình
    - Tự động quay về pose mặc định (như hình) sau 4.5s khi thoại tắt
    - Stand Menacing effect (ゴゴゴゴ) ở bên phải nhân vật
    """
    settings = get_mascot_settings()
    if not settings.get("enabled", True):
        return ""

    size = int(settings.get("size", 95))
    speed = float(settings.get("speed", 3.2))
    gogo_enabled = bool(settings.get("gogo_enabled", True))
    auto_hide_sec = float(settings.get("auto_hide_seconds", 4.5))

    raw_dialogues = settings.get("dialogues", DEFAULT_SETTINGS["dialogues"])
    formatted_dialogues: Dict[str, List[str]] = {}
    for act, lines in raw_dialogues.items():
        fmt_lines = []
        for line in lines:
            fmt_lines.append(line.replace("{her_name}", her_name).replace("{my_name}", my_name))
        formatted_dialogues[act] = fmt_lines

    sprites = get_all_sprites()
    sprites_json = json.dumps(sprites, ensure_ascii=False)
    dialogues_json = json.dumps(formatted_dialogues, ensure_ascii=False)
    gogo_display = "block" if gogo_enabled else "none"

    return f"""
    <!-- ══════════════════════════════════════════════════════════
         BÉ CHIBI JOLYNE KUJO (FLOATING MASCOT COMPONENT)
         ══════════════════════════════════════════════════════════ -->
    <style>
        .jolyne-floating-container {{
            position: fixed !important;
            bottom: 24px !important;
            right: 24px !important;
            z-index: 999999 !important;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            user-select: none;
            -webkit-user-select: none;
            will-change: transform;
            transform: translate3d(0, 0, 0);
        }}

        .jolyne-floating-container.is-dragging {{
            cursor: grabbing !important;
        }}

        /* Bóng thoại lời dặn phong cách JoJo Glassmorphism */
        .jolyne-speech-bubble {{
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 2px solid #ffd1dc;
            border-radius: 18px 18px 4px 18px;
            padding: 12px 16px;
            box-shadow: 0 10px 30px rgba(216, 17, 89, 0.16);
            color: #9d174d;
            font-size: 0.88rem;
            line-height: 1.5;
            font-weight: 600;
            max-width: 260px;
            margin-bottom: 8px;
            margin-right: 14px;
            opacity: 0;
            visibility: hidden;
            pointer-events: auto;
            cursor: pointer;
            transform-origin: bottom right;
            transform: scale(0.6) translate3d(0, 10px, 0);
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
        }}

        .jolyne-speech-bubble.show {{
            opacity: 1;
            visibility: visible;
            transform: scale(1) translate3d(0, 0, 0);
        }}

        .jolyne-speech-bubble::after {{
            content: "";
            position: absolute;
            bottom: -8px;
            right: 28px;
            width: 12px;
            height: 12px;
            background: white;
            border-right: 2px solid #ffd1dc;
            border-bottom: 2px solid #ffd1dc;
            transform: rotate(45deg);
        }}

        /* Khung nhân vật Jolyne */
        .jolyne-avatar-wrap {{
            position: relative;
            pointer-events: auto;
            cursor: grab;
            touch-action: none;
            transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}

        .jolyne-avatar-img {{
            width: {size}px;
            height: auto;
            display: block;
            filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.14));
            animation: jolyneFloat {speed}s ease-in-out infinite alternate;
            will-change: transform;
            transform-origin: bottom center;
            transition: opacity 0.2s ease;
            user-select: none;
            -webkit-user-select: none;
            -webkit-user-drag: none;
            user-drag: none;
            pointer-events: none;
        }}

        /* Gợi ý kéo hiện khi hover */
        .drag-hint {{
            position: absolute;
            top: -24px;
            left: 50%;
            transform: translateX(-50%) scale(0);
            background: rgba(244, 63, 94, 0.90);
            color: white;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 20px;
            white-space: nowrap;
            pointer-events: none;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            z-index: 100001;
        }}

        .jolyne-avatar-wrap:hover .drag-hint {{
            transform: translateX(-50%) scale(1);
        }}

        /* Keyframes */
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

        /* Hiệu ứng hạt lấp lánh */
        .sparkle-particle {{
            position: absolute;
            font-size: 1.15rem;
            pointer-events: none;
            opacity: 0;
            animation: particleFly 1s ease-out forwards;
            z-index: 100000;
        }}

        @keyframes particleFly {{
            0% {{
                opacity: 1;
                transform: translate3d(0, 0, 0) scale(0.5);
            }}
            100% {{
                opacity: 0;
                transform: translate3d(var(--tx), var(--ty), 0) scale(1.4) rotate(var(--rot));
            }}
        }}

        /* ── Stand Menacing Effect (ゴゴゴゴ) BÊN PHẢI NHÂN VẬT ── */
        .gogo-container {{
            position: absolute;
            left: 100%;
            bottom: 0;
            width: 70px;
            height: 120%;
            pointer-events: none;
            z-index: 100002;
            overflow: visible;
            display: {gogo_display};
        }}

        .gogo-glyph {{
            position: absolute;
            font-family: 'Noto Sans JP', 'MS Gothic', sans-serif, serif;
            font-weight: 900;
            font-style: italic;
            background: linear-gradient(165deg, #e879f9 0%, #a855f7 35%, #6b21a8 75%, #3b0764 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 5px rgba(216, 70, 239, 0.75))
                    drop-shadow(1.5px 2.5px 0 rgba(0, 0, 0, 0.6));
            will-change: transform, opacity;
            user-select: none;
            letter-spacing: -2px;
            opacity: 0;
            line-height: 1;
        }}

        @keyframes gogoFloat0 {{
            0%   {{ transform: translate3d(0, 0, 0)       rotate(-10deg) scale(0.95); opacity: 0; }}
            18%  {{ opacity: 0.95; }}
            55%  {{ transform: translate3d(6px, -18px, 0) rotate(-14deg) scale(1.08); opacity: 0.85; }}
            100% {{ transform: translate3d(12px, -36px, 0) rotate(-8deg) scale(0.80); opacity: 0; }}
        }}
        @keyframes gogoFloat1 {{
            0%   {{ transform: translate3d(0, 0, 0)       rotate(8deg)   scale(0.90); opacity: 0; }}
            15%  {{ opacity: 0.90; }}
            50%  {{ transform: translate3d(8px, -14px, 0) rotate(12deg)  scale(1.02); opacity: 0.80; }}
            100% {{ transform: translate3d(4px, -32px, 0) rotate(6deg)   scale(0.75); opacity: 0; }}
        }}
        @keyframes gogoFloat2 {{
            0%   {{ transform: translate3d(0, 0, 0)       rotate(-6deg)  scale(1.10); opacity: 0; }}
            20%  {{ opacity: 0.95; }}
            55%  {{ transform: translate3d(10px, -12px, 0) rotate(-9deg) scale(1.18); opacity: 0.88; }}
            100% {{ transform: translate3d(15px, -28px, 0) rotate(-4deg) scale(0.88); opacity: 0; }}
        }}
        @keyframes gogoFloat3 {{
            0%   {{ transform: translate3d(0, 0, 0)       rotate(14deg)  scale(0.85); opacity: 0; }}
            16%  {{ opacity: 0.85; }}
            55%  {{ transform: translate3d(7px, -15px, 0) rotate(18deg)  scale(0.96); opacity: 0.75; }}
            100% {{ transform: translate3d(11px, -34px, 0) rotate(12deg) scale(0.70); opacity: 0; }}
        }}
        @keyframes gogoFloat4 {{
            0%   {{ transform: translate3d(0, 0, 0)       rotate(-16deg) scale(0.75); opacity: 0; }}
            14%  {{ opacity: 0.80; }}
            50%  {{ transform: translate3d(5px, -10px, 0) rotate(-20deg) scale(0.85); opacity: 0.70; }}
            100% {{ transform: translate3d(8px, -24px, 0) rotate(-12deg) scale(0.60); opacity: 0; }}
        }}
    </style>

    <div class="jolyne-floating-container" id="jolyneWidget">
        <!-- Bóng thoại -->
        <div class="jolyne-speech-bubble" id="jolyneBubble" onclick="window.jolyneDismissBubble();" title="Bấm để ẩn thoại">
            Chào {her_name}! Tớ là Jolyne Kujo nè! 🦋✨
        </div>

        <!-- Thân nhân vật -->
        <div class="jolyne-avatar-wrap" id="jolyneWrap" onclick="window.jolyneInteract();">
            <div class="drag-hint">✥ kéo để di chuyển</div>
            <!-- Khí thế Stand Menacing bên phải -->
            <div class="gogo-container" id="gogoContainer"></div>
            <img src="{sprites.get('idle', '')}" id="jolyneImg" class="jolyne-avatar-img" alt="Jolyne Chibi" draggable="false" />
        </div>
    </div>

    <script>
    (function() {{
        // Tránh chạy trùng lặp khi Streamlit re-render
        if (window.__jolyne_initialized) return;
        window.__jolyne_initialized = true;

        const SPRITES = {sprites_json};
        const DIALOGUES = {dialogues_json};
        const AUTO_HIDE_SEC = {auto_hide_sec};

        let hideTimeout = null;
        let returnTimeout = null;

        // Đưa về tư thế mặc định
        window.jolyneResetToIdle = function() {{
            const img = document.getElementById('jolyneImg');
            if (img && SPRITES['idle']) {{
                img.style.opacity = '0.5';
                setTimeout(() => {{
                    img.src = SPRITES['idle'];
                    img.style.opacity = '1';
                }}, 100);
            }}
        }};

        window.jolyneDismissBubble = function() {{
            const bubble = document.getElementById('jolyneBubble');
            if (bubble) bubble.classList.remove('show');
            window.jolyneResetToIdle();
        }};

        window.jolyneTrigger = function(actionKey) {{
            const dataLines = DIALOGUES[actionKey] || DIALOGUES['idle'] || [];
            const img = document.getElementById('jolyneImg');
            const bubble = document.getElementById('jolyneBubble');
            if (!img || !bubble) return;

            if (hideTimeout) clearTimeout(hideTimeout);
            if (returnTimeout) clearTimeout(returnTimeout);

            // Đổi hình ảnh
            if (SPRITES[actionKey]) {{
                img.style.opacity = '0.4';
                setTimeout(() => {{
                    img.src = SPRITES[actionKey];
                    img.style.opacity = '1';
                }}, 100);
            }}

            // Đổi câu thoại
            if (dataLines.length > 0) {{
                const line = dataLines[Math.floor(Math.random() * dataLines.length)];
                bubble.innerHTML = line;
                bubble.classList.add('show');
            }}

            // Hiệu ứng nảy
            img.classList.remove('animate-bounce', 'animate-shake');
            void img.offsetWidth;
            if (actionKey === 'panic' || actionKey === 'fight') {{
                img.classList.add('animate-shake');
            }} else {{
                img.classList.add('animate-bounce');
            }}

            window.jolyneSpawnParticles();

            // Tự động thu thoại và TRỞ VỀ POSE MẶC ĐỊNH
            hideTimeout = setTimeout(() => {{
                bubble.classList.remove('show');
                if (actionKey !== 'idle') {{
                    returnTimeout = setTimeout(window.jolyneResetToIdle, 300);
                }}
            }}, AUTO_HIDE_SEC * 1000);
        }};

        // Click vào nhân vật -> E thẹn hoặc lời nhắc ngẫu nhiên
        window.jolyneInteract = function() {{
            const pool = ['shy', 'hug', 'water', 'idle'];
            const act = pool[Math.floor(Math.random() * pool.length)];
            window.jolyneTrigger(act);
        }};

        window.jolyneSpawnParticles = function() {{
            const wrap = document.getElementById('jolyneWrap');
            if (!wrap) return;
            const icons = ['🦋', '💖', '✨', '⭐', '🌸'];
            for (let i = 0; i < 4; i++) {{
                const p = document.createElement('div');
                p.className = 'sparkle-particle';
                p.innerText = icons[Math.floor(Math.random() * icons.length)];
                const tx = (Math.random() - 0.5) * 80;
                const ty = -(30 + Math.random() * 50);
                const rot = (Math.random() - 0.5) * 60;
                p.style.setProperty('--tx', `${{tx}}px`);
                p.style.setProperty('--ty', `${{ty}}px`);
                p.style.setProperty('--rot', `${{rot}}deg`);
                p.style.left = '45%';
                p.style.top = '20%';
                wrap.appendChild(p);
                setTimeout(() => {{ p.remove(); }}, 1000);
            }}
        }};

        // Hiệu ứng Stand Menacing (ゴゴゴゴ)
        (function initGogo() {{
            const container = document.getElementById('gogoContainer');
            if (!container) return;
            container.innerHTML = '';
            const GLYPHS = [
                {{ text: 'ゴ', fs: '2.1rem',  b: '78%', l: '4px',  anim: 'gogoFloat0', delay: 0.00, dur: 2.3 }},
                {{ text: 'ゴ', fs: '1.6rem',  b: '60%', l: '14px', anim: 'gogoFloat1', delay: 0.40, dur: 2.7 }},
                {{ text: 'ゴ', fs: '1.3rem',  b: '43%', l: '8px',  anim: 'gogoFloat2', delay: 0.75, dur: 2.1 }},
                {{ text: 'ゴ', fs: '1.05rem', b: '27%', l: '18px', anim: 'gogoFloat3', delay: 1.05, dur: 2.9 }},
                {{ text: 'ゴ', fs: '0.82rem', b: '12%', l: '10px', anim: 'gogoFloat4', delay: 1.35, dur: 2.5 }},
            ];

            const els = GLYPHS.map(g => {{
                const el = document.createElement('div');
                el.className = 'gogo-glyph';
                el.textContent = g.text;
                el.style.fontSize                 = g.fs;
                el.style.bottom                   = g.b;
                el.style.left                     = g.l;
                el.style.animationName            = g.anim;
                el.style.animationDuration        = g.dur + 's';
                el.style.animationDelay           = g.delay + 's';
                el.style.animationTimingFunction  = 'ease-in-out';
                el.style.animationIterationCount  = 'infinite';
                el.style.animationFillMode        = 'both';
                container.appendChild(el);
                return el;
            }});

            setInterval(() => {{
                GLYPHS.forEach((g, i) => {{
                    const jx = ((Math.random() - 0.5) * 6).toFixed(1);
                    const jy = ((Math.random() - 0.5) * 4).toFixed(1);
                    els[i].style.transform = `translate(${{jx}}px, ${{jy}}px)`;
                }});
            }}, 3500);
        }})();

        // Kéo thả bằng Pointer Events (chuẩn giữ chuột mới di chuyển, buông ra là dừng ngay)
        (function initDrag() {{
            const widget = document.getElementById('jolyneWidget');
            const wrap   = document.getElementById('jolyneWrap');
            if (!widget || !wrap) return;

            let isDragging = false;
            let dragX = 0, dragY = 0;
            let startPointerX = 0, startPointerY = 0;
            let initialDragX = 0, initialDragY = 0;
            let hasMovedSignificantly = false;

            wrap.addEventListener('dragstart', e => {{ e.preventDefault(); return false; }});

            function onPointerDown(e) {{
                if (e.button !== undefined && e.button !== 0) return;
                isDragging = true;
                hasMovedSignificantly = false;
                startPointerX = e.clientX;
                startPointerY = e.clientY;
                initialDragX = dragX;
                initialDragY = dragY;

                widget.classList.add('is-dragging');
                try {{ wrap.setPointerCapture(e.pointerId); }} catch(err) {{}}
                e.preventDefault();
            }}

            function onPointerMove(e) {{
                if (!isDragging) return;
                const dx = e.clientX - startPointerX;
                const dy = e.clientY - startPointerY;

                if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {{
                    hasMovedSignificantly = true;
                }}

                // Giới hạn toàn bộ màn hình Safe-area
                const boundary = {{
                    left: 0,
                    top: 0,
                    right: window.innerWidth,
                    bottom: window.innerHeight
                }};

                const wrapRect = wrap.getBoundingClientRect();
                const pad = 8;

                const targetDX = initialDragX + dx;
                const targetDY = initialDragY + dy;

                const minDX = initialDragX - (wrapRect.left - (boundary.left + pad));
                const maxDX = initialDragX + ((boundary.right - pad) - wrapRect.right);
                const minDY = initialDragY - (wrapRect.top - (boundary.top + pad));
                const maxDY = initialDragY + ((boundary.bottom - pad) - wrapRect.bottom);

                dragX = Math.max(minDX, Math.min(maxDX, targetDX));
                dragY = Math.max(minDY, Math.min(maxDY, targetDY));

                widget.style.transform = `translate3d(${{dragX}}px, ${{dragY}}px, 0)`;
            }}

            function onPointerUp(e) {{
                if (!isDragging) return;
                isDragging = false;
                widget.classList.remove('is-dragging');
                try {{ wrap.releasePointerCapture(e.pointerId); }} catch(err) {{}}

                if (hasMovedSignificantly) {{
                    const suppressClick = ev => {{
                        ev.stopPropagation();
                        ev.preventDefault();
                        wrap.removeEventListener('click', suppressClick, true);
                    }};
                    wrap.addEventListener('click', suppressClick, true);
                }}
            }}

            wrap.addEventListener('pointerdown', onPointerDown);
            wrap.addEventListener('pointermove', onPointerMove);
            wrap.addEventListener('pointerup', onPointerUp);
            wrap.addEventListener('pointercancel', onPointerUp);
        }})();

        // Chào mừng lần đầu khi mở app
        setTimeout(() => {{
            window.jolyneTrigger('idle');
        }}, 800);
    }})();
    </script>
    """


def render_mascot_tab_ui(st_module, her_name: str, my_name: str) -> None:
    """
    Vẽ giao diện tùy chỉnh mascot trong tab Navbar Streamlit:
    - Bật / Tắt nhân vật
    - Kích thước nhân vật (slider)
    - Hiệu ứng Stand Menacing (toggle)
    - Tùy chỉnh danh sách câu thoại theo từng hành động
    - Thử nghiệm tương tác trực tiếp
    """
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

    # ── Khối 1: Cài đặt hiển thị & Kích thước ──
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

    # ── Khối 2: Thử nghiệm tương tác trực tiếp ──
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
                f"<script>window.parent.window.jolyneTrigger && window.parent.window.jolyneTrigger('{k}');</script>",
                height=0,
            )

    cols_r2 = st_module.columns(6)
    for i, k in enumerate(row2):
        icon, name = ACTION_LABELS[k]
        if cols_r2[i].button(f"{icon} {name}", key=f"btn_test_{k}", use_container_width=True):
            st_module.components.v1.html(
                f"<script>window.parent.window.jolyneTrigger && window.parent.window.jolyneTrigger('{k}');</script>",
                height=0,
            )

    # ── Khối 3: Tùy chỉnh danh sách lời thoại ──
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

    # Nút lưu cấu hình
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
