# 🌸 TRỢ LÝ YÊU THƯƠNG (HER PERSONAL ASSISTANT) v2.0 💖

> **Dành tặng Người yêu** • Chạy Offline/Local 100% • Bảo mật & Miễn phí trọn đời • Giao diện Streamlit Desktop ngọt ngào & Thông báo tự động qua Telegram Bot.

---

## 🌟 CÁC TÍNH NĂNG NỔI BẬT THEO TÀI LIỆU YÊU CẦU (SRS)

1. **🎒 Module 1: Quản Lý Lịch Học & Điểm Danh Chuyên Cần**
   - Quản lý thời khóa biểu theo thứ trong tuần, giờ học, phòng học, phân loại môn.
   - Điểm danh: Đã đi học, Vắng mặt, Học Online.
   - **Tự động cảnh báo nguy cơ cấm thi** khi tỷ lệ vắng mặt vượt quá **20%** số buổi quy định.
   - Tự động gửi tin nhắn Telegram trước giờ học **30 phút** kèm theo những lời dặn ấm áp (bình nước, sạc máy tính, áo khoác...).

2. **⏰ Module 2: Quản Lý Task, Deadline & AI Dự Đoán Rủi Ro**
   - Thêm bài tập, đồ án lớn với thời hạn và khối lượng giờ ước tính.
   - **AI Machine Learning (`RandomForestClassifier`)**: Dự đoán xác suất trễ hạn dựa trên số ca học trong ngày, số giờ rảnh còn lại và khối lượng công việc.
   - Tự động bắn tin nhắn Telegram nhắc nhở trước mốc: **24 giờ, 12 giờ và 3 giờ**.

3. **🌸 Module 3: Theo Dõi & AI Dự Đoán Chu Kỳ Kinh Nguyệt Cá Nhân Hóa**
   - Đánh dấu 1-click: *"💖 Hôm nay là ngày bắt đầu kỳ mới"*.
   - **AI Học Cơ Địa Riêng (`RandomForestRegressor`)**: Dự đoán chính xác số ngày chu kỳ tiếp theo và tự động huấn luyện lại (`retrain_model()`) khi có dữ liệu mới.
   - **Cơ chế Thông Báo Kép (Dual Notifications)**:
     - **Gửi cho Cô ấy**: Nhắc giữ ấm bụng, uống nước ấm giai đoạn PMS (trước 3-4 ngày) và dặn mang đồ cá nhân ngày bắt đầu.
     - **Gửi BÍ MẬT cho Bạn (Secret Mode)**: Trước 4 ngày, Bot tự động nhắn riêng cho bạn: *"Sếp ơi! Khoảng 4 ngày nữa là đến kỳ của em ấy rồi... nhớ chuẩn bị túi sưởi, đồ ngọt và kiên nhẫn hơn nhé! 🍓"*.

4. **💊 Module 4: Nhắc Lịch Uống Thuốc & Đọc Đơn Thuốc Bằng Ảnh (Local OCR)**
   - Đọc ảnh vỏ thuốc / đơn thuốc bằng OCR offline, tự động trích xuất tên thuốc (Panadol...), liều lượng (2 viên sau ăn...), các mốc giờ uống (sáng, trưa, tối...).
   - Bắn tin nhắn Telegram đúng giờ kèm **hình ảnh chụp vỏ thuốc** để cô ấy dễ nhận biết.
   - Giao diện có nút bấm *"💊 Đã uống liều này"* để xác nhận và ngắt nhắc nhở trong ngày.

