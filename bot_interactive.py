import os
import sys
import time
import threading
import requests
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import config
import database
import notifier
import menstrual_ml
import deadline_ml

_LISTENER_RUNNING = False
_LISTENER_THREAD = None

DAY_NAMES = {
    0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư",
    3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"
}

# ======================= BUILD RESPONSE FUNCTIONS =======================

def build_schedule_response(for_tomorrow: bool = False) -> str:
    """Tạo nội dung tin nhắn lịch học hôm nay hoặc ngày mai + cả tuần."""
    now = config.get_now()
    target_date = now + timedelta(days=1) if for_tomorrow else now
    target_dow = target_date.weekday()
    target_date_str = target_date.strftime("%d/%m/%Y")
    target_day_name = DAY_NAMES.get(target_dow, f"Thứ {target_dow + 2}")

    target_classes = database.get_schedules_by_day(target_dow)
    all_classes = database.get_all_schedules()

    lines = []
    title_label = "NGÀY MAI" if for_tomorrow else "HÔM NAY"
    lines.append(f"🎒 <b>THỜI KHÓA BIỂU & LỊCH HỌC {title_label}</b> 🌸\n")

    lines.append(f"📅 <b>{title_label} ({target_day_name}, {target_date_str}):</b>")
    if not target_classes:
        lines.append(f"<i>🎉 {title_label.lower().capitalize()} em không có lịch học nào cả! Nghỉ ngơi thật tốt nhé! 💖</i>\n")
    else:
        for c in target_classes:
            room_str = f" | 📍 Phòng <code>{c['room']}</code>" if c.get('room') else ""
            notes_str = f"\n   📝 <i>{c['notes']}</i>" if c.get('notes') else ""
            lines.append(
                f"• <b>{c['subject_name']}</b> ({c['start_time']} - {c['end_time']}){room_str}\n"
                f"   🏷️ {c.get('category', 'Môn học')}{notes_str}"
            )
        lines.append("")

    if not for_tomorrow:
        lines.append("━━━━━━━━━━━━━━━━━━")
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
                    is_today = " (Hôm nay ⭐)" if dow == now.weekday() else ""
                    lines.append(f"\n🔹 <b>{d_name}{is_today}:</b>")
                    for c in by_day[dow]:
                        r_str = f" | Phòng {c['room']}" if c.get('room') else ""
                        lines.append(f"  ▫️ {c['start_time']} - {c['end_time']}: <b>{c['subject_name']}</b>{r_str}")

    lines.append("\n💡 <i>Nhắn <code>mai</code> để xem lịch ngày mai, <code>thuốc</code> để xem cữ thuốc, hoặc <code>chu kỳ</code> để xem dự đoán sinh lý nhé!</i>")
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
        lines.append("\n👉 <i>Uống xong em nhắn <code>đã uống thuốc</code> để bot ghi nhận nhé! 🍵</i>")
    return "\n".join(lines)


def handle_take_medicine_command(user_display: str) -> str:
    """Xử lý xác nhận đã uống thuốc trực tiếp qua Telegram."""
    today_str = date.today().strftime("%Y-%m-%d")
    meds = database.get_today_medicine_status(today_str)

    if not meds:
        return f"💖 Hôm nay {user_display} không có đơn thuốc nào cần uống cả. Chúc em luôn khỏe mạnh nhé!"

    untaken = [m for m in meds if not m["taken"]]
    if not untaken:
        return f"🌸 Bé giỏi lắm! Hôm nay {user_display} đã uống đủ tất cả các liều thuốc rồi nhé! 🍵💖"

    now_str = config.get_now().strftime("%H:%M")
    marked_names = []
    for m in untaken:
        database.log_medicine_taken(m["medicine_id"], today_str, m["time_slot"])
        marked_names.append(f"{m['medicine_name']} ({m['time_slot']})")

    joined_names = ", ".join(marked_names)
    return (
        f"✅ <b>ĐÃ GHI NHẬN UỐNG THUỐC!</b> 🌸\n\n"
        f"Bé giỏi quá! Em đã ghi nhận liều: <b>{joined_names}</b> vào lúc {now_str} hôm nay rồi nhé!\n"
        f"Uống nhiều nước ấm và nghỉ ngơi cho mau khỏe nha cô bé của anh! 🍵💖"
    )


