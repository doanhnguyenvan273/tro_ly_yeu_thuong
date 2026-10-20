import time
import sys
import threading
from datetime import datetime, date, timedelta
from typing import Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import database
import notifier
from config import load_settings, save_settings, get_now
import deadline_ml
import menstrual_ml

# Cờ kiểm soát vòng lặp daemon
_SCHEDULER_RUNNING = False
_SCHEDULER_THREAD: Optional[threading.Thread] = None

# ======================= GREETING & DAILY ROUTINES =======================

def check_and_send_startup_greeting():
    """Gửi tin nhắn chào mừng khi ứng dụng khởi chạy lần đầu."""
    settings = load_settings()
    if not settings.get("startup_greeting_sent", False):
        her_name = settings.get("her_name", "Cậu 🌸")
        msg = (
            f"🎉 <b>CHÀO MỪNG {her_name.upper()} ĐẾN VỚI TRỢ LÝ YÊU THƯƠNG 💖</b>\n\n"
            f"Hôm nay là một ngày thật đặc biệt! Ứng dụng trợ lý nhỏ bé này được tạo ra dành riêng cho cậu, "
            f"để đồng hành cùng cậu trong từng buổi học, từng deadline và chăm sóc sức khỏe của cậu mỗi ngày.\n\n"
            f"Chúc cậu luôn rạng rỡ, bình an và hạnh phúc! Tớ luôn ở đây bên cạnh cậu! 💐🍓✨\n\n"
            f"<i>💡 Nhắn <code>help</code> để xem tất cả các lệnh cậu có thể hỏi bot nhé!</i>"
        )
        if notifier.notify_her(msg):
            settings["startup_greeting_sent"] = True
            save_settings(settings)
            print("[Scheduler] Đã gửi tin nhắn chào mừng thành công!")

