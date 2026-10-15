import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from config import DB_PATH

def get_connection():
    """Tạo kết nối tới SQLite CSDL."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo tất cả các bảng CSDL theo tài liệu yêu cầu."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Bảng Lịch học
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            day_of_week INTEGER NOT NULL, -- 0: Thứ 2, ..., 6: Chủ nhật
            day_name TEXT NOT NULL,
            start_time TEXT NOT NULL,      -- Định dạng HH:MM
            end_time TEXT NOT NULL,        -- Định dạng HH:MM
            room TEXT DEFAULT '',
            category TEXT NOT NULL,        -- Môn lý thuyết, Môn đồ án/bài tập lớn, Môn ngoại ngữ
            notes TEXT DEFAULT '',
            total_sessions INTEGER DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Bảng Điểm danh học tập
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            date TEXT NOT NULL,            -- Định dạng YYYY-MM-DD
            status TEXT NOT NULL,          -- Đã đi học, Vắng mặt, Học Online
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (schedule_id) REFERENCES class_schedules(id) ON DELETE CASCADE,
            UNIQUE(schedule_id, date)
        )
        ''')

        # Bảng Quản lý Task & Deadline
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            deadline TEXT NOT NULL,        -- Định dạng YYYY-MM-DD HH:MM
            estimated_hours REAL NOT NULL DEFAULT 2.0,
            status TEXT NOT NULL DEFAULT 'Chưa làm', -- Chưa làm, Đang làm, Đã hoàn thành
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Bảng Chu kỳ sinh lý phụ nữ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS menstrual_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL UNIQUE, -- Định dạng YYYY-MM-DD
            cycle_length INTEGER DEFAULT 28, -- Số ngày của chu kỳ
            period_length INTEGER DEFAULT 5, -- Số ngày đèn đỏ
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Bảng Đơn thuốc & Lịch uống thuốc
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,          -- Ví dụ: 1 viên sau ăn
            times TEXT NOT NULL,           -- Ví dụ: 08:00, 12:30, 20:00
            days_count INTEGER DEFAULT 5,  -- Số ngày cần uống
            start_date TEXT NOT NULL,      -- Định dạng YYYY-MM-DD
            image_path TEXT DEFAULT '',    -- Ảnh chụp vỏ thuốc / đơn thuốc
            notes TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Bảng Xác nhận uống thuốc theo liều trong ngày
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            date TEXT NOT NULL,            -- YYYY-MM-DD
            time_slot TEXT NOT NULL,       -- HH:MM
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Đã uống',
            FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
            UNIQUE(medicine_id, date, time_slot)
        )
        ''')

        # Bảng Nhật ký thông báo Telegram (để tránh bắn tin lặp lại)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            sent_to TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(notification_type, target_id, sent_to)
        )
        ''')
        
        conn.commit()

# ======================= CRUD: LỊCH HỌC & ĐIỂM DANH =======================

def add_schedule(subject_name: str, day_of_week: int, day_name: str, 
                 start_time: str, end_time: str, room: str, 
                 category: str, notes: str = "", total_sessions: int = 15) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO class_schedules (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions))
        conn.commit()
        return cursor.lastrowid

def update_schedule(schedule_id: int, subject_name: str, day_of_week: int, day_name: str,
                    start_time: str, end_time: str, room: str,
                    category: str, notes: str, total_sessions: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE class_schedules 
        SET subject_name = ?, day_of_week = ?, day_name = ?, start_time = ?, end_time = ?, room = ?, category = ?, notes = ?, total_sessions = ?
        WHERE id = ?
        ''', (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions, schedule_id))
        conn.commit()

def delete_schedule(schedule_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM class_schedules WHERE id = ?", (schedule_id,))
        cursor.execute("DELETE FROM attendance_logs WHERE schedule_id = ?", (schedule_id,))
        conn.commit()

def get_all_schedules() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM class_schedules ORDER BY day_of_week, start_time")
        return [dict(row) for row in cursor.fetchall()]

def get_schedules_by_day(day_of_week: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM class_schedules WHERE day_of_week = ? ORDER BY start_time", (day_of_week,))
        return [dict(row) for row in cursor.fetchall()]

def log_attendance(schedule_id: int, log_date: str, status: str, notes: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO attendance_logs (schedule_id, date, status, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(schedule_id, date) DO UPDATE SET status = excluded.status, notes = excluded.notes
        ''', (schedule_id, log_date, status, notes))
        conn.commit()

def get_attendance_stats(schedule_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT total_sessions, subject_name FROM class_schedules WHERE id = ?", (schedule_id,))
        sched = cursor.fetchone()
        if not sched:
            return {"total": 0, "attended": 0, "absent": 0, "online": 0, "absent_rate": 0.0, "is_warning": False}
        
        total = sched["total_sessions"] or 15
        subject_name = sched["subject_name"]
        
        cursor.execute("SELECT status, COUNT(*) as count FROM attendance_logs WHERE schedule_id = ? GROUP BY status", (schedule_id,))
        rows = cursor.fetchall()
        counts = {r["status"]: r["count"] for r in rows}
        
        attended = counts.get("Đã đi học", 0)
        absent = counts.get("Vắng mặt", 0)
        online = counts.get("Học Online", 0)
        
        absent_rate = (absent / total) * 100.0 if total > 0 else 0.0
        # Cảnh báo nếu vắng mặt quá 20% số buổi quy định
        is_warning = absent_rate >= 20.0 or absent >= (total * 0.2)
        
        return {
            "schedule_id": schedule_id,
            "subject_name": subject_name,
            "total": total,
            "attended": attended,
            "absent": absent,
            "online": online,
            "absent_rate": round(absent_rate, 1),
            "is_warning": is_warning
        }

def get_all_attendance_stats() -> List[Dict[str, Any]]:
    schedules = get_all_schedules()
    return [get_attendance_stats(s["id"]) for s in schedules]

def get_attendance_history(schedule_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if schedule_id:
            cursor.execute('''
            SELECT a.*, s.subject_name 
            FROM attendance_logs a
            JOIN class_schedules s ON a.schedule_id = s.id
            WHERE a.schedule_id = ?
            ORDER BY a.date DESC
            ''', (schedule_id,))
        else:
            cursor.execute('''
            SELECT a.*, s.subject_name 
            FROM attendance_logs a
            JOIN class_schedules s ON a.schedule_id = s.id
            ORDER BY a.date DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]

# ======================= CRUD: TASK & DEADLINE =======================

def add_task(task_name: str, subject_name: str, deadline: str, estimated_hours: float, status: str = "Chưa làm") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO tasks (task_name, subject_name, deadline, estimated_hours, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (task_name, subject_name, deadline, estimated_hours, status))
        conn.commit()
        return cursor.lastrowid

def update_task_status(task_id: int, status: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()

def delete_task(task_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

def get_all_tasks(filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if filter_status and filter_status != "Tất cả":
            cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY deadline ASC", (filter_status,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY deadline ASC")
        return [dict(row) for row in cursor.fetchall()]

# ======================= CRUD: CHU KỲ KINH NGUYỆT =======================

def add_menstrual_record(start_date: str, cycle_length: Optional[int] = None, period_length: int = 5, notes: str = "") -> int:
    """Thêm ngày bắt đầu chu kỳ mới. Nếu cycle_length chưa có, tự động tính từ kỳ trước."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Tìm kỳ trước đó gần nhất
        cursor.execute("SELECT start_date FROM menstrual_records WHERE start_date < ? ORDER BY start_date DESC LIMIT 1", (start_date,))
        prev_row = cursor.fetchone()
        
        if prev_row and cycle_length is None:
            prev_d = datetime.strptime(prev_row["start_date"], "%Y-%m-%d").date()
            curr_d = datetime.strptime(start_date, "%Y-%m-%d").date()
            diff_days = (curr_d - prev_d).days
            if 15 <= diff_days <= 60:
                cycle_length = diff_days
            else:
                cycle_length = 28
        elif cycle_length is None:
            cycle_length = 28

        cursor.execute('''
        INSERT INTO menstrual_records (start_date, cycle_length, period_length, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(start_date) DO UPDATE SET cycle_length = excluded.cycle_length, period_length = excluded.period_length, notes = excluded.notes
        ''', (start_date, cycle_length, period_length, notes))
        conn.commit()
        return cursor.lastrowid