def build_deadline_response() -> str:
    """Tạo tin nhắn tra cứu deadline sắp tới."""
    tasks = database.get_all_tasks()
    active_tasks = [t for t in tasks if t.get("status") != "Đã hoàn thành"]

    lines = ["⏰ <b>DANH SÁCH DEADLINE & BÀI TẬP CẦN LÀM</b> 🌸\n"]
    if not active_tasks:
        lines.append("<i>🎉 Tuyệt vời! Hiện tại không có deadline nào đang chờ. Em thật giỏi! 💖</i>")
    else:
        now = config.get_now()
        for t in active_tasks:
            stt = "⏳ Đang làm" if t.get("status") == "Đang làm" else "📝 Chưa làm"
            # Tính giờ còn lại
            try:
                deadline_dt = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                h_left = (deadline_dt - now).total_seconds() / 3600
                if h_left <= 3:
                    urgency = " ⚡ <b>GẤP!</b>"
                elif h_left <= 24:
                    urgency = f" 🔴 còn {int(h_left)}h"
                elif h_left <= 72:
                    urgency = f" 🟡 còn ~{int(h_left // 24)} ngày"
                else:
                    urgency = ""
            except Exception:
                urgency = ""
            lines.append(
                f"• <b>{t['task_name']}</b> ({t['subject_name']})\n"
                f"  📅 Hạn: <b>{t['deadline']}</b>{urgency} | Trạng thái: {stt}"
            )
    lines.append("\n💡 <i>Nhắn <code>lịch học</code> để kiểm tra lịch học tuần này nhé!</i>")
    return "\n".join(lines)


def build_cycle_response() -> str:
    """Tạo tin nhắn dự đoán chu kỳ sinh lý AI."""
    pred = menstrual_ml.predict_next_cycle()
    if not pred.get("has_data"):
        return (
            "🌸 <b>CHU KỲ SINH LÝ PHỤ NỮ</b> 🌸\n\n"
            "Hiện tại chưa có dữ liệu chu kỳ nào. Khi bắt đầu kỳ mới, em chỉ cần nhắn "
            "<code>hôm nay đến kỳ</code> để AI bắt đầu học và theo dõi chu kỳ cho em nhé! 💖"
        )

    days_left = pred["days_left"]
    next_date = pred["predicted_next_date"]
    pms_date = pred["pms_start_date"]
    cycle_len = pred["predicted_length"]

    advice = pred.get("advice_for_her")
    if not advice:
        if days_left <= 0:
            advice = "💖 <b>Hôm nay hoặc đã đến ngày bắt đầu kỳ mới rồi!</b> Em nhớ giữ ấm bụng, mang theo đồ dùng cá nhân và chườm nóng nếu đau nhé!"
        elif days_left <= 4:
            advice = f"🌸 <b>Đang trong giai đoạn PMS (còn {days_left} ngày)!</b> Mấy ngày này em nhớ uống nước ấm, ngủ sớm, hạn chế đồ lạnh và đồ cay nha em!"
        else:
            advice = f"✨ <b>Sức khỏe bình thường</b>, còn <b>{days_left} ngày</b> nữa mới đến chu kỳ kế tiếp. Chúc em mỗi ngày đều tràn đầy năng lượng!"

    return (
        f"🌸 <b>DỰ ĐOÁN CHU KỲ SINH LÝ (AI)</b> 🌸\n\n"
        f"📅 Ngày dự kiến bắt đầu: <b>{next_date}</b>\n"
        f"⏳ Còn lại: <b>{max(0, days_left)} ngày</b>\n"
        f"🔮 Độ dài chu kỳ dự kiến: <b>{cycle_len} ngày</b>\n"
        f"🍵 Giai đoạn PMS bắt đầu từ: <b>{pms_date}</b>\n\n"
        f"{advice}\n\n"
        f"💡 <i>Khi bắt đầu kỳ mới, em chỉ cần nhắn <code>hôm nay đến kỳ</code> là bot tự động cập nhật ngay nhé!</i>"
    )


def handle_log_period_start(user_display: str) -> str:
    """Ghi nhận bắt đầu kỳ mới trực tiếp qua tin nhắn Telegram."""
    today_str = date.today().strftime("%Y-%m-%d")
    database.add_menstrual_record(today_str)
    menstrual_ml.retrain_model()

    secret_msg = (
        f"🍓 <b>[CHẾ ĐỘ BÍ MẬT - THÔNG BÁO CHO BẠN]</b> 🍓\n\n"
        f"Sếp ơi! {user_display} vừa thông báo hôm nay bắt đầu kỳ mới rồi ({today_str}).\n"
        f"Mấy ngày này em ấy sẽ rất mệt, đau lưng và đau bụng. Nhớ chuẩn bị túi chườm ấm, trà gừng, đồ ngọt và kiên nhẫn yêu thương em ấy nhiều hơn nhé! 🍫🧸💖"
    )
    notifier.notify_you_secret(secret_msg)

    return (
        f"💖 <b>ĐÃ GHI NHẬN BẮT ĐẦU CHU KỲ MỚI!</b> 🌸\n\n"
        f"Em đã lưu ngày hôm nay ({today_str}) vào hệ thống và huấn luyện lại AI cơ địa cho {user_display} rồi nhé.\n\n"
        f"🍵 <b>Lời dặn yêu thương:</b>\n"
        f"• Nhớ uống nước ấm, ăn đồ nóng, hạn chế đồ lạnh và cà phê nhé.\n"
        f"• Chườm ấm bụng và nghỉ ngơi thật nhiều nha.\n"
        f"• Em đã nhắn tin 'nhắc nhở' anh ấy chăm sóc em thật chu đáo rồi đó! Thương em nhiều! 🧸🍓✨"
    )


