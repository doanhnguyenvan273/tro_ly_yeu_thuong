import os
import time
import threading
import requests
from datetime import datetime, date
from typing import Dict, Any, List

import config
import database
import notifier

_LISTENER_RUNNING = False
_LISTENER_THREAD = None

DAY_NAMES = {
    0: "Thứ Hai",
    1: "Thứ Ba",
    2: "Thứ Tư",
    3: "Thứ Năm",
    4: "Thứ Sáu",
    5: "Thứ Bảy",
    6: "Chủ Nhật"
}

def build_schedule_response() -> str:
    """Tạo nội dung tin nhắn lịch học hôm nay + cả tuần."""
    now = datetime.now()
    today_dow = now.weekday()
    today_date_str = now.strftime("%d/%m/%Y")
    today_name = DAY_NAMES.get(today_dow, f"Thứ {today_dow + 2}")

    today_classes = database.get_schedules_by_day(today_dow)
    all_classes = database.get_all_schedules()

    lines = []
    lines.append("🎒 <b>THỜI KHÓA BIỂU & LỊCH HỌC</b> 🌸\n")

    # 1. Lịch hôm nay
    lines.append(f"📅 <b>HÔM NAY ({today_name}, {today_date_str}):</b>")
    if not today_classes:
        lines.append("<i>🎉 Hôm nay em/bạn không có lịch học nào cả! Nghỉ ngơi thật tốt nhé! 💖</i>\n")
    else:
        for c in today_classes:
            room_str = f" | 📍 <code>{c['room']}</code>" if c.get('room') else ""
            notes_str = f"\n   📝 <i>{c['notes']}</i>" if c.get('notes') else ""
            lines.append(
                f"• <b>{c['subject_name']}</b> ({c['start_time']} - {c['end_time']}){room_str}\n"
                f"   🏷️ {c.get('category', 'Môn học')}{notes_str}"
            )
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━")
    # 2. Lịch cả tuần
    lines.append("🗓️ <b>LỊCH HỌC CẢ TUẦN:</b>")
    if not all_classes:
        lines.append("<i>Chưa có môn học nào được lưu trong hệ thống.</i>")
    else:
        by_day: Dict[int, List[Dict[str, Any]]] = {}
        for c in all_classes:
            dow = c['day_of_week']
            by_day.setdefault(dow, []).append(c)

        for dow in range(7):
            if dow in by_day:
                d_name = DAY_NAMES.get(dow, f"Thứ {dow + 2}")
                is_today = " (Hôm nay ⭐)" if dow == today_dow else ""
                lines.append(f"\n🔹 <b>{d_name}{is_today}:</b>")
                for c in by_day[dow]:
                    r_str = f" | Phòng {c['room']}" if c.get('room') else ""
                    lines.append(f"  ▫️ {c['start_time']} - {c['end_time']}: <b>{c['subject_name']}</b>{r_str}")

    lines.append("\n💡 <i>Nhắn tin 'thuốc' để xem lịch uống thuốc, hoặc 'deadline' để xem bài tập cần làm nhé!</i>")
    return "\n".join(lines)


def build_medicine_response() -> str:
    """Tạo tin nhắn tra cứu lịch thuốc hôm nay."""
    today_str = date.today().strftime("%Y-%m-%d")
    meds = database.get_today_medicine_status(today_str)
    
    lines = ["💊 <b>LỊCH UỐNG THUỐC HÔM NAY</b> 🌸\n"]
    if not meds:
        lines.append("<i>Hôm nay em không có lịch uống thuốc nào. Mong em luôn khỏe mạnh nhé! 💖</i>")
    else:
        taken_count = sum(1 for m in meds if m["taken"])
        lines.append(f"📊 Tiến độ: <b>{taken_count}/{len(meds)}</b> liều đã uống\n")
        for m in meds:
            stt = "✅ Đã uống" if m["taken"] else "⏳ Chưa uống"
            lines.append(
                f"• <b>{m['medicine_name']}</b> — 🕒 <b>{m['time_slot']}</b>: {stt}\n"
                f"  🥄 Liều: {m['dosage']} (Ngày {m['day_number']}/{m['total_days']})"
            )
    return "\n".join(lines)


