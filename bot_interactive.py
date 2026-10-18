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

# ======================= MOOD TRACKER DATA =======================

_USER_MOOD_SESSIONS: Dict[str, Dict[str, Any]] = {}

MOOD_MAP = {
    "Happy": {"name": "Vui vẻ 😄", "icon": "😄"},
    "Sad": {"name": "Buồn 😔", "icon": "😔"},
    "Stressed": {"name": "Stress 😫", "icon": "😫"},
    "Angry": {"name": "Bực bội 😡", "icon": "😡"},
    "Tired": {"name": "Mệt mỏi 😴", "icon": "😴"},
}

MOOD_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "😄 Vui vẻ", "callback_data": "mood_Happy"},
            {"text": "😔 Buồn", "callback_data": "mood_Sad"}
        ],
        [
            {"text": "😫 Stress", "callback_data": "mood_Stressed"},
            {"text": "😡 Bực bội", "callback_data": "mood_Angry"}
        ],
        [
            {"text": "😴 Mệt mỏi", "callback_data": "mood_Tired"}
        ]
    ]
}

AI_RESPONSES = {
    "Happy": "Tuyệt vời quá! Chúc em bé luôn giữ nụ cười tươi tắn này nhé! 🥰",
    "Sad": "Thương em lắm! Đừng buồn nhé, có anh và Bác sĩ Mèo luôn ở bên em này! Nghỉ ngơi một chút và uống nước ấm nha em! 💖",
    "Stressed": "Thương em lắm! Đừng quá sức nhé, nghỉ ngơi một chút và uống nước ấm nha em! 💖",
    "Angry": "Thương em lắm! Hít thở thật sâu một chút nhé em bé, đừng để chuyện bực mình làm ảnh hưởng đến sức khỏe nha! 💖",
    "Tired": "Thương em nhiều! Đừng làm việc quá sức nha, nghỉ ngơi một chút và uống nước ấm nhé em! 🍵💤💖",
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
    """Tạo tin nhắn tra cứu deadline sắp tới kèm số thứ tự để đánh dấu hoàn thành."""
    tasks = database.get_all_tasks()
    active_tasks = [t for t in tasks if t.get("status") != "Đã hoàn thành"]

    lines = ["⏰ <b>DANH SÁCH DEADLINE & BÀI TẬP CẦN LÀM</b> 🌸\n"]
    if not active_tasks:
        lines.append("<i>🎉 Tuyệt vời! Hiện tại không có deadline nào đang chờ. Em thật giỏi! 💖</i>")
    else:
        now = config.get_now()
        for idx, t in enumerate(active_tasks, 1):
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
                f"<b>[{idx}]</b> <b>{t['task_name']}</b> ({t['subject_name']})\n"
                f"   📅 Hạn: <b>{t['deadline']}</b>{urgency} | Trạng thái: {stt}"
            )
        lines.append(
            "\n💡 <b>Cách đánh dấu hoàn thành:</b>\n"
            "• Xong 1 task: Nhắn <code>xong task 1</code> hoặc <code>done task 1</code>\n"
            "• Xong nhiều task: Nhắn <code>xong task 1, 3</code> hoặc <code>done task 1, 3</code>"
        )
    return "\n".join(lines)


