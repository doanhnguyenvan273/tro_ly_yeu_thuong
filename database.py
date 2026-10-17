import sqlite3
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from config import DB_PATH, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN

class TursoCursor:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []
        self._lastrowid = None
        self._rowcount = 0
        self._index = 0

    def execute(self, sql: str, params=()):
        result = self.conn._execute_stmt(sql, params)
        cols = [c["name"] for c in result.get("cols", [])]
        rows = result.get("rows", [])
        self._lastrowid = int(result["last_insert_rowid"]) if result.get("last_insert_rowid") is not None else None
        self._rowcount = result.get("affected_row_count", 0)
        
        parsed_rows = []
        for r in rows:
            row_dict = {}
            for col_name, val_obj in zip(cols, r):
                t = val_obj.get("type")
                v = val_obj.get("value")
                if t == "null" or v is None:
                    row_dict[col_name] = None
                elif t == "integer":
                    row_dict[col_name] = int(v)
                elif t == "float":
                    row_dict[col_name] = float(v)
                else:
                    row_dict[col_name] = str(v)
            parsed_rows.append(row_dict)
        self._rows = parsed_rows
        self._index = 0
        return self

    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        res = self._rows[self._index:]
        self._index = len(self._rows)
        return res

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._rowcount

_turso_session = None

def get_turso_session() -> requests.Session:
    global _turso_session
    if _turso_session is None:
        _turso_session = _create_turso_session()
    return _turso_session

def _create_turso_session() -> requests.Session:
    """Tạo một requests.Session mới với retry policy."""
    from urllib3.util.retry import Retry
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=5,
        pool_maxsize=10,
        max_retries=retry,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def reset_turso_session():
    """Xóa session cũ đã bị đứt kết nối để lần sau tạo mới."""
    global _turso_session
    if _turso_session is not None:
        try:
            _turso_session.close()
        except Exception:
            pass
    _turso_session = None

class TursoConnection:
    def __init__(self, url: str, token: str):
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        if not url.endswith("/v2/pipeline"):
            url = url.rstrip("/") + "/v2/pipeline"
        self.pipeline_url = url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _format_args(self, params):
        formatted = []
        for p in params:
            if p is None:
                formatted.append({"type": "null"})
            elif isinstance(p, bool):
                formatted.append({"type": "integer", "value": "1" if p else "0"})
            elif isinstance(p, int):
                formatted.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                formatted.append({"type": "float", "value": p})
            else:
                formatted.append({"type": "text", "value": str(p)})
        return formatted

    def _execute_stmt(self, sql: str, params=()):
        args = self._format_args(params) if params else []
        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": args
                    }
                },
                {"type": "close"}
            ]
        }
        # Thử lần 1 với session hiện tại, nếu bị đứt kết nối thì reset để retry
        for attempt in range(2):
            try:
                session = get_turso_session()
                resp = session.post(
                    self.pipeline_url,
                    headers=self.headers,
                    json=payload,
                    timeout=15,
                )
                break  # thành công, thoát vòng
            except requests.exceptions.ConnectionError as e:
                if attempt == 0:
                    # Session bị chết → reset và thử lại với session mới
                    print(f"[Turso] Connection dropped, resetting session and retrying... ({e})")
                    reset_turso_session()
                else:
                    raise  # Lần 2 vẫn lỗi → cho nổ lần này
        if resp.status_code != 200:
            raise Exception(f"Turso Error {resp.status_code}: {resp.text}")
        data = resp.json()
        first_result = data.get("results", [{}])[0]
        if first_result.get("type") == "error":
            raise Exception(f"Turso Query Error: {first_result.get('error', {}).get('message')}")
        return first_result.get("response", {}).get("result", {})

    def cursor(self):
        return TursoCursor(self)

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def get_connection():
    """Tạo kết nối tới Turso Cloud DB (nếu có cấu hình) hoặc fallback về SQLite local."""
    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
        try:
            return TursoConnection(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
        except Exception as e:
            print(f"[Database] Lỗi kết nối Turso ({e}), chuyển sang SQLite local.")
    
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
            max_absences INTEGER DEFAULT 3, -- Số buổi được phép vắng (nhập thủ công)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        # Migration: Thêm cột max_absences nếu DB cũ chưa có
        try:
            cursor.execute("ALTER TABLE class_schedules ADD COLUMN max_absences INTEGER DEFAULT 3")
            conn.commit()
        except Exception:
            pass  # Cột đã tồn tại, bỏ qua

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
                 category: str, notes: str = "", total_sessions: int = 15,
                 max_absences: int = 3) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO class_schedules (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions, max_absences)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions, max_absences))
        conn.commit()
        return cursor.lastrowid