def build_deadline_response() -> str:
    """Tạo tin nhắn tra cứu deadline sắp tới."""
    tasks = database.get_all_tasks()
    active_tasks = [t for t in tasks if t.get("status") != "Đã hoàn thành"]
    
    lines = ["⏰ <b>DANH SÁCH DEADLINE & BÀI TẬP CẦN LÀM</b> 🌸\n"]
    if not active_tasks:
        lines.append("<i>🎉 Tuyệt vời! Hiện tại không có deadline nào đang chờ. Em thật giỏi! 💖</i>")
    else:
        for t in active_tasks:
            stt = "⏳ Đang làm" if t.get("status") == "Đang làm" else "📝 Chưa làm"
            lines.append(
                f"• <b>{t['task_name']}</b> ({t['subject_name']})\n"
                f"  📅 Hạn: <b>{t['deadline']}</b> | Trạng thái: {stt}"
            )
    return "\n".join(lines)


def build_help_response(name: str = "Bạn") -> str:
    """Tin nhắn chào mừng và hướng dẫn các lệnh tra cứu."""
    return (
        f"🌸 <b>Xin chào {name}! Em là Trợ Lý Yêu Thương 💖</b>\n\n"
        f"Bạn có thể nhắn tin cho em bất kỳ lúc nào để tra cứu nhanh:\n\n"
        f"📅 <b>Lịch học:</b> Gõ <code>lịch học</code>, <code>tkb</code> hoặc <code>hôm nay học gì</code> để xem lịch hôm nay & cả tuần.\n"
        f"💊 <b>Uống thuốc:</b> Gõ <code>thuốc</code> hoặc <code>uống thuốc</code> để xem các cữ thuốc hôm nay.\n"
        f"⏰ <b>Deadline:</b> Gõ <code>deadline</code> hoặc <code>bài tập</code> để xem danh sách việc cần nộp.\n\n"
        f"<i>Chúc bạn một ngày thật vui vẻ và ngập tràn năng lượng! ✨</i>"
    )


def handle_incoming_message(msg: Dict[str, Any]):
    """
    Xử lý một tin nhắn người dùng gửi tới bot.
    Tuân thủ quy tắc bảo mật: Chỉ cho phép ALLOWED_CHAT_IDS tương tác.
    """
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    sender_id_str = str(chat_id).strip()

    # BẢO MẬT & CHỐNG SPAM: Nếu đã cấu hình ALLOWED_CHAT_IDS, chỉ cho phép ID hợp lệ
    allowed = getattr(config, "ALLOWED_CHAT_IDS", [])
    if allowed and sender_id_str not in allowed:
        print(f"[Bảo Mật] Bỏ qua tin nhắn từ Chat ID lạ không trong ALLOWED_CHAT_IDS: {sender_id_str}")
        return

    text = (msg.get("text") or "").strip()
    if not text:
        return

    text_lower = text.lower()
    settings = config.load_settings()
    her_id = str(config.HER_CHAT_ID or settings.get("telegram_her_chat_id", "")).strip()
    my_id = str(config.YOUR_CHAT_ID or settings.get("telegram_my_chat_id", "")).strip()

    # Xác định danh xưng
    if sender_id_str == her_id:
        user_display = settings.get("her_name", "Em yêu 🌸")
    elif sender_id_str == my_id:
        user_display = settings.get("my_name", "Anh 💖")
    else:
        user_display = msg.get("from", {}).get("first_name", "Bạn")

    # 1. Tra cứu Lịch học
    schedule_keywords = [
        "lịch học", "lich hoc", "thời khóa biểu", "thoi khoa bieu", "tkb",
        "môn học", "mon hoc", "học gì", "hoc gi", "lịch", "lich",
        "/lichhoc", "/schedule"
    ]
    if any(k in text_lower for k in schedule_keywords):
        reply = build_schedule_response()
        notifier.send_telegram_message(chat_id, reply)
        print(f"[Bot Interactive] Đã trả lời lịch học cho {chat_id}")
        return

    # 2. Tra cứu Lịch uống thuốc
    med_keywords = ["thuốc", "thuoc", "uống thuốc", "uong thuoc", "lich thuoc", "/thuoc"]
    if any(k in text_lower for k in med_keywords):
        reply = build_medicine_response()
        notifier.send_telegram_message(chat_id, reply)
        print(f"[Bot Interactive] Đã trả lời lịch thuốc cho {chat_id}")
        return

    # 3. Tra cứu Deadline
    deadline_keywords = ["deadline", "bài tập", "bai tap", "nhiệm vụ", "nhiem vu", "/deadline"]
    if any(k in text_lower for k in deadline_keywords):
        reply = build_deadline_response()
        notifier.send_telegram_message(chat_id, reply)
        print(f"[Bot Interactive] Đã trả lời deadline cho {chat_id}")
        return

    # 4. Lệnh /start, /help hoặc câu chào
    greeting_keywords = ["/start", "/help", "help", "chào", "chao", "hi", "hello", "xin chào"]
    if any(text_lower.startswith(k) or text_lower == k for k in greeting_keywords):
        reply = build_help_response(user_display)
        notifier.send_telegram_message(chat_id, reply)
        print(f"[Bot Interactive] Đã gửi menu trợ giúp cho {chat_id}")
        return

    # 5. Nếu không khớp lệnh nào, gửi hướng dẫn nhẹ nhàng
    default_reply = (
        f"Dạ em đây! 🌸 Em chưa hiểu yêu cầu <i>\"{text}\"</i> của {user_display}.\n\n"
        f"👉 Bạn hãy nhắn: <b>lịch học</b>, <b>uống thuốc</b> hoặc <b>deadline</b> để em tra cứu ngay nha! 💖"
    )
    notifier.send_telegram_message(chat_id, default_reply)