def build_status_response() -> str:
    """Trả về trạng thái tổng quan hệ thống: số môn, deadline, thuốc, chu kỳ."""
    now = config.get_now()
    today_str = now.strftime("%Y-%m-%d")

    # Lịch học
    all_schedules = database.get_all_schedules()
    today_classes = database.get_schedules_by_day(now.weekday())

    # Deadline
    all_tasks = database.get_all_tasks()
    active_tasks = [t for t in all_tasks if t.get("status") != "Đã hoàn thành"]

    # Thuốc
    meds_today = database.get_today_medicine_status(today_str)
    taken_count = sum(1 for m in meds_today if m["taken"])

    # Chu kỳ
    pred = menstrual_ml.predict_next_cycle()
    cycle_info = ""
    if pred.get("has_data"):
        days_left = pred.get("days_left", "?")
        cycle_info = f"\n🌸 Chu kỳ sinh lý: còn <b>{days_left} ngày</b> đến kỳ tiếp theo"

    return (
        f"📊 <b>TRẠNG THÁI HỆ THỐNG TRỢ LÝ YÊU THƯƠNG</b> 🌸\n\n"
        f"🕒 Thời điểm kiểm tra: <b>{now.strftime('%H:%M %d/%m/%Y')}</b>\n"
        f"🌐 Server: <b>Online 24/7 ✅</b>\n\n"
        f"📚 Lịch học: <b>{len(all_schedules)} môn</b> trong DB | Hôm nay: <b>{len(today_classes)} môn</b>\n"
        f"⏰ Deadline đang chờ: <b>{len(active_tasks)} việc</b>\n"
        f"💊 Thuốc hôm nay: <b>{taken_count}/{len(meds_today)}</b> liều đã uống"
        f"{cycle_info}\n\n"
        f"💖 <i>Mọi thứ đang hoạt động tốt! Anh luôn dõi theo em nhé!</i>"
    )


def build_attendance_response() -> str:
    """Trả về thống kê điểm danh theo từng môn học."""
    stats = database.get_all_attendance_stats()
    if not stats:
        return (
            "📋 <b>THỐNG KÊ ĐIỂM DANH</b> 🌸\n\n"
            "<i>Chưa có dữ liệu điểm danh. Vào app để ghi nhận điểm danh sau mỗi buổi học nhé!</i>"
        )

    lines = ["📋 <b>THỐNG KÊ ĐIỂM DANH THEO MÔN</b> 🌸\n"]
    for s in stats:
        max_abs = s.get('max_absences', 3)
        rem = s.get('remaining_absences', max(0, max_abs - s['absent']))
        if s.get("is_warning"):
            status_tag = " 🚨 <b>(NGUY CƠ CẤM THI!)</b>"
        elif rem == 1:
            status_tag = " ⚠️ <i>(Sắp hết lượt nghỉ)</i>"
        else:
            status_tag = " ✅"

        lines.append(
            f"• <b>{s['subject_name']}</b>{status_tag}\n"
            f"  ✅ Đã đi: {s['attended']} | ❌ Đã vắng: <b>{s['absent']}/{max_abs} buổi tối đa</b> | 💻 Online: {s['online']}\n"
            f"  📊 Tổng: {s['total']} buổi | Còn được nghỉ: <b>{rem} buổi</b>"
        )
    lines.append("\n💡 <i>Bot sẽ tự động cảnh báo khi em chạm ngưỡng số buổi nghỉ cho phép. Cố gắng đi đủ nhé bé yêu! 💪</i>")
    return "\n".join(lines)


