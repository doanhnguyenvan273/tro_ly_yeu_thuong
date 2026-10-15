import time
import sys
import threading
from datetime import datetime, date, timedelta
from typing import Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import database
import notifier
from config import load_settings, save_settings
import deadline_ml
import menstrual_ml

# Cờ kiểm soát vòng lặp daemon
_SCHEDULER_RUNNING = False
_SCHEDULER_THREAD: Optional[threading.Thread] = None

def check_and_send_startup_greeting():
    """Gửi tin nhắn chào mừng / chúc 20/10 ngọt ngào khi ứng dụng khởi chạy lần đầu."""
    settings = load_settings()
    if not settings.get("startup_greeting_sent", False):
        her_name = settings.get("her_name", "Em yêu 🌸")
        msg = (
            f"🎉 <b>CHÀO MỪNG {her_name.upper()} ĐẾN VỚI TRỢ LÝ YÊU THƯƠNG 💖</b>\n\n"
            f"Hôm nay là một ngày thật đặc biệt! Ứng dụng trợ lý nhỏ bé này được tạo ra dành riêng cho em, "
            f"để đồng hành cùng em trong từng buổi học, từng deadline và chăm sóc sức khỏe của em mỗi ngày.\n\n"
            f"Chúc em luôn rạng rỡ, bình an và hạnh phúc! Anh luôn ở đây bên cạnh em! 💐🍓✨"
        )
        if notifier.notify_her(msg):
            settings["startup_greeting_sent"] = True
            save_settings(settings)
            print("[Scheduler] Đã gửi tin nhắn chào mừng thành công!")