def get_all_menstrual_records() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menstrual_records ORDER BY start_date ASC")
        return [dict(row) for row in cursor.fetchall()]

def get_latest_menstrual_record() -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menstrual_records ORDER BY start_date DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_menstrual_record(record_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menstrual_records WHERE id = ?", (record_id,))
        conn.commit()

# ======================= CRUD: ĐƠN THUỐC & LỊCH UỐNG THUỐC =======================

def add_medicine(name: str, dosage: str, times: str, days_count: int, start_date: str, image_path: str = "", notes: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO medicines (name, dosage, times, days_count, start_date, image_path, notes, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (name, dosage, times, days_count, start_date, image_path, notes))
        conn.commit()
        return cursor.lastrowid

def update_medicine(med_id: int, name: str, dosage: str, times: str, days_count: int, start_date: str, active: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE medicines
        SET name = ?, dosage = ?, times = ?, days_count = ?, start_date = ?, active = ?
        WHERE id = ?
        ''', (name, dosage, times, days_count, start_date, active, med_id))
        conn.commit()

def delete_medicine(med_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
        cursor.execute("DELETE FROM medicine_logs WHERE medicine_id = ?", (med_id,))
        conn.commit()

def get_all_medicines(only_active: bool = False) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if only_active:
            cursor.execute("SELECT * FROM medicines WHERE active = 1 ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM medicines ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def log_medicine_taken(medicine_id: int, log_date: str, time_slot: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO medicine_logs (medicine_id, date, time_slot, status)
        VALUES (?, ?, ?, 'Đã uống')
        ON CONFLICT(medicine_id, date, time_slot) DO UPDATE SET status = 'Đã uống', taken_at = CURRENT_TIMESTAMP
        ''', (medicine_id, log_date, time_slot))
        conn.commit()

def is_medicine_taken_today(medicine_id: int, log_date: str, time_slot: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM medicine_logs WHERE medicine_id = ? AND date = ? AND time_slot = ?", 
                       (medicine_id, log_date, time_slot))
        return cursor.fetchone() is not None

def get_today_medicine_status(today_str: str) -> List[Dict[str, Any]]:
    """Lấy danh sách tất cả các liều thuốc cần uống hôm nay cùng trạng thái đã uống hay chưa."""
    medicines = get_all_medicines(only_active=True)
    results = []
    today_d = datetime.strptime(today_str, "%Y-%m-%d").date()
    
    for med in medicines:
        med_start = datetime.strptime(med["start_date"], "%Y-%m-%d").date()
        days_passed = (today_d - med_start).days
        # Kiểm tra còn trong thời hạn uống không
        if 0 <= days_passed < med["days_count"]:
            times_list = [t.strip() for t in med["times"].split(",") if t.strip()]
            for slot in times_list:
                taken = is_medicine_taken_today(med["id"], today_str, slot)
                results.append({
                    "medicine_id": med["id"],
                    "medicine_name": med["name"],
                    "dosage": med["dosage"],
                    "time_slot": slot,
                    "image_path": med["image_path"],
                    "taken": taken,
                    "day_number": days_passed + 1,
                    "total_days": med["days_count"]
                })
    return results

# ======================= NOTIFICATION LOGS =======================

def has_notification_been_sent(notification_type: str, target_id: str, sent_to: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id FROM notification_logs 
        WHERE notification_type = ? AND target_id = ? AND sent_to = ?
        ''', (notification_type, str(target_id), sent_to))
        return cursor.fetchone() is not None

def log_notification_sent(notification_type: str, target_id: str, sent_to: str, message: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO notification_logs (notification_type, target_id, sent_to, message)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(notification_type, target_id, sent_to) DO NOTHING
        ''', (notification_type, str(target_id), sent_to, message))
        conn.commit()

# Khởi tạo CSDL khi import
init_db()