def update_schedule(schedule_id: int, subject_name: str, day_of_week: int, day_name: str,
                    start_time: str, end_time: str, room: str,
                    category: str, notes: str, total_sessions: int, max_absences: int = 3):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE class_schedules
        SET subject_name = ?, day_of_week = ?, day_name = ?, start_time = ?, end_time = ?, room = ?, category = ?, notes = ?, total_sessions = ?, max_absences = ?
        WHERE id = ?
        ''', (subject_name, day_of_week, day_name, start_time, end_time, room, category, notes, total_sessions, max_absences, schedule_id))
        conn.commit()

def update_schedule_limits(schedule_id: int, total_sessions: int, max_absences: int):
    """Cập nhật nhanh tổng số buổi và giới hạn số buổi được phép nghỉ."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE class_schedules
        SET total_sessions = ?, max_absences = ?
        WHERE id = ?
        ''', (total_sessions, max_absences, schedule_id))
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
        cursor.execute("SELECT total_sessions, max_absences, subject_name FROM class_schedules WHERE id = ?", (schedule_id,))
        sched = cursor.fetchone()
        if not sched:
            return {"total": 0, "max_absences": 3, "attended": 0, "absent": 0, "online": 0, "absent_rate": 0.0, "remaining_absences": 3, "is_warning": False}

        total = sched["total_sessions"] or 15
        # Ưu tiên max_absences do người dùng nhập; fallback về 20% tổng buổi
        max_abs = sched["max_absences"]
        if max_abs is None:
            max_abs = max(1, int(total * 0.2))
        subject_name = sched["subject_name"]

        cursor.execute("SELECT status, COUNT(*) as count FROM attendance_logs WHERE schedule_id = ? GROUP BY status", (schedule_id,))
        rows = cursor.fetchall()
        counts = {r["status"]: r["count"] for r in rows}

        attended = counts.get("Đã đi học", 0)
        absent = counts.get("Vắng mặt", 0)
        online = counts.get("Học Online", 0)

        absent_rate = (absent / total) * 100.0 if total > 0 else 0.0
        remaining = max_abs - absent
        # Cảnh báo khi số buổi vắng vượt quá giới hạn cho phép
        is_warning = absent >= max_abs

        return {
            "schedule_id": schedule_id,
            "subject_name": subject_name,
            "total": total,
            "max_absences": max_abs,
            "attended": attended,
            "absent": absent,
            "online": online,
            "absent_rate": round(absent_rate, 1),
            "remaining_absences": remaining,
            "is_warning": is_warning
        }

def get_all_attendance_stats() -> List[Dict[str, Any]]:
    """Lấy thống kê điểm danh cho tất cả các môn trong duy nhất 1-2 truy vấn (tối ưu tốc độ)."""
    schedules = get_all_schedules()
    if not schedules:
        return []

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT schedule_id, status, COUNT(*) as count FROM attendance_logs GROUP BY schedule_id, status")
        rows = cursor.fetchall()

    counts_map = {}
    for r in rows:
        sid = r["schedule_id"]
        if sid not in counts_map:
            counts_map[sid] = {}
        counts_map[sid][r["status"]] = r["count"]

    res = []
    for s in schedules:
        sid = s["id"]
        total = s.get("total_sessions") or 10
        max_abs = s.get("max_absences")
        if max_abs is None:
            max_abs = max(1, int(total * 0.2))

        c = counts_map.get(sid, {})
        attended = c.get("Đã đi học", 0)
        absent = c.get("Vắng mặt", 0)
        online = c.get("Học Online", 0)

        absent_rate = (absent / total) * 100.0 if total > 0 else 0.0
        remaining = max_abs - absent
        is_warning = absent >= max_abs

        res.append({
            "schedule_id": sid,
            "subject_name": s["subject_name"],
            "total": total,
            "max_absences": max_abs,
            "attended": attended,
            "absent": absent,
            "online": online,
            "absent_rate": round(absent_rate, 1),
            "remaining_absences": remaining,
            "is_warning": is_warning
        })
    return res

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