def lang_nghe_tin_nhan():
    """
    Vòng lặp Long Polling nhận tin nhắn từ Telegram Bot 24/7.
    Chống sập hoàn toàn (Resilient Loop) với try-except và tự phục hồi khi mất mạng.
    """
    global _LISTENER_RUNNING
    _LISTENER_RUNNING = True
    print("[Bot Interactive] Bắt đầu lắng nghe tin nhắn Telegram (Long Polling 24/7)...")
    
    offset = None
    
    while _LISTENER_RUNNING:
        try:
            token = (config.TELEGRAM_BOT_TOKEN or config.load_settings().get("telegram_bot_token", "")).strip()
            if not token:
                time.sleep(5)
                continue

            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 20}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(url, params=params, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        if "message" in update:
                            try:
                                handle_incoming_message(update["message"])
                            except Exception as handle_err:
                                print(f"[Bot Interactive] Lỗi xử lý tin nhắn: {handle_err}")
            elif resp.status_code == 409:
                # Đang có tiến trình polling khác trùng lặp, chờ một chút
                time.sleep(5)
            else:
                time.sleep(3)
        except (requests.ConnectionError, requests.Timeout):
            # Mất mạng hoặc rớt kết nối tạm thời - không làm văng tiến trình
            time.sleep(3)
        except Exception as e:
            print(f"[Bot Interactive] Ngoại lệ vòng lặp polling: {e}")
            time.sleep(3)

    print("[Bot Interactive] Đã dừng lắng nghe Telegram.")


def start_telegram_listener():
    """Khởi động luồng lắng nghe tin nhắn Telegram nếu chưa chạy (dùng cho GUI)."""
    global _LISTENER_RUNNING, _LISTENER_THREAD
    if _LISTENER_RUNNING and _LISTENER_THREAD and _LISTENER_THREAD.is_alive():
        return

    _LISTENER_RUNNING = True
    _LISTENER_THREAD = threading.Thread(target=lang_nghe_tin_nhan, daemon=True, name="BotInteractiveListener")
    _LISTENER_THREAD.start()


def stop_telegram_listener():
    """Dừng luồng lắng nghe an toàn."""
    global _LISTENER_RUNNING
    _LISTENER_RUNNING = False