5. **⚙️ Module 5: Daemon Scheduler & Chống Crash**
   - Tiến trình ngầm tự động quét CSDL mỗi **60 giây**.
   - Bắt lỗi rớt mạng/mất Wi-Fi bằng `try-except`, tự động thử lại mà không gây crash ứng dụng.

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
Du_an_bi_mat/
│
├── config.py             # Cấu hình Token Telegram, Chat ID, đường dẫn CSDL
├── database.py           # SQLite3 & CRUD (Lịch học, Task, Chu kỳ, Thuốc)
├── menstrual_ml.py       # ML Dự đoán chu kỳ (RandomForestRegressor)
├── deadline_ml.py        # ML Dự đoán rủi ro deadline (RandomForestClassifier)
├── medicine_ocr.py       # Local OCR quét ảnh vỏ thuốc & trích xuất từ khóa
├── notifier.py           # Gửi thông báo Telegram (chống crash, gửi ảnh, secret mode)
├── scheduler.py          # Daemon Thread kiểm tra CSDL thời gian thực định kỳ 60s
├── app.py                # Giao diện Desktop Streamlit Web App ngọt ngào
├── run_app.py            # Entry point khởi chạy song song Backend Scheduler & App
├── TroLyYeuThuong.bat    # File kích hoạt 1-click hoặc cài đặt tự khởi động Windows
├── requirements.txt      # Danh sách thư viện phụ thuộc
├── test_system.py        # Kịch bản kiểm thử toàn diện 100%
│
├── data/
│   ├── schedule_data.db  # CSDL SQLite lưu trữ toàn bộ dữ liệu
│   ├── settings.json     # Cài đặt cấu hình người dùng
│   └── uploads/          # Thư mục lưu ảnh chụp vỏ thuốc
│
└── models/
    ├── menstrual_model.pkl # Mô hình AI dự đoán chu kỳ đã export
    └── deadline_model.pkl  # Mô hình AI dự đoán rủi ro deadline đã export
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG

### 1. Khởi chạy Ứng dụng
Bạn chỉ cần nhấp đúp chuột vào file:
👉 **`TroLyYeuThuong.bat`**

Hoặc chạy lệnh từ terminal:
```bash
py -3.13 run_app.py
```
Hệ thống sẽ tự động khởi tạo CSDL, nạp mô hình AI, bật tiến trình ngầm Scheduler và mở giao diện ứng dụng trên trình duyệt!

---

### 2. Hướng dẫn Lấy Telegram Bot Token & Chat ID (Chỉ 2 phút)

1. **Tạo Bot Token**:
   - Mở Telegram, tìm kiếm bot **`@BotFather`**.
   - Gửi lệnh `/newbot` và đặt tên cho bot (VD: `TroLyYeuThuongBot`).
   - Copy mã **HTTP API Token** được cấp.
2. **Lấy Chat ID**:
   - Tìm kiếm bot **`@userinfobot`** trên Telegram và bấm `Start`. Bot sẽ trả về **Id** của bạn.
   - Nhờ cô ấy bấm `Start` với `@userinfobot` để lấy **Chat ID của Cô ấy**.
   - **QUAN TRỌNG**: Cả bạn và cô ấy cần vào bot bạn vừa tạo và bấm nút **Start** một lần để cho phép bot gửi tin nhắn.
3. **Nhập vào Ứng dụng**:
   - Mở ứng dụng, vào mục **⚙️ Cài Đặt & Telegram Bot**.
   - Dán Bot Token, Chat ID của Cô ấy và Chat ID của Bạn (Secret Mode), sau đó bấm **Lưu Cài Đặt**.
   - Bấm nút **Gửi Tin Nhắn Thử** để kiểm tra kết nối ngay lập tức!

---

### 3. Cài Đặt Tự Động Khởi Động Cùng Windows (Windows Startup)

Để phần mềm tự động chạy ngầm mỗi khi cô ấy mở máy tính:
1. Nhấn tổ hợp phím `Windows + R`, gõ `shell:startup` và nhấn `Enter`.
2. Chuột phải vào file `TroLyYeuThuong.bat` -> chọn **Show more options** -> **Create shortcut**.
3. Kéo shortcut vừa tạo vào thư mục Startup vừa mở ra.
4. Đổi tên shortcut thành: `Trợ Lý Yêu Thương 💖`.

---

### 4. Màn Bất Ngờ Khi Gửi Tặng (Quà 20/10)
- Bạn âm thầm nhập sẵn Thời khóa biểu học kỳ này của cô ấy vào mục **🎒 Lịch Học & Điểm Danh**.
- Cài sẵn shortcut vào Windows Startup.
- Khi cô ấy bật máy tính, phần mềm kích hoạt và con Bot Telegram sẽ tự động gửi tin nhắn chào mừng kèm lời chúc 20/10 ngọt ngào đầu tiên! 💐✨
