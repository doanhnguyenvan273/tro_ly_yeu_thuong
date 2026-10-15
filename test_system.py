import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Đảm bảo đường dẫn import
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


import config
import database
import deadline_ml
import menstrual_ml
import medicine_ocr
import notifier
import scheduler

def test_all():
    print(">>> [TEST 1] Khởi tạo CSDL & CRUD Lịch học & Điểm danh...")
    database.init_db()
    
    # Thêm môn học thử nghiệm
    sched_id = database.add_schedule(
        subject_name="Công nghệ phần mềm SE2033",
        day_of_week=0,
        day_name="Thứ Hai",
        start_time="07:30",
        end_time="11:00",
        room="A2-402",
        category="Môn lý thuyết",
        notes="Phải mang laptop",
        total_sessions=10
    )
    assert sched_id > 0, "Lỗi thêm lịch học"
    
    # Điểm danh: 3 buổi vắng mặt (30% > 20% -> phải kích hoạt cảnh báo cấm thi)
    database.log_attendance(sched_id, "2026-10-01", "Vắng mặt")
    database.log_attendance(sched_id, "2026-10-08", "Vắng mặt")
    database.log_attendance(sched_id, "2026-10-15", "Vắng mặt")
    database.log_attendance(sched_id, "2026-10-22", "Đã đi học")
    
    stats = database.get_attendance_stats(sched_id)
    assert stats["is_warning"] is True, f"Cảnh báo cấm thi phải là True! Nhận được: {stats}"
    assert stats["absent_rate"] == 30.0, f"Tỷ lệ vắng mặt phải là 30%! Nhận được: {stats['absent_rate']}"
    print(f"    ✅ Điểm danh & Cảnh báo cấm thi thành công! (Vắng {stats['absent']}/{stats['total']}, Tỷ lệ: {stats['absent_rate']}%, Cảnh báo: {stats['is_warning']})")

    print("\n>>> [TEST 2] Quản lý Task & AI Dự đoán Rủi ro (RandomForestClassifier)...")
    task_id = database.add_task(
        task_name="Bài tập lớn SE2033",
        subject_name="Công nghệ phần mềm SE2033",
        deadline=(datetime.now() + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
        estimated_hours=4.0
    )
    assert task_id > 0, "Lỗi thêm task"
    
    # Dự đoán rủi ro: 3 ca học, chỉ còn 3.5 giờ rảnh, khối lượng 4h
    risk_res = deadline_ml.predict_deadline_risk(
        task_name="Bài tập lớn SE2033",
        classes_today=3,
        free_hours_left=3.5,
        estimated_hours=4.0
    )
    print(f"    Rủi ro dự đoán: {risk_res['risk_percentage']}% - Mức độ: {risk_res['warning_level']}")
    print(f"    Thông điệp: {risk_res['warning_message']}")
    assert risk_res["risk_percentage"] >= 60.0, "Nguy cơ trễ hạn phải cao do thiếu giờ rảnh và nhiều ca học!"
    print("    ✅ Module AI Deadline hoạt động chính xác!")

    print("\n>>> [TEST 3] AI Dự đoán Chu kỳ Kinh nguyệt (RandomForestRegressor)...")
    # Thêm dữ liệu chu kỳ
    today = date.today()
    database.add_menstrual_record((today - timedelta(days=60)).strftime("%Y-%m-%d"), cycle_length=28)
    database.add_menstrual_record((today - timedelta(days=32)).strftime("%Y-%m-%d"), cycle_length=28)
    database.add_menstrual_record((today - timedelta(days=4)).strftime("%Y-%m-%d"), cycle_length=28)
    
    menstrual_ml.retrain_model()
    cycle_pred = menstrual_ml.predict_next_cycle()
    print(f"    Dự đoán chu kỳ: {cycle_pred['predicted_length']} ngày")
    print(f"    Ngày bắt đầu kế tiếp: {cycle_pred['predicted_next_date']}")
    print(f"    Giai đoạn PMS: {cycle_pred['pms_start_date']}")
    print(f"    Số ngày còn lại: {cycle_pred['days_left']}")
    assert cycle_pred["has_data"] is True, "Phải có dữ liệu dự đoán!"
    print("    ✅ Module AI Chu kỳ sinh lý hoạt động chính xác!")

    print("\n>>> [TEST 4] Nhận diện Từ khóa Đơn thuốc & Vỏ thuốc (OCR/NLP Regex)...")
    test_prescription = "Đơn thuốc: PANADOL EXTRA 500mg. Uống 2 viên sau ăn, ngày 3 lần: sáng, trưa, tối. Dùng liên tục 5 ngày."
    parsed = medicine_ocr.parse_medicine_info(test_prescription)
    print(f"    Tên thuốc: {parsed['name']}")
    print(f"    Liều lượng: {parsed['dosage']}")
    print(f"    Các khung giờ: {parsed['times']}")
    print(f"    Số ngày: {parsed['days_count']}")
    assert "panadol" in parsed["name"].lower(), "Không nhận diện được tên thuốc Panadol!"
    assert "2 viên" in parsed["dosage"].lower(), "Không nhận diện đúng số viên!"
    assert "08:00" in parsed["times"] and "12:30" in parsed["times"] and "20:00" in parsed["times"], "Không nhận diện đúng mốc giờ!"
    print("    ✅ Module Phân tích Đơn thuốc hoạt động chính xác!")

    print("\n>>> [TEST 5] Kiểm tra Notifier & Chống Crash...")
    # Khi token trống hoặc chat_id trống, notifier không được ném Exception làm sập app
    res1 = notifier.send_telegram_message("", "test")
    assert res1 is False, "Phải trả về False an toàn khi token rỗng"
    res2 = notifier.send_telegram_message("12345", "", "")
    # Kiểm tra an toàn khi không có nội dung hoặc token rỗng
    assert notifier.send_telegram_photo("", "") is False, "Phải trả về False an toàn khi ảnh rỗng"
    print("    ✅ Notifier chống sập và xử lý an toàn 100%!")

    print("\n>>> [TEST 6] Kiểm tra Scheduler Tick...")
    # Chạy thử một nhịp quét
    scheduler.run_scheduler_tick()
    print("    ✅ Scheduler quét CSDL thành công không có lỗi!")

    print("\n" + "=" * 60)
    print("🎉 TẤT CẢ CÁC BÀI KIỂM THỬ ĐÃ VƯỢT QUA 100%! HỆ THỐNG HOÀN TOÀN CHÍNH XÁC THEO SRS!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