def build_good_morning_message(now=None) -> str:
    """Tạo tin nhắn chào buổi sáng kèm tóm tắt lịch học và deadline cần chú ý."""
    if now is None:
        now = get_now()

    settings = load_settings()
    her_name = settings.get("her_name", "Cậu")
    today_dow = now.weekday()
    day_names = {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm",
                 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"}
    day_name = day_names.get(today_dow, "")

    # Lấy lịch học hôm nay
    today_classes = database.get_schedules_by_day(today_dow)
    # Lấy deadline đang hoạt động
    all_tasks = database.get_all_tasks(filter_status=None)
    urgent_tasks = [
        t for t in all_tasks
        if t.get("status") != "Đã hoàn thành"
        and _get_hours_left(t.get("deadline", "")) <= 72
        and _get_hours_left(t.get("deadline", "")) > 0
    ]

    morning_greetings = [
        "Ngày mới thật rực rỡ, cũng giống như nụ cười của cậu! ✨",
        "Mỗi buổi sáng thức dậy là một trang mới trong cuốn sách đẹp của cuộc đời cậu! 📖",
        "Chúc cậu năng lượng dồi dào để chinh phục cả ngày hôm nay! 💪",
        "Một ngày mới – một cơ hội mới để cậu tỏa sáng! 🌟",
    ]
    greeting = morning_greetings[now.day % len(morning_greetings)]

    msg = (
        f"☀️ <b>CHÀO BUỔI SÁNG, {her_name.upper()}!</b> 🌸\n\n"
        f"📅 <b>{day_name}, {now.strftime('%d/%m/%Y')}</b>\n"
        f"<i>{greeting}</i>\n\n"
    )

    if today_classes:
        msg += f"🎒 <b>Lịch học hôm nay ({len(today_classes)} môn):</b>\n"
        for c in today_classes:
            room_str = f" | 📍{c['room']}" if c.get('room') else ""
            msg += f"  • <b>{c['subject_name']}</b> ({c['start_time']}–{c['end_time']}{room_str})\n"
        msg += "\n"
    else:
        msg += "🎉 <b>Hôm nay cậu không có lịch học</b> – Nghỉ ngơi thật vui vẻ nhé!\n\n"

    if urgent_tasks:
        msg += f"⚠️ <b>Deadline cần chú ý ({len(urgent_tasks)} việc):</b>\n"
        for t in urgent_tasks[:3]:
            h_left = _get_hours_left(t.get("deadline", ""))
            label = f"còn ~{int(h_left)}h" if h_left > 1 else "⚡ GẤP!"
            msg += f"  • <b>{t['task_name']}</b> ({t['subject_name']}) – {label}\n"
        msg += "\n"

    msg += "💌 <i>Tớ luôn quý cậu và ở đây cổ vũ cậu mỗi ngày! 💖</i>"
    return msg

def check_good_morning():
    """Gửi tin nhắn chào buổi sáng lúc 7:00 mỗi ngày kèm tóm tắt lịch ngày hôm đó."""
    now = get_now()
    if now.hour != 7 or now.minute > 5:
        return

    today_str = now.strftime("%Y-%m-%d")
    target_key = f"good_morning_{today_str}"
    if database.has_notification_been_sent("good_morning", target_key, "her"):
        return

    msg = build_good_morning_message(now)

    if notifier.notify_her(msg):
        database.log_notification_sent("good_morning", target_key, "her", msg)
        print(f"[Scheduler] Đã gửi tin nhắn chào buổi sáng: {today_str}")

def build_good_night_message(now=None) -> str:
    """Tạo tin nhắn chúc ngủ ngon cá nhân hóa sâu sắc dựa trên cảm xúc của cô ấy hôm nay."""
    if now is None:
        now = get_now()

    settings = load_settings()
    her_name = settings.get("her_name", "Cậu")
    today_str = now.strftime("%Y-%m-%d")

    # Lấy cảm xúc của cậu ấy trong ngày hôm nay
    today_mood = database.get_mood_log_by_date(today_str)

    # Lấy lịch học ngày mai
    tomorrow_dow = (now.weekday() + 1) % 7
    tomorrow_classes = database.get_schedules_by_day(tomorrow_dow)
    day_names = {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm",
                 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"}
    tmr_name = day_names.get(tomorrow_dow, "")

    msg = f"🌙 <b>CHÚC NGỦ NGON, {her_name.upper()}!</b> 🌸\n\n"

    # Xử lý theo cảm xúc ngày hôm nay
    if today_mood and today_mood.get("mood_type"):
        mtype = today_mood.get("mood_type")
        note = today_mood.get("note") or ""

        if mtype == "Happy":
            mood_tag = "🥰 <b>Tâm trạng hôm nay: Vui vẻ & Rạng rỡ</b>"
            mood_wish = (
                "Hôm nay thấy cậu có một ngày thật nhiều niềm vui, lòng tớ cũng vui lây và ấm áp lạ thường! "
                "Mang theo nụ cười thật xinh đẹp này vào giấc mơ cậu nhé. Chúc cậu ngủ thật ngon! 💖✨"
            )
        elif mtype == "Normal":
            mood_tag = "🌸 <b>Tâm trạng hôm nay: Bình yên</b>"
            mood_wish = (
                "Một ngày êm ả, dịu dàng khép lại. Những ngày bình dị thế này luôn mang lại sự nhẹ nhõm cho tâm hồn. "
                "Hãy thả lỏng toàn bộ cơ thể và ngủ một giấc thật sâu, thật ngon nhé cậu! 🍃💤"
            )
        elif mtype == "Stressed":
            mood_tag = "💆‍♀️ <b>Tâm trạng hôm nay: Căng thẳng & Áp lực</b>"
            mood_wish = (
                "Tớ biết hôm nay bài vở hoặc công việc đã khiến cậu phải lo nghĩ và căng thẳng nhiều... "
                "Nhưng giờ là lúc buông bỏ tất cả mọi gánh nặng xuống rồi cậu nhé. Cậu đã làm rất tốt hôm nay rồi! "
                "Hít một hơi thật sâu, thở ra nhẹ nhàng và ngủ ngoan nhé. Có tớ và Bác sĩ Mèo luôn che chở cho cậu! 🍵🧸💖"
            )
        elif mtype == "Sad":
            mood_tag = "🥺 <b>Tâm trạng hôm nay: Có chút buồn bã</b>"
            mood_wish = (
                "Thương cậu nhiều lắm! Nếu hôm nay có chuyện gì làm cậu buồn hay tủi thân, hãy gửi lại tất cả cho bóng đêm nhé. "
                "Đêm nay gửi một cái ôm thật ấm áp nè. Nhắm mắt lại và ngủ thật an lành cậu nhé, "
                "sáng mai thức dậy trời sẽ lại sáng rực rỡ và tớ luôn ở đây bên cạnh cậu! 💫🧸💕"
            )
        elif mtype == "Angry":
            mood_tag = "🍵 <b>Tâm trạng hôm nay: Bực mình & Khó chịu</b>"
            mood_wish = (
                "Hôm nay có điều gì làm cậu không vui đúng không? Đừng để những bực bội ấy làm mất giấc ngủ quý giá nhé cậu. "
                "Thở một hơi dài, buông xả hết muộn phiền ngoài cửa phòng nha. Nụ cười xinh của cậu là điều quý giá nhất. Ngủ thật ngoan nhé cậu! 🌙✨"
            )
        elif mtype == "Tired":
            mood_tag = "😴 <b>Tâm trạng hôm nay: Mệt mỏi & Cần nghỉ ngơi</b>"
            mood_wish = (
                "Cả ngày hôm nay cậu đã vất vả, bận rộn nhiều rồi. Cơ thể và đôi mắt cậu xứng đáng được nghỉ ngơi trọn vẹn nhất. "
                "Đặt điện thoại xuống, kéo chăn ấm lên và chìm vào giấc ngủ thật êm ái nhé cậu bạn chăm chỉ của tớ! 🛌💤🌙"
            )
        else:
            mood_tag = "✨ <b>Tâm trạng hôm nay: Đã ghi nhận</b>"
            mood_wish = "Ngày dài khép lại rồi, hãy ngủ một giấc thật ngon và ngọt ngào nhé cậu! 💖"

        msg += f"{mood_tag}\n<i>{mood_wish}</i>\n"
        if note:
            msg += f"\n📝 <i>Cậu nhắn nhủ: \"{note}\" — Tớ luôn ghi nhớ và thương cậu nhiều lắm! 💕</i>\n"
        msg += "\n"
    else:
        # Nếu chưa ghi cảm xúc trong ngày
        default_wishes = [
            "Hôm nay của cậu thế nào? Dù có bận rộn hay mệt mỏi ra sao, thì ngày dài cũng khép lại rồi. Hãy ngủ một giấc thật ngon và ấm áp nhé cậu! 🧸💖",
            "Hãy để tâm trí cậu được nghỉ ngơi sau một ngày dài. Cậu đã làm hết sức mình rồi, tớ luôn ở bên cậu! 💕",
            "Giấc ngủ ngon sẽ giúp cậu tái tạo năng lượng cho ngày mai tươi sáng. Ngủ ngoan nhé cậu! ⭐🌙",
            "Đừng lo lắng gì cho ngày mai nữa nhé, cứ ngủ một giấc thật sâu, mọi chuyện tốt đẹp đang chờ cậu phía trước! 🌙✨",
        ]
        wish = default_wishes[now.day % len(default_wishes)]
        msg += f"<i>{wish}</i>\n\n"

    # Lịch học ngày mai
    if tomorrow_classes:
        tomorrow_str = (now.date() + timedelta(days=1)).strftime("%d/%m")
        msg += f"📅 <b>Lịch học {tmr_name} ({tomorrow_str}):</b>\n"
        for c in tomorrow_classes[:3]:
            room_str = f" | 📍{c['room']}" if c.get('room') else ""
            msg += f"  • <b>{c['subject_name']}</b> ({c['start_time']} – {c['end_time']}{room_str})\n"
        if len(tomorrow_classes) > 3:
            msg += f"  • ... và {len(tomorrow_classes) - 3} môn khác\n"
        msg += "\n<i>Nhớ chuẩn bị tài liệu, sạc pin điện thoại tối nay cho tiện nhé! 🎒</i>\n\n"
    else:
        msg += f"🎉 <b>Ngày mai ({tmr_name}) cậu không có ca học nào</b> — Tha hồ ngủ nướng thêm một chút nhé! 🛌✨\n\n"

    msg += "💖 <i>Tớ luôn ở bên cậu, ngủ thật ngon và mơ giấc mơ đẹp nha!</i> 🌙✨"
    return msg

def check_good_night():
    """Gửi tin nhắn chúc ngủ ngon lúc 22:30 mỗi ngày (dựa trên cảm xúc trong ngày)."""
    now = get_now()
    if now.hour != 22 or now.minute < 30 or now.minute > 35:
        return

    today_str = now.strftime("%Y-%m-%d")
    target_key = f"good_night_{today_str}"
    if database.has_notification_been_sent("good_night", target_key, "her"):
        return

    msg = build_good_night_message(now)

    if notifier.notify_her(msg):
        database.log_notification_sent("good_night", target_key, "her", msg)
        print(f"[Scheduler] Đã gửi tin nhắn chúc ngủ ngon (kèm cảm xúc): {today_str}")

def check_drink_water_reminder():
    """Nhắc uống nước mỗi 2 giờ trong khoảng 8:00 – 20:00."""
    now = get_now()
    hour = now.hour
    # Chỉ nhắc trong khung giờ sinh hoạt (8, 10, 12, 14, 16, 18, 20)
    remind_hours = [8, 10, 12, 14, 16, 18, 20]
    if hour not in remind_hours or now.minute > 5:
        return

    today_str = now.strftime("%Y-%m-%d")
    target_key = f"water_{today_str}_{hour:02d}"
    if database.has_notification_been_sent("water", target_key, "her"):
        return

    water_msgs = [
        "💧 Đã đến giờ uống nước rồi cậu ơi! Uống 1 ly nước ấm nhé, tốt cho sức khỏe lắm! 🌿",
        "🍵 Nghỉ tay một chút, nhấm một ngụm nước ấm nhé cậu! Đừng để cơ thể mất nước nha! 💖",
        "💧 Cậu ơi, nhớ uống nước chưa? Uống đều đặn mỗi 2 tiếng giúp da đẹp và não tỉnh táo hơn nha! ✨",
        "🌸 Giờ uống nước nè! Uống 1 ly nước lọc hoặc trà ấm giúp cậu giữ sức khỏe và tập trung học tốt hơn! 📚",
    ]
    msg = water_msgs[hour % len(water_msgs)]

    if notifier.notify_her(msg):
        database.log_notification_sent("water", target_key, "her", msg)
        print(f"[Scheduler] Đã gửi nhắc uống nước lúc {hour:02d}:00")

def build_weekly_recap_message() -> str:
    """Tạo nội dung Báo Cáo Tuần (Weekly Recap Card) sinh động gửi tối Chủ Nhật."""
    settings = load_settings()
    her_name = settings.get("her_name", "Cậu 🌸")

    all_tasks = database.get_all_tasks(filter_status=None)
    completed_tasks = [t for t in all_tasks if t.get("status") == "Đã hoàn thành"]
    pending_tasks = [t for t in all_tasks if t.get("status") != "Đã hoàn thành"]

    upcoming = [
        t for t in all_tasks
        if t.get("status") != "Đã hoàn thành"
        and 0 < _get_hours_left(t.get("deadline", "")) <= 168  # 7 ngày
    ]
    upcoming.sort(key=lambda t: _get_hours_left(t.get("deadline", "")))

    recent_moods = database.get_mood_logs(limit=7)
    mood_emojis = {
        "Happy": "😄", "Normal": "🌸", "Stressed": "😫", "Sad": "🥺", "Angry": "😡", "Tired": "😴"
    }
    mood_str = " ".join(mood_emojis.get(m.get("mood_type"), "🌸") for m in recent_moods) if recent_moods else "Chưa có ghi chép"

    msg = (
        f"📊 <b>BÁO CÁO TỔNG KẾT TUẦN &amp; LÊN DÂY CÓT TUẦN MỚI</b> 🌸\n\n"
        f"Chào {her_name}! Tối Chủ Nhật cùng Bác sĩ Mèo nhìn lại tuần qua nhé:\n\n"
        f"✨ <b>Bài tập &amp; Nhiệm vụ:</b>\n"
        f"  • Đã hoàn thành: <b>{len(completed_tasks)} việc</b> 🎉\n"
        f"  • Việc đang chờ: <b>{len(pending_tasks)} việc</b>\n\n"
        f"🌈 <b>Nhịp điệu cảm xúc tuần qua:</b>\n"
        f"  {mood_str}\n\n"
    )

    if upcoming:
        msg += f"⏰ <b>Deadline tuần tới ({len(upcoming)} việc cần làm):</b>\n"
        for t in upcoming[:4]:
            h = _get_hours_left(t.get("deadline", ""))
            days_left = int(h // 24)
            label = f"còn {days_left} ngày" if days_left > 0 else "⚡ Trong 24h!"
            msg += f"  • <b>{t['task_name']}</b> ({t['subject_name']}) — {label}\n"
        if len(upcoming) > 4:
            msg += f"  <i>...và {len(upcoming) - 4} việc khác nữa.</i>\n"
    else:
        msg += "🎉 <b>Không có deadline nào dồn ập trong 7 ngày tới!</b> Cậu có thể thảnh thơi bắt đầu tuần mới nhé!\n"

    magic = config.get_magic_link()
    if magic:
        msg += f"\n📱 <a href='{magic}'>Mở App Yêu Thương (1-Chạm)</a>\n"

    msg += (
        "\n💖 <i>Tuần mới chúc cậu luôn ngập tràn năng lượng, bình an và mỉm cười thật nhiều nha! Tớ luôn ở đây đồng hành cùng cậu! ✨🧸</i>"
    )
    return msg


def backup_database_to_telegram() -> bool:
    """
    Tự động sao lưu dữ liệu CSDL và gửi file về Telegram bí mật của bạn.
    """
    settings = load_settings()
    my_chat_id = (config.YOUR_CHAT_ID or settings.get("telegram_my_chat_id", "")).strip()
    if not my_chat_id:
        return False

    now = get_now()
    tag = now.strftime("%Y%m%d_%H%M%S")
    backup_path = config.DATA_DIR / f"backup_schedule_{tag}.db"

    try:
        # Nếu dùng SQLite file, copy trực tiếp
        if config.DB_PATH.exists():
            import shutil
            shutil.copy2(config.DB_PATH, backup_path)
        else:
            # Nếu dùng Turso Cloud, tạo bản dump JSON các bảng chính
            import json
            dump_data = {
                "backup_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "schedules": database.get_all_schedules(),
                "tasks": database.get_all_tasks(),
                "medicines": database.get_all_medicines(),
                "menstrual": database.get_menstrual_records(),
                "mood_logs": database.get_mood_logs(limit=100),
            }
            backup_path = config.DATA_DIR / f"backup_turso_{tag}.json"
            with open(backup_path, "w", encoding="utf-8") as f_bk:
                json.dump(dump_data, f_bk, ensure_ascii=False, indent=2)

        caption = (
            f"💾 <b>[SAO LƯU DỮ LIỆU TỰ ĐỘNG]</b> 🌸\n"
            f"📅 Thời gian: {now.strftime('%d/%m/%Y %H:%M')}\n"
            f"Toàn bộ lịch học, deadline, đơn thuốc & nhật ký cảm xúc đã được sao lưu an toàn!"
        )
        success = notifier.send_telegram_document(my_chat_id, backup_path, caption=caption)
        try:
            if backup_path.exists():
                backup_path.unlink()
        except Exception:
            pass
        return success
    except Exception as e:
        print(f"[Backup] Lỗi sao lưu: {e}")
        return False


def check_weekly_summary():
    """Gửi tóm tắt tuần vào Chủ Nhật lúc 20:00 và tự động sao lưu dữ liệu."""
    now = get_now()
    if now.weekday() != 6 or now.hour != 20 or now.minute > 5:
        return

    today_str = now.strftime("%Y-%m-%d")
    target_key = f"weekly_summary_{today_str}"
    if database.has_notification_been_sent("weekly_summary", target_key, "her"):
        return

    msg = build_weekly_recap_message()

    if notifier.notify_her(msg):
        database.log_notification_sent("weekly_summary", target_key, "her", msg)
        print("[Scheduler] Đã gửi tóm tắt tuần mới cho cậu ấy!")

    # Tự động sao lưu dữ liệu gửi về Telegram của bạn
    try:
        backup_database_to_telegram()
        print("[Scheduler] Đã tự động sao lưu CSDL tuần về Telegram!")
    except Exception as e_bk:
        print(f"[Scheduler] Lỗi sao lưu tuần: {e_bk}")

# ======================= UTILITY =======================

def _get_hours_left(deadline_str: str) -> float:
    """Tính số giờ còn lại đến deadline. Trả về -1 nếu không parse được."""
    if not deadline_str:
        return -1
    try:
        deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        return (deadline_dt - get_now()).total_seconds() / 3600.0
    except Exception:
        return -1

# ======================= CORE SCHEDULE CHECKS =======================

def check_class_schedules():
    """Kiểm tra lịch học và gửi thông báo nhắc nhở trước 30 phút."""
    now = get_now()
    current_weekday = now.weekday()
    today_str = now.strftime("%Y-%m-%d")

    schedules = database.get_schedules_by_day(current_weekday)

    for s in schedules:
        try:
            start_parts = s["start_time"].split(":")
            start_hour, start_min = int(start_parts[0]), int(start_parts[1])
            class_dt = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)

            diff_minutes = (class_dt - now).total_seconds() / 60.0

            # Nhắc nhở nếu trong khoảng từ 20 đến 35 phút trước giờ học
            if 20 <= diff_minutes <= 35:
                target_key = f"schedule_{s['id']}_{today_str}"
                if not database.has_notification_been_sent("schedule", target_key, "her"):
                    warm_wishes = [
                        "Nhớ mang bình nước ấm và sạc laptop nha cậu! 💪",
                        "Trời có thể lạnh hoặc điều hòa phòng học rét, cậu nhớ mang áo khoác nhé! 🧥",
                        "Đi đường cẩn thận và chú ý an toàn nha cậu! 🛵",
                        "Hôm nay cậu học giỏi nhé, tớ cổ vũ cậu từ xa! 📚💖",
                    ]
                    wish = warm_wishes[s["id"] % len(warm_wishes)]

                    msg = (
                        f"🔔 <b>NHẮC LỊCH HỌC SẮP DIỄN RA!</b> 🎒\n\n"
                        f"📚 Môn học: <b>{s['subject_name']}</b>\n"
                        f"🕒 Giờ học: <b>{s['start_time']} - {s['end_time']}</b>\n"
                        f"📍 Phòng học: <b>{s['room'] or 'Theo thông báo lớp'}</b>\n"
                        f"🏷️ Phân loại: {s['category']}\n"
                    )
                    if s["notes"]:
                        msg += f"📝 Ghi chú: {s['notes']}\n"
                    msg += f"\n💌 <i>Lời dặn: {wish}</i>"

                    if notifier.notify_her(msg):
                        database.log_notification_sent("schedule", target_key, "her", msg)
                        print(f"[Scheduler] Đã nhắc lịch học: {s['subject_name']}")
        except Exception as e:
            print(f"[Scheduler] Lỗi kiểm tra lịch học {s.get('subject_name')}: {e}")

def check_task_deadlines():
    """Kiểm tra và gửi nhắc nhở deadline trước 48h, 24h, 12h và 3h kèm AI đánh giá rủi ro."""
    now = get_now()
    tasks = database.get_all_tasks(filter_status=None)

    today_weekday = now.weekday()
    classes_today = len(database.get_schedules_by_day(today_weekday))

    for t in tasks:
        if t["status"] == "Đã hoàn thành":
            continue

        try:
            deadline_dt = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
            diff_hours = (deadline_dt - now).total_seconds() / 3600.0

            if diff_hours <= 0:
                continue

            # Các mốc nhắc nhở: 48h, 24h, 12h, 3h
            milestones = [
                (48, 47.0, 49.0, "deadline_48h", "48 Giờ"),
                (24, 23.0, 25.0, "deadline_24h", "24 Giờ"),
                (12, 11.0, 13.0, "deadline_12h", "12 Giờ"),
                (3,  2.5,  3.5,  "deadline_3h",  "3 Giờ"),
            ]

            for m_hours, lower_bound, upper_bound, notif_type, label in milestones:
                if lower_bound <= diff_hours <= upper_bound:
                    target_key = f"task_{t['id']}_{notif_type}"
                    if not database.has_notification_been_sent(notif_type, target_key, "her"):
                        ai_result = deadline_ml.predict_deadline_risk(
                            task_name=t["task_name"],
                            classes_today=classes_today,
                            free_hours_left=diff_hours,
                            estimated_hours=t["estimated_hours"]
                        )

                        risk_pct = ai_result["risk_percentage"]
                        warning_msg = ai_result["warning_message"]

                        msg = (
                            f"⏰ <b>CẢNH BÁO DEADLINE (CÒN {label.upper()})!</b>\n\n"
                            f"📌 Bài tập: <b>{t['task_name']}</b>\n"
                            f"📖 Môn: {t['subject_name']}\n"
                            f"⏳ Hạn chót: <b>{t['deadline']}</b>\n"
                            f"⏱️ Khối lượng dự kiến: {t['estimated_hours']} giờ\n\n"
                            f"{warning_msg}"
                        )

                        if notifier.notify_her(msg):
                            database.log_notification_sent(notif_type, target_key, "her", msg)
                            print(f"[Scheduler] Đã nhắc deadline {label}: {t['task_name']}")
        except Exception as e:
            print(f"[Scheduler] Lỗi kiểm tra deadline task {t.get('task_name')}: {e}")

def check_menstrual_cycle():
    """
    Kiểm tra chu kỳ kinh nguyệt và cơ chế Thông báo Kép:
    - Gửi cho Cô ấy: PMS (trước 3-4 ngày), ngày bắt đầu dự kiến
    - Gửi BÍ MẬT cho Bạn (Secret Mode): trước 4 ngày
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    prediction = menstrual_ml.predict_next_cycle()
    if not prediction.get("has_data", False):
        return

    pred_next_str = prediction["predicted_next_date"]
    days_left = prediction["days_left"]

    # 1. Thông báo BÍ MẬT cho BẠN - Trước 4 ngày
    if 3 <= days_left <= 4:
        target_key = f"secret_you_{pred_next_str}"
        if not database.has_notification_been_sent("secret_you", target_key, "you"):
            secret_msg = (
                f"🍓 <b>[CHẾ ĐỘ BÍ MẬT - NHẮC NHỞ DÀNH CHO BẠN]</b> 🍓\n\n"
                f"Sếp ơi! Khoảng {days_left} ngày nữa là đến kỳ của cậu ấy rồi (Dự kiến ngày {pred_next_str}).\n"
                f"Mấy ngày tới cậu ấy có thể mệt hoặc dễ dỗi, nhớ chuẩn bị túi sưởi, đồ ngọt và kiên nhẫn hơn nhé! 🍫🧸💖"
            )
            if notifier.notify_you_secret(secret_msg):
                database.log_notification_sent("secret_you", target_key, "you", secret_msg)
                print("[Scheduler] Đã gửi thông báo Secret Mode cho Bạn!")

    # 2. Thông báo cho CẬU ẤY - Giai đoạn PMS (trước 3 ngày)
    if days_left == 3:
        target_key = f"pms_her_{pred_next_str}"
        if not database.has_notification_been_sent("pms_her", target_key, "her"):
            pms_msg = (
                f"🌸 <b>TRỢ LÝ YÊU THƯƠNG NHẮC NHỞ CẬU</b> 🌸\n\n"
                f"Dự kiến khoảng 3 ngày nữa là đến chu kỳ mới của cậu rồi đó (ngày {pred_next_str}).\n"
                f"Mấy ngày này cậu nhớ giữ ấm bụng, uống nước ấm, hạn chế ăn đồ lạnh và ngủ sớm nha cậu! 🍵💖"
            )
            if notifier.notify_her(pms_msg):
                database.log_notification_sent("pms_her", target_key, "her", pms_msg)
                print("[Scheduler] Đã gửi thông báo PMS cho Cậu ấy!")

    # 3. Thông báo cho CẬU ẤY - Ngày bắt đầu dự kiến (days_left == 0)
    if days_left == 0:
        target_key = f"start_her_{pred_next_str}"
        if not database.has_notification_been_sent("start_her", target_key, "her"):
            start_msg = (
                f"💖 <b>HÔM NAY LÀ NGÀY DỰ KIẾN BẮT ĐẦU KỲ MỚI</b> 💖\n\n"
                f"Cậu nhớ kiểm tra và mang theo các đồ dùng cá nhân cần thiết khi đi học nhé.\n"
                f"Nếu thấy mệt hay đau bụng thì nghỉ ngơi, chườm ấm và nhắn tớ ngay nha! Cố lên nhé! 🌸\n\n"
                f"<i>💡 Nhắn <code>hôm nay đến kỳ</code> để bot ghi nhận và thông báo cho cậu ấy nhé!</i>"
            )
            if notifier.notify_her(start_msg):
                database.log_notification_sent("start_her", target_key, "her", start_msg)
                print("[Scheduler] Đã gửi thông báo ngày bắt đầu cho Cậu ấy!")

def check_medicine_schedules():
    """Kiểm tra lịch uống thuốc đúng khung giờ và gửi Telegram kèm ảnh."""
    now = get_now()
    today_str = now.strftime("%Y-%m-%d")

    today_medicines = database.get_today_medicine_status(today_str)

    for item in today_medicines:
        if item["taken"]:
            continue

        slot = item["time_slot"]
        try:
            slot_parts = slot.split(":")
            slot_h, slot_m = int(slot_parts[0]), int(slot_parts[1])
            slot_dt = now.replace(hour=slot_h, minute=slot_m, second=0, microsecond=0)

            diff_minutes = (now - slot_dt).total_seconds() / 60.0

            # Gửi thông báo trong khoảng từ 0 đến 10 phút sau giờ hẹn
            if 0 <= diff_minutes <= 10:
                target_key = f"medicine_{item['medicine_id']}_{today_str}_{slot}"
                if not database.has_notification_been_sent("medicine", target_key, "her"):
                    msg = (
                        f"💊 <b>ĐẾN GIỜ UỐNG THUỐC RỒI CẬU NHÉ!</b> 🌸\n\n"
                        f"🏷️ Tên thuốc: <b>{item['medicine_name']}</b>\n"
                        f"🥄 Liều lượng: <b>{item['dosage']}</b>\n"
                        f"🕒 Khung giờ: <b>{slot}</b> (Ngày {item['day_number']}/{item['total_days']})\n\n"
                        f"<i>Uống xong cậu chỉ cần nhắn <code>đã uống thuốc</code> là bot ghi nhận ngay nhé! 🍵</i>"
                    )

                    sent = notifier.notify_her(msg, photo_path=item["image_path"])
                    if sent:
                        database.log_notification_sent("medicine", target_key, "her", msg)
                        print(f"[Scheduler] Đã nhắc uống thuốc: {item['medicine_name']} lúc {slot}")
        except Exception as e:
            print(f"[Scheduler] Lỗi kiểm tra lịch thuốc {item.get('medicine_name')}: {e}")

# ======================= MAIN LOOP =======================

import bot_interactive

def run_scheduler_tick():
    """Một nhịp quét CSDL toàn diện (mỗi 60s)."""
    try:
        check_and_send_startup_greeting()
        check_good_morning()
        check_good_night()
        check_drink_water_reminder()
        check_weekly_summary()
        check_class_schedules()
        check_task_deadlines()
        check_menstrual_cycle()
        check_medicine_schedules()
        # Watchdog: Luôn đảm bảo Telegram Bot Listener đang hoạt động 24/7
        try:
            bot_interactive.start_telegram_listener()
        except Exception:
            pass
    except Exception as e:
        print(f"[Scheduler Tick Error] {e}")

def start_scheduler_loop():
    """
    Vòng lặp quét DB định kỳ mỗi 60 giây chạy trong Thread Worker (Render.com).
    Bọc toàn diện trong try-except, tự phục hồi và không bao giờ làm crash tiến trình.
    """
    global _SCHEDULER_RUNNING
    _SCHEDULER_RUNNING = True
    print("[Scheduler] Tiến trình Scheduler Loop (24/7) đã khởi động!")
    while _SCHEDULER_RUNNING:
        try:
            run_scheduler_tick()
        except Exception as tick_err:
            print(f"[Scheduler Loop] Ngoại lệ nhịp quét: {tick_err}")

        # Chờ 60 giây (kiểm tra ngắt mỗi 1s để dừng nhanh)
        for _ in range(60):
            if not _SCHEDULER_RUNNING:
                break
            time.sleep(1)
    print("[Scheduler] Scheduler Loop đã dừng.")

def _scheduler_loop():
    """Hàm chạy trong daemon thread."""
    start_scheduler_loop()

def start_scheduler():
    """Bắt đầu chạy background Daemon Thread nếu chưa chạy (dùng cho GUI)."""
    global _SCHEDULER_RUNNING, _SCHEDULER_THREAD

    try:
        bot_interactive.start_telegram_listener()
    except Exception as e:
        print(f"[Scheduler] Không thể bật bot_interactive: {e}")

    if _SCHEDULER_RUNNING and _SCHEDULER_THREAD and _SCHEDULER_THREAD.is_alive():
        return

    _SCHEDULER_RUNNING = True
    _SCHEDULER_THREAD = threading.Thread(target=_scheduler_loop, daemon=True, name="HerAssistantScheduler")
    _SCHEDULER_THREAD.start()

def stop_scheduler():
    """Dừng scheduler an toàn."""
    global _SCHEDULER_RUNNING
    _SCHEDULER_RUNNING = False
    try:
        bot_interactive.stop_telegram_listener()
    except Exception:
        pass

if __name__ == "__main__":
    start_scheduler()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