def build_help_response(name: str = "Bạn") -> str:
    """Tin nhắn chào mừng và hướng dẫn các lệnh tra cứu thông minh 24/7."""
    return (
        f"🌸 <b>Xin chào {name}! Em là Trợ Lý Yêu Thương 💖</b>\n\n"
        f"Hệ thống đang chạy ngầm <b>24/7</b> trên Cloud. Bạn có thể nhắn tin tra cứu mọi lúc:\n\n"
        f"📅 <b>Lịch học:</b> <code>lịch học</code> / <code>tkb</code> / <code>hôm nay học gì</code>\n"
        f"📅 <b>Lịch mai:</b> <code>mai học gì</code> / <code>ngày mai</code>\n"
        f"💊 <b>Uống thuốc:</b> <code>thuốc</code> để xem lịch | <code>đã uống thuốc</code> để xác nhận\n"
        f"⏰ <b>Deadline:</b> <code>deadline</code> / <code>bài tập</code>\n"
        f"🌸 <b>Chu kỳ sinh lý:</b> <code>chu kỳ</code> / <code>kỳ tới</code>\n"
        f"💖 <b>Báo đến kỳ:</b> <code>hôm nay đến kỳ</code>\n"
        f"📋 <b>Điểm danh:</b> <code>điểm danh</code> / <code>vắng mặt</code>\n"
        f"📊 <b>Trạng thái:</b> <code>status</code> / <code>tình trạng</code>\n\n"
        f"<i>Chúc {name} một ngày luôn rạng ngời và ngập tràn hạnh phúc! ✨</i>"
    )

# ======================= MESSAGE HANDLER =======================

def handle_incoming_message(msg: Dict[str, Any]):
    """
    Xử lý thông minh mọi tin nhắn người dùng gửi tới bot.
    Tuân thủ quy tắc bảo mật: Chỉ cho phép ALLOWED_CHAT_IDS tương tác.
    """
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    sender_id_str = str(chat_id).strip()

    settings = config.load_settings()
    her_id = str(config.HER_CHAT_ID or settings.get("telegram_her_chat_id", "")).strip()
    my_id = str(config.YOUR_CHAT_ID or settings.get("telegram_my_chat_id", "")).strip()
    allowed = [cid for cid in [her_id, my_id] if cid]

    # BẢO MẬT: Chỉ cho phép ID hợp lệ (nếu đã cấu hình)
    if allowed and sender_id_str not in allowed:
        try:
            print(f"[Bảo Mật] Bỏ qua tin nhắn từ Chat ID lạ: {sender_id_str} (Hợp lệ: {allowed})")
        except Exception:
            pass
        return

    text = (msg.get("text") or "").strip()
    if not text:
        return

    text_lower = text.lower()

    if sender_id_str == her_id:
        user_display = settings.get("her_name", "Em yêu 🌸")
    elif sender_id_str == my_id:
        user_display = settings.get("my_name", "Anh 💖")
    else:
        user_display = msg.get("from", {}).get("first_name", "Bạn")

    # 1. Báo bắt đầu kỳ mới
    period_keywords = ["đến kỳ", "den ky", "bắt đầu kỳ", "bat dau ky", "hôm nay bị", "hom nay bi", "có kinh", "co kinh"]
    if any(k in text_lower for k in period_keywords):
        reply = handle_log_period_start(user_display)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 2. Xác nhận đã uống thuốc
    taken_keywords = ["đã uống thuốc", "da uong thuoc", "uống thuốc rồi", "uong thuoc roi", "đã uống", "da uong", "uống rồi", "uong roi"]
    if any(text_lower == k or text_lower.startswith(k) for k in taken_keywords):
        reply = handle_take_medicine_command(user_display)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 3. Tra cứu lịch ngày mai
    tomorrow_keywords = ["mai học gì", "mai hoc gi", "ngày mai", "ngay mai", "lịch mai", "lich mai", "ngày mai học gì"]
    if any(k in text_lower for k in tomorrow_keywords):
        reply = build_schedule_response(for_tomorrow=True)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 4. Tra cứu lịch học hôm nay / cả tuần
    schedule_keywords = [
        "lịch học", "lich hoc", "thời khóa biểu", "thoi khoa bieu", "tkb",
        "môn học", "mon hoc", "học gì", "hoc gi", "lịch", "lich",
        "/lichhoc", "/schedule", "tuần này", "tuan nay"
    ]
    if any(k in text_lower for k in schedule_keywords):
        reply = build_schedule_response(for_tomorrow=False)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 5. Tra cứu lịch uống thuốc
    med_keywords = ["thuốc", "thuoc", "uống thuốc", "uong thuoc", "lich thuoc", "/thuoc"]
    if any(k in text_lower for k in med_keywords):
        reply = build_medicine_response()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 6. Tra cứu chu kỳ kinh nguyệt
    cycle_keywords = ["chu kỳ", "chu ky", "kỳ tới", "ky toi", "mấy ngày nữa", "may ngay nua", "pms", "đèn đỏ", "den do"]
    if any(k in text_lower for k in cycle_keywords):
        reply = build_cycle_response()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 7. Tra cứu deadline
    deadline_keywords = ["deadline", "bài tập", "bai tap", "nhiệm vụ", "nhiem vu", "/deadline", "nộp", "nop"]
    if any(k in text_lower for k in deadline_keywords):
        reply = build_deadline_response()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 8. Điểm danh
    attendance_keywords = ["điểm danh", "diem danh", "vắng mặt", "vang mat", "nghỉ học", "nghi hoc", "/diemdanh"]
    if any(k in text_lower for k in attendance_keywords):
        reply = build_attendance_response()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 9. Trạng thái hệ thống
    status_keywords = ["status", "tình trạng", "tinh trang", "trạng thái", "trang thai", "/status", "hệ thống", "he thong"]
    if any(k in text_lower for k in status_keywords):
        reply = build_status_response()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 10. /start, /help, câu chào
    greeting_keywords = ["/start", "/help", "help", "chào", "chao", "hi", "hello", "xin chào"]
    if any(text_lower.startswith(k) or text_lower == k for k in greeting_keywords):
        reply = build_help_response(user_display)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 11. Default: gợi ý nhẹ nhàng
    default_reply = (
        f"Dạ em đây! 🌸 Em chưa hiểu yêu cầu <i>\"{text}\"</i> của {user_display}.\n\n"
        f"👉 Nhắn <code>help</code> để xem tất cả lệnh em hỗ trợ nhé! 💖"
    )
    notifier.send_telegram_message(chat_id, default_reply)