def handle_complete_deadline_command(text: str, user_display: str) -> str:
    """Đánh dấu hoàn thành một hoặc nhiều deadline cùng lúc qua tin nhắn Telegram."""
    import re

    all_tasks = database.get_all_tasks()
    active_tasks = [t for t in all_tasks if t.get("status") != "Đã hoàn thành"]

    if not active_tasks:
        return (
            f"🎉 <b>HOÀN THÀNH SẠCH SẼ!</b> 💖\n\n"
            f"Tuyệt vời quá {user_display} ơi! Hiện tại không có deadline nào đang chờ cả, "
            f"em đã dọn dẹp sạch sẽ bài tập rồi! Tận hưởng thời gian nghỉ ngơi xả hơi thôi nào! 🏖️✨"
        )

    text_lower = text.lower()
    matched_tasks = []

    # 1. Trích xuất tất cả các số thứ tự (ví dụ: 'task 1', '1, 3', 'task 1,3', 'done 1 2')
    found_nums = [int(n) for n in re.findall(r'\b\d+\b', text)]
    valid_indices = []
    for n in found_nums:
        if 1 <= n <= len(active_tasks):
            idx = n - 1
            if idx not in valid_indices:
                valid_indices.append(idx)

    if valid_indices:
        matched_tasks = [active_tasks[i] for i in valid_indices]
    elif found_nums and not valid_indices:
        return (
            f"⚠️ <b>Không tìm thấy task số {found_nums[0]}!</b>\n\n"
            f"Hiện tại chỉ có từ <b>task 1 đến task {len(active_tasks)}</b>. "
            f"Nhắn <code>deadline</code> để xem lại danh sách bài tập nhé! 🌸"
        )

    # 2. Khớp theo từ khóa tên bài tập (nếu không ghi số, ví dụ: 'xong slide', 'done reflection')
    if not matched_tasks:
        for t in active_tasks:
            t_name = t["task_name"].lower()
            keywords_in_name = [w for w in re.split(r'[\s\(\)\-_,]+', t_name) if len(w) >= 3]
            if any(k in text_lower for k in keywords_in_name):
                matched_tasks.append(t)
                break

    # 3. Mặc định: nếu chỉ nhắn 'xong deadline' hoặc 'done task' mà không ghi số:
    if not matched_tasks:
        matched_tasks = [active_tasks[0]]

    # Cập nhật trạng thái trong database sang Đã hoàn thành
    for t in matched_tasks:
        database.update_task_status(t["id"], "Đã hoàn thành")

    # Kiểm tra các task còn lại sau khi hoàn thành
    matched_ids = {t["id"] for t in matched_tasks}
    remaining_tasks = [t for t in active_tasks if t["id"] not in matched_ids]

    # Tạo nội dung danh sách task vừa hoàn thành
    task_bullets = []
    for t in matched_tasks:
        original_idx = active_tasks.index(t) + 1
        task_bullets.append(f"• <b>[{original_idx}] {t['task_name']}</b> ({t.get('subject_name', 'Môn học')}) ✅")
    task_done_str = "\n".join(task_bullets)

    if len(matched_tasks) > 1:
        header_title = (
            f"🎉 <b>QUÁ ĐỈNH {user_display.upper()} ƠI! MỘT CÔNG ĐÔI VIỆC!</b> ✨\n\n"
            f"Em đã hoàn thành xuất sắc <b>{len(matched_tasks)} bài tập</b> cùng lúc:\n{task_done_str}"
        )
    else:
        header_title = (
            f"🎉 <b>XUẤT SẮC QUÁ {user_display.upper()} ƠI!</b> ✨\n\n"
            f"Em đã đánh dấu hoàn thành bài tập:\n{task_done_str}"
        )

    if remaining_tasks:
        rem_bullets = []
        for new_idx, r in enumerate(remaining_tasks, 1):
            rem_bullets.append(f"• <b>[{new_idx}] {r['task_name']}</b> (Hạn: {r['deadline']})")
        rem_str = "\n".join(rem_bullets)
        rem_info = f"\n\n📝 <b>Hiện em còn {len(remaining_tasks)} bài tập nữa nè:</b>\n{rem_str}\n\nCố lên nhé em bé! Anh luôn cổ vũ em! 💪🌸"
    else:
        rem_info = f"\n\n🎊 <b>WOAHH! Em đã dọn sạch TẤT CẢ deadline rồi!</b> Thật tự hào về em! Nghỉ ngơi cho khỏe nhé cô bé siêu giỏi giang! 🍵🧸💖"

    return f"{header_title}{rem_info}"


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
        f"⏰ <b>Deadline:</b> <code>deadline</code> để xem | <code>xong task 1</code> hoặc <code>done task 1, 3</code> để hoàn thành\n"
        f"🌸 <b>Chu kỳ sinh lý:</b> <code>chu kỳ</code> / <code>kỳ tới</code>\n"
        f"💖 <b>Báo đến kỳ:</b> <code>hôm nay đến kỳ</code>\n"
        f"🐱 <b>Cảm xúc hôm nay:</b> <code>cảm xúc</code> / <code>mood</code>\n"
        f"☀️ <b>Chào buổi sáng:</b> <code>chào buổi sáng</code>\n"
        f"🌙 <b>Chúc ngủ ngon:</b> <code>chúc ngủ ngon</code> (tâm sự theo cảm xúc hôm nay)\n"
        f"📋 <b>Điểm danh:</b> <code>điểm danh</code> / <code>vắng mặt</code>\n"
        f"📊 <b>Trạng thái:</b> <code>status</code> / <code>tình trạng</code>\n\n"
        f"<i>Chúc {name} một ngày luôn rạng ngời và ngập tràn hạnh phúc! ✨</i>"
    )

