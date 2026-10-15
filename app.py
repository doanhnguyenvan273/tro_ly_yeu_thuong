import streamlit as st
from datetime import datetime, date, time, timedelta
import pandas as pd
from pathlib import Path
from PIL import Image
import os

import config
import database
import deadline_ml
import menstrual_ml
import medicine_ocr
import notifier
import scheduler

import telegram_listener

st.set_page_config(
    page_title="Trợ Lý Yêu Thương 💖",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

scheduler.start_scheduler()
telegram_listener.start_telegram_listener()

# ======= CSS =======
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }
.stApp { background: linear-gradient(135deg, #fff5f7 0%, #fbf5ff 50%, #fff9f5 100%); }

.main-header {
    background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
    padding: 22px 28px; border-radius: 20px; color: white;
    text-align: center; box-shadow: 0 10px 25px rgba(255,117,140,0.25); margin-bottom: 22px;
}
.main-header h1 { margin:0; font-weight:700; font-size:2rem; }
.main-header p  { margin:6px 0 0 0; font-size:1rem; opacity:.95; }

.card {
    background: rgba(255,255,255,0.92); border: 1px solid rgba(255,182,193,0.45);
    border-radius: 16px; padding: 20px 22px;
    box-shadow: 0 6px 18px rgba(255,182,193,0.13); margin-bottom: 16px;
}
.section-title { font-size:1.1rem; font-weight:700; color:#d81159; margin-bottom:12px; }

.preview-box {
    background: linear-gradient(135deg,#fff0f5,#ffe4e9);
    border: 1.5px solid #ffb3c6; border-radius: 14px; padding: 16px 20px;
    margin-top: 12px; font-size: 0.97rem; line-height: 1.7;
}
.preview-box b { color: #c0185a; }

.quick-btn-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
.hint-text { font-size:0.83rem; color:#888; margin-top:-6px; margin-bottom:8px; }

.badge-danger { background:#ffe0e6; color:#d81159; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #ffb3c1; display:inline-block; }
.badge-safe   { background:#e8f8f0; color:#0d8a52; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #b7ebd0; display:inline-block; }
.badge-warn   { background:#fff4e5; color:#d97706; font-weight:600;
    padding:3px 12px; border-radius:20px; border:1px solid #fed7aa; display:inline-block; }

.step-label { background:#ff758c; color:white; border-radius:50%; width:26px; height:26px;
    display:inline-flex; align-items:center; justify-content:center; font-weight:700;
    font-size:0.85rem; margin-right:8px; }

#MainMenu {visibility:hidden;} footer {visibility:hidden;}
div.stButton > button { border-radius:25px; font-weight:600; border:none; transition:all .25s; }
div.stButton > button:hover { transform:scale(1.02); }
</style>
""", unsafe_allow_html=True)

settings = config.load_settings()
her_name = settings.get("her_name", "Em Yêu 🌸")

# ======= BẢO MẬT: XÁC THỰC MẬT KHẨU (WEB_PASSWORD) =======
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"""
    <div class="main-header" style="max-width:500px; margin: 60px auto 25px auto;">
      <h1>🔐 TRỢ LÝ YÊU THƯƠNG 🌸</h1>
      <p>Ứng dụng cá nhân bảo mật • Dành riêng cho {her_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown("""<div class="card" style="text-align:center;">
            <p style="color:#666; font-size:0.95rem;">Vui lòng nhập mật khẩu để truy cập:</p>
        </div>""", unsafe_allow_html=True)
        pwd_input = st.text_input("Mật khẩu:", type="password", placeholder="Nhập mật khẩu...", label_visibility="collapsed")
        if st.button("💖 Mở Khóa Trợ Lý", use_container_width=True, type="primary"):
            if pwd_input == config.WEB_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác! Hãy thử lại.")
    st.stop()

st.markdown(f"""
<div class="main-header">
  <h1>💖 TRỢ LÝ YÊU THƯƠNG 🌸</h1>
  <p>Dành riêng cho {her_name} • Đồng hành mỗi ngày trong học tập và sức khỏe!</p>
</div>
""", unsafe_allow_html=True)

# ======= SIDEBAR =======
with st.sidebar:
    st.markdown(f"### 💌 Xin chào {her_name}!")
    st.caption("Hôm nay em thấy thế nào? Nhớ uống đủ nước và giữ ấm nhé! 🍵")
    st.divider()
    selected_menu = st.radio("✨ Tính năng:", [
        "🎒 Lịch Học & Điểm Danh",
        "⏰ Deadline & AI Phân Tích",
        "🌸 Chu Kỳ Sinh Lý (AI)",
        "💊 Lịch Uống Thuốc & OCR",
        "⚙️ Cài Đặt & Telegram Bot"
    ])
    st.divider()
    st.success("🟢 AI & Scheduler: Đang chạy")
    st.caption("🤖 Tra cứu 2 chiều qua Telegram: Đang bật\n⏱️ Tự động quét mỗi 60 giây • Offline 100%")
    st.divider()
    if st.button("🔒 Khóa màn hình", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ====================================================================
# TAB 1: LỊCH HỌC & ĐIỂM DANH
# ====================================================================
if selected_menu == "🎒 Lịch Học & Điểm Danh":
    st.subheader("🎒 Lịch Học & Điểm Danh Chuyên Cần")

    tab_add, tab_att, tab_view = st.tabs(["➕ Thêm Môn Học", "📝 Điểm Danh Hôm Nay", "📊 Toàn Bộ Lịch Học"])

    # ---------- TAB: THÊM MÔN HỌC ----------
    with tab_add:
        st.markdown('<p class="hint-text">Điền thông tin bên dưới để lưu một môn học vào lịch tuần. Chỉ các trường có (*) là bắt buộc.</p>', unsafe_allow_html=True)

        # BƯỚC 1: Tên môn
        st.markdown('<span class="step-label">1</span> <b>Tên môn học</b>', unsafe_allow_html=True)
        subj_name = st.text_input(
            label="ten_mon",
            placeholder="VD: Lập trình Web, Tiếng Anh B2, Kinh tế vĩ mô...",
            label_visibility="collapsed",
            help="Nhập đúng tên môn học trên thời khóa biểu của em"
        )

        st.markdown('<span class="step-label">2</span> <b>Lịch học trong tuần</b>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            day_opts = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            day_select = st.selectbox("Ngày học", day_opts,
                help="Chọn thứ mà môn này được dạy mỗi tuần")
        with c2:
            category = st.selectbox("Loại môn", ["Môn lý thuyết", "Môn đồ án/bài tập lớn", "Môn ngoại ngữ"],
                help="Phân loại giúp lọc và nhắc nhở chính xác hơn")

        st.markdown('<span class="step-label">3</span> <b>Thời gian học</b> <span style="color:#888; font-size:0.85rem;">(gõ giờ theo định dạng HH:MM, VD: 07:30)</span>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            start_str = st.text_input("Giờ bắt đầu (*)", value="07:30",
                placeholder="07:30",
                help="Giờ bắt đầu buổi học. Nhập theo dạng HH:MM (VD: 07:30, 13:00, 17:30)")
        with c4:
            end_str = st.text_input("Giờ kết thúc (*)", value="11:00",
                placeholder="11:00",
                help="Giờ kết thúc buổi học. Bot sẽ nhắc em trước 30 phút trước giờ này")

        # Quick-fill gợi ý ca học phổ biến
        st.markdown('<p class="hint-text">⚡ Gợi ý ca học nhanh:</p>', unsafe_allow_html=True)
        qc1, qc2, qc3, qc4, qc5 = st.columns(5)
        if qc1.button("Ca 1\n07:30-11:00", use_container_width=True): start_str = "07:30"; end_str = "11:00"
        if qc2.button("Ca 2\n11:30-15:00", use_container_width=True): start_str = "11:30"; end_str = "15:00"
        if qc3.button("Ca 3\n13:00-16:30", use_container_width=True): start_str = "13:00"; end_str = "16:30"
        if qc4.button("Ca 4\n15:30-19:00", use_container_width=True): start_str = "15:30"; end_str = "19:00"
        if qc5.button("Ca tối\n18:00-21:00", use_container_width=True): start_str = "18:00"; end_str = "21:00"

        st.markdown('<span class="step-label">4</span> <b>Thông tin phòng học & số buổi</b>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            room = st.text_input("Phòng học", placeholder="VD: A2-301, Zoom, Google Meet...",
                help="Tên phòng học hoặc link Zoom nếu học online. Có thể bỏ trống.")
        with c6:
            total_sess = st.number_input("Tổng số buổi cả học kỳ", min_value=5, max_value=45, value=15,
                help="Thường là 15 buổi/học kỳ. Dùng để tính % vắng mặt và cảnh báo cấm thi (ngưỡng 20%)")

        notes = ""
        with st.expander("📝 Thêm ghi chú đặc biệt cho môn này (không bắt buộc)"):
            notes = st.text_area("Ghi chú",
                placeholder="VD: Nhớ mang máy tính, chuẩn bị bài thuyết trình tuần 3, giảng viên hay kiểm tra đầu giờ...",
                help="Ghi chú này sẽ được kèm trong tin nhắn nhắc lịch học qua Telegram",
                height=90)


        # Preview trước khi lưu
        if subj_name.strip():
            st.markdown(f"""
            <div class="preview-box">
                <b>👁️ Xem trước trước khi lưu:</b><br>
                📚 Môn học: <b>{subj_name}</b> &nbsp;|&nbsp; 🏷️ {category}<br>
                📅 <b>{day_select}</b> &nbsp;|&nbsp; 🕒 <b>{start_str} → {end_str}</b> &nbsp;|&nbsp; 📍 {room or "(Chưa điền phòng)"}<br>
                📋 Tổng <b>{total_sess} buổi</b> cả học kỳ &nbsp;|&nbsp; Ngưỡng cấm thi: <b>{int(total_sess*0.2)} buổi vắng</b>
            </div>
            """, unsafe_allow_html=True)

        if st.button("💖 Lưu Môn Học Này Vào Lịch", use_container_width=True, type="primary"):
            err = []
            if not subj_name.strip(): err.append("Chưa nhập tên môn học")
            try: datetime.strptime(start_str, "%H:%M")
            except: err.append(f"Giờ bắt đầu '{start_str}' chưa đúng định dạng HH:MM")
            try: datetime.strptime(end_str, "%H:%M")
            except: err.append(f"Giờ kết thúc '{end_str}' chưa đúng định dạng HH:MM")

            if err:
                for e in err: st.error(f"⚠️ {e}")
            else:
                day_idx = day_opts.index(day_select)
                database.add_schedule(subj_name.strip(), day_idx, day_select, start_str, end_str,
                                      room.strip(), category, notes.strip() if notes else "", int(total_sess))
                st.success(f"✅ Đã lưu môn '{subj_name}' vào lịch {day_select} {start_str}-{end_str}!")
                st.balloons()
                st.rerun()

    # ---------- TAB: ĐIỂM DANH ----------
    with tab_att:
        all_scheds = database.get_all_schedules()
        if not all_scheds:
            st.info("📭 Chưa có môn học nào. Hãy thêm môn ở tab **➕ Thêm Môn Học** trước nhé!")
        else:
            st.markdown('<p class="hint-text">Chọn môn học, ngày học và đánh dấu trạng thái tham dự. Hệ thống sẽ tự tính % chuyên cần và cảnh báo cấm thi.</p>', unsafe_allow_html=True)

            sched_labels = [f"{s['subject_name']} ({s['day_name']} {s['start_time']}-{s['end_time']})" for s in all_scheds]
            sched_ids    = [s["id"] for s in all_scheds]

            sel_idx = st.selectbox("Chọn môn học cần điểm danh:", sched_labels,
                help="Chọn đúng môn học và buổi học cần ghi nhận")
            sel_id = sched_ids[sched_labels.index(sel_idx)]

            ca1, ca2, ca3 = st.columns(3)
            with ca1:
                att_date = st.date_input("Ngày học:", value=date.today(),
                    help="Ngày diễn ra buổi học cần điểm danh")
            with ca2:
                att_status = st.selectbox("Trạng thái tham dự:", ["Đã đi học", "Vắng mặt", "Học Online"],
                    help="Đã đi học = buổi bình thường | Vắng mặt = không đến | Học Online = học qua Zoom/Meet")
            with ca3:
                att_note = st.text_input("Lý do / ghi chú:", placeholder="VD: Bệnh, kiểm tra 15 phút...",
                    help="Không bắt buộc. Giúp ghi nhớ chi tiết mỗi buổi học")

            # Hiện stats trước khi bấm
            stats = database.get_attendance_stats(sel_id)
            cols_s = st.columns(4)
            cols_s[0].metric("Đã đi học", f"{stats['attended']} buổi")
            cols_s[1].metric("Vắng mặt", f"{stats['absent']} buổi",
                delta=f"{stats['absent_rate']}%", delta_color="inverse")
            cols_s[2].metric("Học Online", f"{stats['online']} buổi")
            cols_s[3].metric("Tổng quy định", f"{stats['total']} buổi")

            if stats["is_warning"]:
                st.error(f"🚨 **NGUY CƠ CẤM THI!** Đã vắng {stats['absent']}/{stats['total']} buổi ({stats['absent_rate']}%). Ngưỡng cho phép: 20% = {int(stats['total']*0.2)} buổi.")
            else:
                buoi_con_duoc_vang = int(stats['total']*0.2) - stats['absent']
                st.success(f"✅ Chuyên cần tốt! Còn được vắng tối đa **{buoi_con_duoc_vang}** buổi nữa trước khi bị cảnh báo cấm thi.")

            if st.button("📝 Ghi Nhận Điểm Danh Buổi Này", use_container_width=True, type="primary"):
                database.log_attendance(sel_id, att_date.strftime("%Y-%m-%d"), att_status, att_note)
                st.success(f"✅ Đã ghi nhận: **{att_status}** ngày {att_date.strftime('%d/%m/%Y')}!")
                st.rerun()

    # ---------- TAB: XEM TOÀN BỘ ----------
    with tab_view:
        all_scheds = database.get_all_schedules()
        if not all_scheds:
            st.info("Chưa có môn học nào.")
        else:
            rows = []
            for s in all_scheds:
                stt = database.get_attendance_stats(s["id"])
                rows.append({
                    "ID": s["id"], "Tên Môn": s["subject_name"], "Thứ": s["day_name"],
                    "Thời Gian": f"{s['start_time']}-{s['end_time']}", "Phòng": s["room"] or "-",
                    "Loại": s["category"],
                    "Vắng / Tổng": f"{stt['absent']}/{stt['total']} ({stt['absent_rate']}%)",
                    "Cấm Thi": "🚨 Nguy cơ!" if stt['is_warning'] else "✅ An toàn"
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander("🗑️ Xóa môn học"):
                del_label = st.selectbox("Chọn môn cần xóa:",
                    [f"ID {s['id']}: {s['subject_name']} ({s['day_name']})" for s in all_scheds])
                del_id = int(del_label.split(":")[0].replace("ID","").strip())
                if st.button("Xác nhận xóa", type="primary"):
                    database.delete_schedule(del_id)
                    st.success("Đã xóa!")
                    st.rerun()

# ====================================================================
# TAB 2: DEADLINE & AI
# ====================================================================
elif selected_menu == "⏰ Deadline & AI Phân Tích":
    st.subheader("⏰ Quản Lý Deadline & AI Dự Đoán Rủi Ro")

    tab_add_t, tab_list_t, tab_ai_t = st.tabs(["➕ Thêm Deadline", "📋 Danh Sách Task", "🤖 Kiểm Tra AI Nhanh"])

    with tab_add_t:
        all_scheds = database.get_all_schedules()
        subj_list = list(set([s["subject_name"] for s in all_scheds])) if all_scheds else []

        st.markdown('<p class="hint-text">Nhập thông tin bài tập / đồ án để hệ thống tự động theo dõi và nhắc nhở qua Telegram.</p>', unsafe_allow_html=True)

        st.markdown('<span class="step-label">1</span> <b>Thông tin bài tập</b>', unsafe_allow_html=True)
        c1, c2 = st.columns([2,1])
        with c1:
            task_name = st.text_input("Tên bài tập / đồ án (*)",
                placeholder="VD: Báo cáo đồ án SE2033, Bài tập nhóm chương 4...",
                help="Đặt tên rõ ràng để dễ nhận biết trong danh sách và tin nhắn nhắc nhở")
        with c2:
            if subj_list:
                subj_task = st.selectbox("Thuộc môn học:", subj_list,
                    help="Chọn môn mà bài tập này thuộc về (được lấy từ danh sách môn học đã nhập)")
            else:
                subj_task = st.text_input("Thuộc môn học:", placeholder="VD: Công nghệ phần mềm",
                    help="Nhập tên môn học (hoặc thêm môn vào tab Lịch Học trước)")

        st.markdown('<span class="step-label">2</span> <b>Thời hạn nộp bài (Deadline)</b>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        with d1:
            due_date = st.date_input("Ngày hết hạn (*)", value=date.today() + timedelta(days=3),
                help="Ngày nộp bài cuối cùng. Hệ thống sẽ nhắc nhở ở các mốc 24h, 12h và 3h trước deadline")
        with d2:
            due_hour = st.select_slider("Giờ hết hạn (*)",
                options=["00:00","01:00","02:00","06:00","07:00","08:00","09:00","10:00",
                         "11:00","11:59","12:00","13:00","14:00","15:00","16:00","17:00",
                         "18:00","19:00","20:00","21:00","22:00","23:00","23:59"],
                value="23:59",
                help="Hầu hết deadline nộp bài là 23:59. Nếu nộp trên Moodle hoặc mail hãy kiểm tra lại giờ quy định")

        st.markdown('<span class="step-label">3</span> <b>Khối lượng công việc</b>', unsafe_allow_html=True)
        est_hours = st.slider(
            "Ước tính cần bao nhiêu giờ để làm xong?",
            min_value=0.5, max_value=24.0, value=3.0, step=0.5,
            help="Thành thật ước tính nhé! Con số này giúp AI tính xác suất trễ hạn chính xác hơn. Nếu chưa biết, hãy ước cao hơn một chút để an toàn."
        )

        # Thông tin preview + AI nhanh
        if task_name.strip():
            deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
            deadline_dt  = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            diff_h = (deadline_dt - datetime.now()).total_seconds() / 3600.0
            today_wd = datetime.now().weekday()
            classes_today = len(database.get_schedules_by_day(today_wd))

            if diff_h > 0:
                quick_ai = deadline_ml.predict_deadline_risk(task_name, classes_today, diff_h, est_hours)
                risk_color = "#d81159" if quick_ai["risk_percentage"] >= 70 else ("#d97706" if quick_ai["risk_percentage"] >= 40 else "#0d8a52")
                st.markdown(f"""
                <div class="preview-box">
                    <b>👁️ Xem trước:</b><br>
                    📌 <b>{task_name}</b> &nbsp;|&nbsp; 📖 {subj_task}<br>
                    ⏳ Deadline: <b>{due_date.strftime('%d/%m/%Y')} lúc {due_hour}</b> (còn <b>{diff_h:.1f} giờ</b>)<br>
                    ⏱️ Ước tính cần: <b>{est_hours}h</b><br>
                    🤖 AI đánh giá rủi ro ngay hôm nay: <b style="color:{risk_color};">{quick_ai['risk_percentage']}% — {quick_ai['warning_level']}</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Ngày deadline đã qua rồi! Hãy chọn lại ngày đúng nhé.")

        if st.button("🚀 Lưu Task & Bắt Đầu Theo Dõi", use_container_width=True, type="primary"):
            if not task_name.strip():
                st.error("Chưa nhập tên bài tập!")
            elif not subj_task or not str(subj_task).strip():
                st.error("Chưa chọn môn học!")
            else:
                deadline_str = f"{due_date.strftime('%Y-%m-%d')} {due_hour}"
                database.add_task(task_name.strip(), str(subj_task), deadline_str, float(est_hours), "Chưa làm")
                st.success(f"✅ Đã lưu task '{task_name}'! Bot Telegram sẽ nhắc nhở em đúng các mốc thời gian.")
                st.rerun()

    with tab_list_t:
        tasks = database.get_all_tasks()
        if not tasks:
            st.info("🎉 Hiện tại không có deadline nào. Em được nghỉ ngơi rồi!")
        else:
            now = datetime.now()
            today_wd = now.weekday()
            classes_today = len(database.get_schedules_by_day(today_wd))

            filter_status = st.segmented_control(
                "Lọc theo trạng thái:", 
                ["Tất cả", "Chưa làm", "Đang làm", "Đã hoàn thành"],
                default="Tất cả"
            ) if hasattr(st, "segmented_control") else st.selectbox("Lọc:", ["Tất cả","Chưa làm","Đang làm","Đã hoàn thành"])

            for t in tasks:
                if filter_status and filter_status != "Tất cả" and t["status"] != filter_status:
                    continue
                d_dt = datetime.strptime(t["deadline"], "%Y-%m-%d %H:%M")
                diff_h = (d_dt - now).total_seconds() / 3600.0
                pred = deadline_ml.predict_deadline_risk(t["task_name"], classes_today, max(0.1,diff_h), t["estimated_hours"])

                badge_cls = "badge-safe" if t["status"]=="Đã hoàn thành" else ("badge-warn" if t["status"]=="Đang làm" else "badge-danger")
                risk_icon = "🔴" if pred["risk_percentage"]>=70 else ("🟡" if pred["risk_percentage"]>=40 else "🟢")

                with st.container():
                    st.markdown(f"""<div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                          <span style="font-weight:700;font-size:1.05rem;">📌 {t['task_name']}</span>
                          <span class="{badge_cls}">{t['status']}</span>
                        </div>
                        📖 {t['subject_name']} &nbsp;|&nbsp; ⏳ Hạn: <b>{t['deadline']}</b> (còn <b>{max(0,diff_h):.1f}h</b>) &nbsp;|&nbsp; ⏱️ {t['estimated_hours']}h<br>
                        {risk_icon} <b>AI Rủi ro:</b> {pred['risk_percentage']}% — {pred['warning_message']}
                    </div>""", unsafe_allow_html=True)
                    b1,b2,b3,b4 = st.columns(4)
                    if b1.button("⏳ Chưa làm", key=f"td_{t['id']}"): database.update_task_status(t["id"],"Chưa làm"); st.rerun()
                    if b2.button("🔨 Đang làm",  key=f"tp_{t['id']}"): database.update_task_status(t["id"],"Đang làm"); st.rerun()
                    if b3.button("🎉 Đã xong",   key=f"td2_{t['id']}"): database.update_task_status(t["id"],"Đã hoàn thành"); st.rerun()
                    if b4.button("🗑️ Xóa",        key=f"del_{t['id']}", type="secondary"): database.delete_task(t["id"]); st.rerun()

    with tab_ai_t:
        st.markdown("**Thử nghiệm AI dự đoán rủi ro với thông số tùy chỉnh:**")
        st.markdown('<p class="hint-text">Công cụ kiểm tra nhanh — Không cần lưu vào CSDL.</p>', unsafe_allow_html=True)
        ai_name = st.text_input("Tên bài tập:", value="Bài tập thử nghiệm")
        c1,c2,c3 = st.columns(3)
        with c1:
            ai_classes = st.number_input("Số ca học hôm đó:", 0, 4, 2,
                help="Mỗi ca học chiếm khoảng 2-3 giờ thực tế, làm giảm thời gian rảnh")
        with c2:
            ai_free = st.number_input("Số giờ rảnh còn lại (h):", 0.5, 48.0, 6.0, step=0.5,
                help="Tổng số giờ rảnh (không tính giờ học, giờ ngủ, đi lại) cho đến khi hết deadline")
        with c3:
            ai_load = st.number_input("Khối lượng cần làm (h):", 0.5, 20.0, 4.0, step=0.5,
                help="Ước tính thực tế số giờ cần để hoàn thành bài tập này")

        r = deadline_ml.predict_deadline_risk(ai_name, int(ai_classes), ai_free, ai_load)
        st.metric("Xác suất trễ hạn", f"{r['risk_percentage']}%", delta=r['warning_level'], delta_color="inverse")
        if r["risk_percentage"] >= 70:   st.error(r["warning_message"])
        elif r["risk_percentage"] >= 40: st.warning(r["warning_message"])
        else:                            st.success(r["warning_message"])

# ====================================================================
# TAB 3: CHU KỲ SINH LÝ
# ====================================================================
elif selected_menu == "🌸 Chu Kỳ Sinh Lý (AI)":
    st.subheader("🌸 Theo Dõi & AI Dự Đoán Chu Kỳ Kinh Nguyệt")

    pred = menstrual_ml.predict_next_cycle()

    # --- Trạng thái hiện tại nổi bật ---
    if pred.get("has_data"):
        days_left = pred["days_left"]
        if days_left <= 0:
            st.error(f"💖 Hôm nay hoặc đã qua ngày dự kiến bắt đầu kỳ mới ({pred['predicted_next_date']}). Em nhớ cập nhật nhé!")
        elif days_left <= 4:
            st.warning(f"🌸 Đang vào giai đoạn PMS! Còn **{days_left} ngày** nữa đến kỳ mới (dự kiến {pred['predicted_next_date']}). Em nhớ giữ ấm bụng, uống nước ấm nhé!")
        else:
            st.success(f"✨ Bình thường — Còn **{days_left} ngày** đến chu kỳ tiếp theo (dự kiến {pred['predicted_next_date']})")
    else:
        st.info("👋 Chưa có dữ liệu. Hãy bấm nút bên dưới để bắt đầu theo dõi!")

    st.divider()

    col_a, col_b = st.columns([1.2, 1])

    with col_a:
        st.markdown("""<div class="card">
            <div class="section-title">💖 Ghi Nhận Chu Kỳ Mới</div>
            <p style="font-size:0.95rem; color:#555; margin-bottom:16px;">
            Mỗi lần bắt đầu kỳ mới, em chỉ cần bấm 1 nút bên dưới (hoặc chọn ngày khác nếu quên ghi). 
            AI sẽ tự động học cơ địa riêng của em và dự đoán ngày tới chính xác hơn theo thời gian!
            </p>
        </div>""", unsafe_allow_html=True)

        if st.button("💖 HÔM NAY BẮT ĐẦU KỲ MỚI", use_container_width=True, type="primary"):
            database.add_menstrual_record(date.today().strftime("%Y-%m-%d"))
            menstrual_ml.retrain_model()
            st.balloons()
            st.success("Đã ghi nhận! AI đã cập nhật dữ liệu cơ địa của em.")
            st.rerun()

        st.markdown('<p class="hint-text">Hoặc chọn ngày khác nếu quên ghi:</p>', unsafe_allow_html=True)
        with st.expander("📅 Chọn ngày bắt đầu khác"):
            custom_d = st.date_input("Ngày bắt đầu thực tế:", value=date.today(),
                help="Dùng khi em quên bấm nút vào đúng ngày đó")
            custom_len = st.number_input("Độ dài chu kỳ lần này (ngày):", 21, 45, 28,
                help="Nếu không biết chính xác, giữ nguyên 28 ngày. AI sẽ tự tính từ dữ liệu sau.")
            if st.button("Lưu ngày này", use_container_width=True):
                database.add_menstrual_record(custom_d.strftime("%Y-%m-%d"), cycle_length=int(custom_len))
                menstrual_ml.retrain_model()
                st.success("Đã lưu và cập nhật AI!")
                st.rerun()

        if pred.get("has_data"):
            st.markdown(f"""<div class="preview-box">
                <b>🔮 AI Dự Đoán Cơ Địa Của Em:</b><br>
                • Chu kỳ dự kiến: <b>{pred['predicted_length']} ngày</b> (học từ {pred['history_count']} lần ghi nhận)<br>
                • Kỳ gần nhất: <b>{pred['latest_start_date']}</b><br>
                • Kỳ tiếp theo: <b>{pred['predicted_next_date']}</b><br>
                • PMS bắt đầu: <b>{pred['pms_start_date']}</b>
            </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("""<div class="card">
            <div class="section-title">🍓 Cơ Chế Thông Báo Kép</div>
            <p style="font-size:0.92rem; color:#555; line-height:1.65;">
            <b>🌸 Nhắn cho Em (Telegram):</b><br>
            — Trước 3 ngày: Nhắc giữ ấm bụng, uống nước ấm, hạn chế đồ lạnh<br>
            — Đúng ngày dự kiến: Nhắc chuẩn bị đồ dùng cá nhân<br><br>
            <b>🍓 Nhắn BÍ MẬT cho Bạn:</b><br>
            — Trước 4 ngày: Bot tự nhắn riêng cho bạn:<br>
            <i>"Sếp ơi! Khoảng 4 ngày nữa là đến kỳ của em ấy rồi. Nhớ chuẩn bị túi sưởi, đồ ngọt và kiên nhẫn hơn nhé! 🧸🍫"</i>
            </p>
        </div>""", unsafe_allow_html=True)

        if st.button("🔄 Huấn Luyện Lại AI (Retrain)", use_container_width=True):
            menstrual_ml.retrain_model()
            st.success("AI đã được cập nhật lại!")

    # Lịch sử
    st.divider()
    st.markdown("#### 📜 Lịch Sử Chu Kỳ Đã Ghi Nhận")
    records = database.get_all_menstrual_records()
    if records:
        df_m = pd.DataFrame(records)[["id","start_date","cycle_length","period_length","notes"]]
        df_m.columns = ["ID","Ngày Bắt Đầu","Độ Dài CK (ngày)","Số Ngày Đèn Đỏ","Ghi Chú"]
        st.dataframe(df_m, use_container_width=True, hide_index=True)

        with st.expander("🗑️ Xóa bản ghi nhập nhầm"):
            del_ids = [r["id"] for r in records]
            del_m_id = st.selectbox("Chọn ID cần xóa:", del_ids,
                format_func=lambda x: f"ID {x}: {next(r['start_date'] for r in records if r['id']==x)}")
            if st.button("Xóa bản ghi này", type="primary"):
                database.delete_menstrual_record(del_m_id)
                menstrual_ml.retrain_model()
                st.success("Đã xóa!")
                st.rerun()
    else:
        st.caption("Chưa có bản ghi nào.")

# ====================================================================
# TAB 4: LỊCH UỐNG THUỐC
# ====================================================================
elif selected_menu == "💊 Lịch Uống Thuốc & OCR":
    st.subheader("💊 Nhắc Lịch Uống Thuốc & Đọc Đơn Thuốc Bằng Ảnh")

    tab_today, tab_add_m, tab_list_m = st.tabs(["🔔 Lịch Hôm Nay", "➕ Thêm Lịch Thuốc", "📋 Danh Sách Thuốc"])

    with tab_today:
        today_str = date.today().strftime("%Y-%m-%d")
        today_meds = database.get_today_medicine_status(today_str)

        if not today_meds:
            st.info("💖 Hôm nay em không có lịch uống thuốc nào. Mong em luôn khỏe mạnh!")
        else:
            total = len(today_meds)
            taken_count = sum(1 for m in today_meds if m["taken"])
            st.progress(taken_count/total, text=f"Đã uống {taken_count}/{total} liều hôm nay")

            for item in today_meds:
                icon = "✅" if item["taken"] else "⏳"
                badge = "badge-safe" if item["taken"] else "badge-warn"
                status_txt = "Đã uống" if item["taken"] else "Chưa uống"
                with st.container():
                    st.markdown(f"""<div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                          <span style="font-weight:700;">{icon} {item['medicine_name']} — {item['time_slot']}</span>
                          <span class="{badge}">{status_txt}</span>
                        </div>
                        <div style="color:#666;font-size:0.92rem;margin:6px 0;">
                          💊 Liều: <b>{item['dosage']}</b> &nbsp;|&nbsp; 📅 Ngày {item['day_number']}/{item['total_days']}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if not item["taken"]:
                        c_take, c_test = st.columns([3, 2])
                        with c_take:
                            if st.button(f"✅ Đánh dấu Đã uống lúc {item['time_slot']}", key=f"take_{item['medicine_id']}_{item['time_slot']}", use_container_width=True):
                                database.log_medicine_taken(item["medicine_id"], today_str, item["time_slot"])
                                st.success("Bé giỏi quá! 🌸")
                                st.rerun()
                        with c_test:
                            if st.button(f"📲 Test gửi nhắc qua Telegram", key=f"test_med_{item['medicine_id']}_{item['time_slot']}", use_container_width=True, help="Bấm để Bot gửi ngay tin nhắn nhắc nhở liều này vào Telegram"):
                                msg = (
                                    f"💊 <b>[TEST NHẮC UỐNG THUỐC]</b> 🌸\n\n"
                                    f"🏷️ Tên thuốc: <b>{item['medicine_name']}</b>\n"
                                    f"🥄 Liều lượng: <b>{item['dosage']}</b>\n"
                                    f"🕒 Khung giờ: <b>{item['time_slot']}</b> (Ngày {item['day_number']}/{item['total_days']})\n\n"
                                    f"<i>Uống thuốc đúng giờ để mau khỏe nha cô bé! Uống xong nhớ vào app bấm 'Đã uống' nhé! 🍵</i>"
                                )
                                res = notifier.notify_her(msg, photo_path=item.get("image_path"))
                                if res:
                                    st.success("✅ Đã gửi tin nhắc qua Telegram!")
                                else:
                                    st.error("❌ Gửi không thành công. Hãy kiểm tra Bot Token & Chat ID!")

    with tab_add_m:
        st.markdown('<p class="hint-text">Nhập thông tin đơn thuốc để hệ thống tự nhắc uống đúng giờ qua Telegram. Bạn có thể tải ảnh đơn thuốc lên để AI đọc tự động!</p>', unsafe_allow_html=True)

        ocr_data = {"name": "", "dosage": "1 viên (sau ăn)", "times": "08:00, 19:30", "days_count": 5}
        saved_img_path = ""

        with st.expander("📷 Tải Ảnh Đơn Thuốc / Vỏ Thuốc (AI đọc tự động)"):
            uploaded = st.file_uploader("Chọn ảnh:", type=["jpg","jpeg","png"],
                help="Chụp rõ mặt trước vỏ hộp thuốc hoặc tờ đơn thuốc của bác sĩ. AI sẽ tự nhận diện tên thuốc, liều lượng và các mốc giờ uống!")
            if uploaded:
                col_img, col_res = st.columns(2)
                with col_img:
                    st.image(uploaded, caption="Ảnh đã tải lên", use_container_width=True)
                fname = f"med_{int(datetime.now().timestamp())}_{uploaded.name}"
                fpath = config.UPLOADS_DIR / fname
                with open(fpath,"wb") as f: f.write(uploaded.getbuffer())
                saved_img_path = str(fpath)
                with col_res:
                    if st.button("🔍 Bấm để AI đọc ảnh và điền tự động", use_container_width=True):
                        with st.spinner("AI đang nhận diện chữ trong ảnh..."):
                            ocr_data = medicine_ocr.process_medicine_image(saved_img_path)
                        st.success("Đã nhận diện xong! Kiểm tra lại thông tin bên dưới nhé.")
                        if ocr_data.get("raw_text"):
                            with st.expander("Xem văn bản thô trích xuất từ ảnh"):
                                st.text(ocr_data["raw_text"])

        st.markdown('<span class="step-label">1</span> <b>Thông tin thuốc</b>', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            med_name   = st.text_input("Tên thuốc (*)", value=ocr_data.get("name",""),
                placeholder="VD: Panadol Extra 500mg, Vitamin C, Berberin...",
                help="Nhập đúng tên thuốc để dễ nhận biết trong thông báo và ảnh thumbnail")
        with m2:
            med_dosage = st.text_input("Liều lượng (*)", value=ocr_data.get("dosage","1 viên (sau ăn)"),
                placeholder="VD: 1 viên sau ăn, 2 viên khi sốt, 5ml pha nước ấm...",
                help="Mô tả cách uống rõ ràng. Thông tin này sẽ được gửi trong tin nhắn nhắc nhở")

        st.markdown('<span class="step-label">2</span> <b>Lịch uống trong ngày</b>', unsafe_allow_html=True)
        st.markdown('<p class="hint-text">Nhập các khung giờ uống thuốc, cách nhau bởi dấu phẩy. VD: 08:00, 12:30, 20:00</p>', unsafe_allow_html=True)

        # Quick presets
        preset_col = st.columns(4)
        preset_val = ocr_data.get("times","08:00, 19:30")
        if preset_col[0].button("1 lần/ngày\n(Sáng)", use_container_width=True): preset_val = "08:00"
        if preset_col[1].button("2 lần/ngày\n(S+T)", use_container_width=True): preset_val = "08:00, 20:00"
        if preset_col[2].button("3 lần/ngày\n(S+T+T)", use_container_width=True): preset_val = "08:00, 13:00, 20:00"
        if preset_col[3].button("4 lần/ngày\n(S+T+C+T)", use_container_width=True): preset_val = "07:30, 12:00, 17:00, 21:00"

        med_times = st.text_input("Các khung giờ uống (*)", value=preset_val,
            help="Nhập đúng định dạng HH:MM, phân cách bởi dấu phẩy. VD: 08:00, 12:30, 20:00")

        st.markdown('<span class="step-label">3</span> <b>Thời gian điều trị</b>', unsafe_allow_html=True)
        m3, m4 = st.columns(2)
        with m3:
            med_days = st.number_input("Uống trong bao nhiêu ngày (*)", 1, 60, int(ocr_data.get("days_count",5)),
                help="Số ngày cần uống theo đơn. Sau hết số ngày này, thuốc sẽ tự kết thúc và không nhắc nữa")
        with m4:
            med_start = st.date_input("Ngày bắt đầu uống (*)", value=date.today(),
                help="Thường là hôm nay. Chỉ thay đổi nếu em đã uống từ mấy ngày trước mà quên nhập")

        if med_name.strip():
            st.markdown(f"""<div class="preview-box">
                <b>👁️ Xem trước lịch uống thuốc:</b><br>
                💊 <b>{med_name}</b> — {med_dosage}<br>
                🕒 Giờ uống: <b>{med_times}</b><br>
                📅 Từ <b>{med_start.strftime('%d/%m/%Y')}</b> trong <b>{med_days} ngày</b> liên tiếp<br>
                📬 Bot Telegram sẽ nhắc em đúng các giờ trên kèm theo ảnh thuốc (nếu có tải lên)
            </div>""", unsafe_allow_html=True)

        if st.button("💊 Lưu Lịch Uống Thuốc Này", use_container_width=True, type="primary"):
            if not med_name.strip():
                st.error("Chưa nhập tên thuốc!")
            else:
                database.add_medicine(med_name.strip(), med_dosage.strip(), med_times.strip(),
                                      int(med_days), med_start.strftime("%Y-%m-%d"), saved_img_path)
                st.success(f"✅ Đã lưu lịch uống '{med_name}'! Bot sẽ nhắc em đúng giờ kèm ảnh thuốc.")
                st.rerun()

    with tab_list_m:
        all_meds = database.get_all_medicines()
        if not all_meds:
            st.info("Chưa có thuốc nào được thêm.")
        else:
            for m in all_meds:
                end_date = datetime.strptime(m["start_date"],"%Y-%m-%d").date() + timedelta(days=m["days_count"])
                is_active = date.today() <= end_date and m["active"]
                badge = "badge-safe" if is_active else "badge-danger"
                label = "Đang điều trị" if is_active else "Đã kết thúc"
                st.markdown(f"""<div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                      <b>💊 {m['name']}</b>
                      <span class="{badge}">{label}</span>
                    </div>
                    <div style="color:#666;font-size:0.92rem;margin-top:6px;">
                      Liều: {m['dosage']} &nbsp;|&nbsp; Giờ: {m['times']} &nbsp;|&nbsp; {m['days_count']} ngày từ {m['start_date']}
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"🗑️ Xóa '{m['name']}'", key=f"del_med_{m['id']}"):
                    database.delete_medicine(m["id"])
                    st.rerun()

# ====================================================================
# TAB 5: CÀI ĐẶT
# ====================================================================
elif selected_menu == "⚙️ Cài Đặt & Telegram Bot":
    st.subheader("⚙️ Cấu Hình Telegram Bot & Thông Báo")

    cur = config.load_settings()

    st.markdown("""<div class="card">
        <div class="section-title">📋 Hướng dẫn nhanh lấy Bot Token & Chat ID (chỉ 3 phút)</div>
        <div style="font-size:0.93rem;line-height:1.75;">
        <b>Bước 1 — Tạo Bot Token:</b> Mở Telegram → tìm <b>@BotFather</b> → gửi <code>/newbot</code> → đặt tên bot → copy mã <b>HTTP API Token</b><br>
        <b>Bước 2 — Lấy Chat ID:</b> Tìm <b>@userinfobot</b> → bấm Start → bot trả về ID của bạn. Nhờ cô ấy làm tương tự để lấy ID của cô ấy.<br>
        <b>Bước 3 — Bấm Start với bot của bạn:</b> Cả hai cần vào bot vừa tạo và bấm <b>/start</b> một lần để bot được phép gửi tin.
        </div>
    </div>""", unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("#### 🤖 Telegram Bot")
        bot_token = st.text_input("Bot Token (*)",
            value=cur.get("telegram_bot_token",""),
            type="password",
            placeholder="VD: 7123456789:AAFxxx...",
            help="Lấy từ @BotFather. Giữ bí mật, không chia sẻ cho bất kỳ ai!")

        st.markdown("#### 💌 Chat ID")
        c1, c2 = st.columns(2)
        with c1:
            her_chat = st.text_input("Chat ID của Cô Ấy (*)",
                value=cur.get("telegram_her_chat_id",""),
                placeholder="VD: 987654321",
                help="Nhắn lịch học, deadline, thuốc, chu kỳ. Lấy bằng @userinfobot.")
            her_name_v = st.text_input("Tên hiển thị của Cô Ấy",
                value=cur.get("her_name","Em yêu 🌸"),
                help="Tên này xuất hiện trong các tin nhắn chào hỏi và thông báo")
        with c2:
            my_chat = st.text_input("Chat ID của Bạn (Secret Mode)",
                value=cur.get("telegram_my_chat_id",""),
                placeholder="VD: 123456789",
                help="Nhận thông báo BÍ MẬT trước 4 ngày kỳ kinh nguyệt của cô ấy. Chỉ mình bạn thấy!")
            my_name_v = st.text_input("Tên hiển thị của Bạn",
                value=cur.get("my_name","Anh 💖"),
                help="Xuất hiện trong các tin nhắn cá nhân")

        secret_on = st.toggle("🍓 Kích hoạt Secret Mode (Nhắn bí mật cho Bạn)",
            value=cur.get("secret_mode_enabled", True),
            help="Khi bật: Bot sẽ tự nhắn bí mật cho bạn trước 4 ngày chu kỳ kinh nguyệt của cô ấy")

        save_btn = st.form_submit_button("💾 Lưu Tất Cả Cài Đặt", use_container_width=True)
        if save_btn:
            cur.update({
                "telegram_bot_token": bot_token.strip(),
                "telegram_her_chat_id": her_chat.strip(),
                "telegram_my_chat_id": my_chat.strip(),
                "her_name": her_name_v.strip(),
                "my_name": my_name_v.strip(),
                "secret_mode_enabled": secret_on
            })
            if config.save_settings(cur):
                st.success("✅ Đã lưu cấu hình!")
                st.rerun()

    st.divider()
    st.markdown("#### 🧪 Kiểm Tra Kết Nối Telegram")

    t1, t2, t3 = st.columns(3)
    with t1:
        if st.button("📤 Gửi Test → Cô Ấy", use_container_width=True):
            res = notifier.notify_her("💖 Xin chào Em Yêu! Trợ Lý Yêu Thương đang hoạt động và luôn ở bên em! 🌸")
            if res:
                st.success("✅ Đã gửi tin nhắn test thành công!")
            else:
                st.error("❌ Gửi thất bại. Kiểm tra Bot Token và Chat ID, nhớ bấm /start với bot trên Telegram!")
    with t2:
        if st.button("🍓 Gửi Test Secret Mode", use_container_width=True):
            res2 = notifier.notify_you_secret("🍓 [SECRET MODE] Kênh bí mật hoạt động hoàn hảo rồi sếp ơi!")
            if res2:
                st.success("✅ Đã gửi Secret Mode thành công!")
            else:
                st.error("❌ Gửi thất bại. Kiểm tra Chat ID của Bạn và nhớ bấm /start với bot!")
    with t3:
        if st.button("🎉 Kích Hoạt Lời Chúc Mừng", use_container_width=True):
            cur = config.load_settings()
            cur["startup_greeting_sent"] = False
            config.save_settings(cur)
            scheduler.check_and_send_startup_greeting()
            st.success("Đã bắn lời chúc ngọt ngào tới Cô Ấy!")