def check_class_schedules():
    """Kiểm tra lịch học và gửi thông báo nhắc nhở trước 30 phút."""
    now = datetime.now()
    current_weekday = now.weekday() # 0 = Thứ 2, ..., 6 = Chủ nhật
    today_str = now.strftime("%Y-%m-%d")
    
    schedules = database.get_schedules_by_day(current_weekday)
    
    for s in schedules:
        try:
            start_parts = s["start_time"].split(":")
            start_hour, start_min = int(start_parts[0]), int(start_parts[1])
            class_dt = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            
            # Tính khoảng cách phút từ bây giờ đến giờ học
            diff_minutes = (class_dt - now).total_seconds() / 60.0
            
            # Nhắc nhở nếu trong khoảng từ 20 đến 35 phút trước giờ học
            if 20 <= diff_minutes <= 35:
                target_key = f"schedule_{s['id']}_{today_str}"
                if not database.has_notification_been_sent("schedule", target_key, "her"):
                    warm_wishes = [
                        "Nhớ mang bình nước ấm và sạc laptop nha em!",
                        "Trời có thể lạnh hoặc điều hòa phòng học rét, em nhớ mang áo khoác nhé!",
                        "Đi đường cẩn thận và chú ý an toàn nha cô bé của anh! 🛵"
                    ]
                    # Chọn lời nhắn theo id
                    wish = warm_wishes[s["id"] % len(warm_wishes)]
                    
                    msg = (
                        f"🔔 <b>NHẮC LỊCH HỌC SẮP DIỄN RA!</b> 🎒\n\n"
                        f"📚 Môn học: <b>{s['subject_name']}</b>\n"
                        f"🕒 Giờ học: <b>{s['start_time']} - {s['end_time']}</b>\n"
                        f"📍 Phòng học: <b>{s['room'] or 'Theo thông báo'}</b>\n"
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
    """Kiểm tra và gửi nhắc nhở deadline trước 24h, 12h và 3h kèm AI đánh giá rủi ro."""
    now = datetime.now()
    tasks = database.get_all_tasks(filter_status=None)
    
    # Đếm số ca học hôm nay để đưa vào model ML
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
                
            # Các mốc nhắc nhở: 24h, 12h, 3h
            milestones = [
                (24, 23.0, 25.0, "deadline_24h", "24 Giờ"),
                (12, 11.0, 13.0, "deadline_12h", "12 Giờ"),
                (3, 2.5, 3.5, "deadline_3h", "3 Giờ")
            ]
            
            for m_hours, lower_bound, upper_bound, notif_type, label in milestones:
                if lower_bound <= diff_hours <= upper_bound:
                    target_key = f"task_{t['id']}_{notif_type}"
                    if not database.has_notification_been_sent(notif_type, target_key, "her"):
                        # Chạy AI dự đoán rủi ro
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
    - Gửi cho Cô ấy:
      + Giai đoạn PMS (trước 3-4 ngày)
      + Ngày bắt đầu dự kiến
    - Gửi BÍ MẬT cho Bạn (Secret Mode):
      + Trước 4 ngày
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    prediction = menstrual_ml.predict_next_cycle()
    if not prediction.get("has_data", False):
        return
        
    pred_next_str = prediction["predicted_next_date"]
    days_left = prediction["days_left"]
    
    # 1. Thông báo BÍ MẬT cho BẠN (Secret Mode) - Trước 4 ngày
    if days_left == 4 or (3 <= days_left <= 4):
        target_key = f"secret_you_{pred_next_str}"
        if not database.has_notification_been_sent("secret_you", target_key, "you"):
            secret_msg = (
                f"🍓 <b>[CHẾ ĐỘ BÍ MẬT - NHẮC NHỞ DÀNH CHO BẠN]</b> 🍓\n\n"
                f"Sếp ơi! Khoảng 4 ngày nữa là đến kỳ của em ấy rồi (Dự kiến ngày {pred_next_str}).\n"
                f"Mấy ngày tới em ấy có thể mệt hoặc dễ dỗi, nhớ chuẩn bị túi sưởi, đồ ngọt và kiên nhẫn hơn nhé! 🍫🧸💖"
            )
            if notifier.notify_you_secret(secret_msg):
                database.log_notification_sent("secret_you", target_key, "you", secret_msg)
                print("[Scheduler] Đã gửi thông báo Secret Mode cho Bạn!")

    # 2. Thông báo cho CÔ ẤY - Giai đoạn PMS (trước 3 ngày)
    if days_left == 3:
        target_key = f"pms_her_{pred_next_str}"
        if not database.has_notification_been_sent("pms_her", target_key, "her"):
            pms_msg = (
                f"🌸 <b>TRỢ LÝ YÊU THƯƠNG NHẮC NHỞ EM</b> 🌸\n\n"
                f"Dự kiến khoảng 3 ngày nữa là đến chu kỳ mới của em rồi đó (ngày {pred_next_str}).\n"
                f"Mấy ngày này em nhớ giữ ấm bụng, uống nước ấm, hạn chế ăn đồ lạnh và ngủ sớm nha em yêu! 🍵💖"
            )
            if notifier.notify_her(pms_msg):
                database.log_notification_sent("pms_her", target_key, "her", pms_msg)
                print("[Scheduler] Đã gửi thông báo PMS cho Cô ấy!")

    # 3. Thông báo cho CÔ ẤY - Ngày bắt đầu dự kiến (days_left == 0)
    if days_left == 0:
        target_key = f"start_her_{pred_next_str}"
        if not database.has_notification_been_sent("start_her", target_key, "her"):
            start_msg = (
                f"💖 <b>HÔM NAY LÀ NGÀY DỰ KIẾN BẮT ĐẦU KỲ MỚI</b> 💖\n\n"
                f"Em nhớ kiểm tra và mang theo các đồ dùng cá nhân cần thiết khi đi học nhé.\n"
                f"Nếu thấy mệt hay đau bụng thì nghỉ ngơi, chườm ấm và nhắn anh ngay nha! Yêu em nhiều! 🌸"
            )
            if notifier.notify_her(start_msg):
                database.log_notification_sent("start_her", target_key, "her", start_msg)
                print("[Scheduler] Đã gửi thông báo ngày bắt đầu cho Cô ấy!")

def check_medicine_schedules():
    """Kiểm tra lịch uống thuốc đúng khung giờ và gửi Telegram kèm ảnh."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")
    
    today_medicines = database.get_today_medicine_status(today_str)
    
    for item in today_medicines:
        # Nếu đã uống rồi thì bỏ qua không nhắc
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
                        f"💊 <b>ĐẾN GIỜ UỐNG THUỐC RỒI EM NHÉ!</b> 🌸\n\n"
                        f"🏷️ Tên thuốc: <b>{item['medicine_name']}</b>\n"
                        f"🥄 Liều lượng: <b>{item['dosage']}</b>\n"
                        f"🕒 Khung giờ: <b>{slot}</b> (Ngày {item['day_number']}/{item['total_days']})\n\n"
                        f"<i>Uống thuốc đúng giờ để mau khỏe nha cô bé! Uống xong nhớ vào app bấm 'Đã uống liều này' nhé! 🍵</i>"
                    )
                    
                    sent = notifier.notify_her(msg, photo_path=item["image_path"])
                    if sent:
                        database.log_notification_sent("medicine", target_key, "her", msg)
                        print(f"[Scheduler] Đã nhắc uống thuốc: {item['medicine_name']} lúc {slot}")
        except Exception as e:
            print(f"[Scheduler] Lỗi kiểm tra lịch thuốc {item.get('medicine_name')}: {e}")

import bot_interactive

def run_scheduler_tick():
    """Một nhịp quét CSDL toàn diện (mỗi 60s)."""
    try:
        check_and_send_startup_greeting()
        check_class_schedules()
        check_task_deadlines()
        check_menstrual_cycle()
        check_medicine_schedules()
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
            
        # Chờ 60 giây (kiểm tra ngắt mỗi 1s)
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
    
    # Khởi động bộ lắng nghe tin nhắn Telegram để tra cứu lịch
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