# ======================= CALLBACK QUERY & MESSAGE HANDLER =======================

def handle_incoming_callback_query(cq: Dict[str, Any]):
    """Xử lý sự kiện bấm nút Inline Keyboard từ Telegram."""
    cq_id = cq.get("id")
    from_user = cq.get("from", {})
    user_id = str(from_user.get("id") or "").strip()
    data = cq.get("data", "")
    message = cq.get("message", {})
    chat_id = message.get("chat", {}).get("id") or user_id

    # Acknowledge callback query để tắt vòng quay trên Telegram client
    token = (config.TELEGRAM_BOT_TOKEN or config.load_settings().get("telegram_bot_token", "")).strip()
    if token and cq_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                json={"callback_query_id": cq_id},
                timeout=5
            )
        except Exception:
            pass

    if data.startswith("mood_"):
        mood_type = data.replace("mood_", "")
        _USER_MOOD_SESSIONS[user_id] = {
            "mood": mood_type,
            "chat_id": chat_id,
            "time": time.time()
        }
        mood_info = MOOD_MAP.get(mood_type, {"name": mood_type, "icon": "🌸"})
        prompt = (
            f"Bác sĩ Mèo đã ghi nhận em đang <b>{mood_info['name']}</b>! 🌸\n\n"
            f"Em có muốn nhắn thêm điều gì đã xảy ra hôm nay không?\n"
            f"👉 <i>(Gõ nội dung ghi chú, hoặc gõ <code>Không</code> để bỏ qua nhé!)</i>"
        )
        notifier.send_telegram_message(chat_id, prompt)


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
        user_display = config.HER_NAME or settings.get("her_name", "Em bé 🌸")
    elif sender_id_str == my_id:
        user_display = config.MY_NAME or settings.get("my_name", "Dawn 💫")
    else:
        user_display = msg.get("from", {}).get("first_name", "Bạn")

    # 0. Kiểm tra phiên nhập ghi chú cảm xúc (Mood Tracker)
    if sender_id_str in _USER_MOOD_SESSIONS:
        session = _USER_MOOD_SESSIONS.pop(sender_id_str)
        if time.time() - session.get("time", 0) <= 600:
            mood_type = session.get("mood", "Happy")
            mood_info = MOOD_MAP.get(mood_type, {"name": mood_type, "icon": "🌸"})
            note_raw = text.strip()
            if note_raw.lower() in ["không", "khong", "k", "ko", "no", "skip"]:
                note = None
            else:
                note = note_raw

            ai_response = AI_RESPONSES.get(mood_type, "Thương em nhiều! Luôn giữ gìn sức khỏe nhé! 💖")
            today_str = config.get_now().strftime("%Y-%m-%d")

            try:
                database.add_mood_log(today_str, mood_type, note, ai_response)
            except Exception as e:
                print(f"[Mood Tracker] Lỗi lưu DB: {e}")

            note_str = f"\n📝 <i>Ghi chú: \"{note}\"</i>" if note else ""
            reply_msg = (
                f"🐱 <b>BÁC SĨ MÈO ĐÃ LẮNG NGHE!</b> 🌸\n\n"
                f"Tâm trạng hôm nay: <b>{mood_info['name']}</b>{note_str}\n\n"
                f"{ai_response}"
            )
            notifier.send_telegram_message(chat_id, reply_msg)

            # Cảnh báo bí mật cho bạn trai nếu tâm trạng tiêu cực - chỉ khi cô ấy ghi, không phải Anh
            if mood_type in ["Sad", "Stressed", "Angry", "Tired"] and sender_id_str == her_id:
                try:
                    note_content = note if note else "Không có ghi chú"
                    secret_msg = (
                        f"🤫 <b>[CẢNH BÁO TÂM LÝ BÍ MẬT]</b>\n\n"
                        f"Em bé vừa cập nhật cảm xúc: <b>{mood_info['name']}</b> qua Telegram.\n"
                        f"📝 <b>Ghi chú:</b> {note_content}\n\n"
                        f"👉 <i>Hãy nhắn tin hỏi thăm và chuẩn bị món gì đó ngon hoặc đồ ngọt cho cô ấy nhé! 🍫🧸💖</i>"
                    )
                    notifier.notify_you_secret(secret_msg)
                except Exception as notify_err:
                    print(f"[Mood Tracker] Lỗi gửi cảnh báo bí mật: {notify_err}")
            return

    # 0.5 Bắt từ khóa cập nhật cảm xúc (Mood Tracker)
    mood_keywords = ["cảm xúc", "cảm xúc hôm nay", "cập nhật cảm xúc", "mood", "tâm trạng", "tam trang"]
    if any(k in text_lower for k in mood_keywords):
        # Chỉ cho phép cô ấy dùng Mood Tracker; Anh không cần ghi nhận cảm xúc
        if sender_id_str != her_id and my_id:
            notifier.send_telegram_message(chat_id, "💡 Tính năng ghi nhận cảm xúc chỉ dành cho em bé thôi nha! 🌸")
            return
        prompt = (
            "🌸 <b>NHẬT KÝ CẢM XÚC HÔM NAY</b> 🐱\n\n"
            "Bác sĩ Mèo đang lắng nghe em nè! Hôm nay tâm trạng của em thế nào?\n"
            "<i>Bấm vào một nút bên dưới để chia sẻ với em nhé:</i>"
        )
        notifier.send_telegram_message(chat_id, prompt, reply_markup=MOOD_KEYBOARD)
        return

    # 0.6 Lời chúc ngủ ngon (Cá nhân hóa theo cảm xúc hôm nay)
    night_keywords = [
        "chúc ngủ ngon", "chuc ngu ngon", "ngủ ngon", "ngu ngon",
        "ngủ thôi", "ngu thoi", "đi ngủ đây", "di ngu day", "đi ngủ", "di ngu",
        "good night", "g9", "/chucngon", "ngủ đây", "ngu day"
    ]
    if any(k in text_lower for k in night_keywords):
        import scheduler
        if sender_id_str == her_id:
            # Gửi tin chúc ngủ ngon cá nhân hóa cho cô ấy
            reply = scheduler.build_good_night_message()
        else:
            # Anh nhắn: chỉ báo preview ngắn
            reply = "🌙 <b>Xem trước tin nhắn ngủ ngon sẽ gửi cho em bé tối nay...</b>\n\n" + scheduler.build_good_night_message()
        notifier.send_telegram_message(chat_id, reply)
        return

    # 0.7 Lời chào buổi sáng
    morning_keywords = [
        "chào buổi sáng", "chao buoi sang", "buổi sáng tốt lành",
        "buoi sang tot lanh", "good morning", "/buoisang", "/morning"
    ]
    if any(k in text_lower for k in morning_keywords):
        import scheduler
        if sender_id_str == her_id:
            # Gửi tin chào sáng cá nhân hóa cho cô ấy
            reply = scheduler.build_good_morning_message()
        else:
            # Anh nhắn: chỉ báo preview ngắn
            reply = "☀️ <b>Xem trước tin nhắn chào buổi sáng sẽ gửi cho em bé...</b>\n\n" + scheduler.build_good_morning_message()
        notifier.send_telegram_message(chat_id, reply)
        return

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

    # 7. Đánh dấu hoàn thành deadline (hỗ trợ: xong task 1, done task 1, hoàn thành task 1, 3, done 1, 3, v.v.)
    import re
    complete_deadline_prefixes = [
        "xong task", "done task", "hoàn thành task", "hoan thanh task",
        "xong deadline", "done deadline", "hoàn thành deadline", "hoan thanh deadline",
        "xong bài tập", "done bài tập", "hoàn thành bài tập", "hoan thanh bài tập",
        "đã xong task", "da xong task", "đã hoàn thành", "da hoan thanh",
        "xong hết bài", "làm xong deadline", "đã làm xong", "xong rồi", "xong rùi", "done all"
    ]
    is_complete_cmd = any(p in text_lower for p in complete_deadline_prefixes)
    if not is_complete_cmd:
        # Nhận diện cú pháp: 'done 1', 'xong 1, 3', 'done 1,3', 'hoàn thành 1, 3', 'done task 1, 3'
        if re.search(r'\b(xong|done|hoàn thành|hoan thanh)\b.*(\btask\b|\bdeadline\b|\d+)', text_lower):
            is_complete_cmd = True

    if is_complete_cmd:
        reply = handle_complete_deadline_command(text, user_display)
        notifier.send_telegram_message(chat_id, reply)
        return

    # 8. Tra cứu deadline
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
                        elif "callback_query" in update:
                            try:
                                handle_incoming_callback_query(update["callback_query"])
                            except Exception as cb_err:
                                try:
                                    print(f"[Bot Interactive] Lỗi xử lý callback query: {cb_err}")
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