# ======================= POLLING LOOP =======================

def lang_nghe_tin_nhan():
    """
    Vòng lặp Long Polling nhận tin nhắn từ Telegram Bot 24/7.
    Resilient Loop: tự phục hồi khi mất mạng, không bao giờ crash.
    """
    global _LISTENER_RUNNING
    _LISTENER_RUNNING = True
    try:
        print("[Bot Interactive] Bắt đầu lắng nghe tin nhắn Telegram (Long Polling 24/7)...")
    except Exception:
        pass

    offset = None
    consecutive_errors = 0

    while _LISTENER_RUNNING:
        try:
            token = (config.TELEGRAM_BOT_TOKEN or config.load_settings().get("telegram_bot_token", "")).strip()
            if not token:
                time.sleep(3)
                continue

            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 20}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(url, params=params, timeout=25)
            consecutive_errors = 0  # Reset khi thành công

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        if "message" in update:
                            try:
                                handle_incoming_message(update["message"])
                            except Exception as handle_err:
                                try:
                                    print(f"[Bot Interactive] Lỗi xử lý tin nhắn: {handle_err}")
                                except Exception:
                                    pass
            elif resp.status_code == 409:
                try:
                    print("[Bot Interactive] Conflict 409 – Bot đang chạy ở nơi khác, chờ 5s...")
                except Exception:
                    pass
                time.sleep(5)
            else:
                try:
                    print(f"[Bot Interactive] HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception:
                    pass
                time.sleep(3)

        except (requests.ConnectionError, requests.Timeout):
            consecutive_errors += 1
            wait_time = min(15, 2 * consecutive_errors)
            time.sleep(wait_time)
        except Exception as e:
            try:
                print(f"[Bot Interactive] Ngoại lệ polling: {e}")
            except Exception:
                pass
            consecutive_errors += 1
            time.sleep(3)

    try:
        print("[Bot Interactive] Đã dừng lắng nghe Telegram.")
    except Exception:
        pass


_LISTENER_LOCK = threading.Lock()

def start_telegram_listener():
    """Khởi động luồng lắng nghe tin nhắn Telegram nếu chưa chạy (Singleton Thread-Safe)."""
    global _LISTENER_RUNNING, _LISTENER_THREAD
    with _LISTENER_LOCK:
        if _LISTENER_RUNNING and _LISTENER_THREAD and _LISTENER_THREAD.is_alive():
            return

        _LISTENER_RUNNING = True
        _LISTENER_THREAD = threading.Thread(target=lang_nghe_tin_nhan, daemon=True, name="BotInteractiveListener")
        _LISTENER_THREAD.start()


def stop_telegram_listener():
    """Dừng luồng lắng nghe an toàn."""
    global _LISTENER_RUNNING
    _LISTENER_RUNNING = False
