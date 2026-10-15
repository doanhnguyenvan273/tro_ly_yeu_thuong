import numpy as np
import joblib
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from config import MENSTRUAL_MODEL_PATH
import database

def generate_baseline_cycles_data():
    """Tạo bộ dữ liệu chu kỳ cơ bản của phụ nữ (trung bình 27-32 ngày) để huấn luyện mô hình ban đầu."""
    np.random.seed(42)
    n_samples = 400
    
    # Giả lập các chuỗi 3 chu kỳ liên tiếp: [cycle_t-2, cycle_t-1, cycle_t]
    # Cơ địa của mỗi cá nhân thường có tính ổn định quanh một mốc (ví dụ 28 ngày +- 2 ngày)
    base_means = np.random.uniform(26.0, 33.0, size=n_samples)
    
    X = []
    y = []
    for m in base_means:
        c1 = np.clip(np.random.normal(m, 1.5), 23, 38)
        c2 = np.clip(np.random.normal(m, 1.5), 23, 38)
        c3 = np.clip(np.random.normal(m, 1.5), 23, 38)
        c_next = np.clip(np.random.normal(m, 1.5), 23, 38)
        X.append([c1, c2, c3])
        y.append(c_next)
        
    return np.array(X), np.array(y)

def train_or_load_menstrual_model() -> RandomForestRegressor:
    """Tải hoặc khởi tạo mô hình RandomForestRegressor dự đoán chu kỳ."""
    if MENSTRUAL_MODEL_PATH.exists():
        try:
            model = joblib.load(MENSTRUAL_MODEL_PATH)
            return model
        except Exception:
            pass
            
    X, y = generate_baseline_cycles_data()
    model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X, y)
    
    MENSTRUAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MENSTRUAL_MODEL_PATH)
    return model

def retrain_model():
    """
    Tự động huấn luyện lại mô hình với dữ liệu chu kỳ thực tế của cô ấy.
    Được gọi tự động mỗi khi cô ấy thêm mới hoặc cập nhật chu kỳ.
    """
    records = database.get_all_menstrual_records()
    cycle_lengths = [r["cycle_length"] for r in records if r.get("cycle_length") and 15 <= r["cycle_length"] <= 60]
    
    X_base, y_base = generate_baseline_cycles_data()
    
    if len(cycle_lengths) >= 4:
        # Tạo thêm các mẫu từ dữ liệu thực tế của cô ấy
        user_X = []
        user_y = []
        for i in range(len(cycle_lengths) - 3):
            user_X.append(cycle_lengths[i:i+3])
            user_y.append(cycle_lengths[i+3])
            
        if user_X:
            # Gán trọng số cao hơn cho dữ liệu thực tế của cô ấy bằng cách nhân bản mẫu
            user_X_repeated = np.repeat(np.array(user_X), 25, axis=0)
            user_y_repeated = np.repeat(np.array(user_y), 25, axis=0)
            
            X_combined = np.vstack([X_base, user_X_repeated])
            y_combined = np.concatenate([y_base, user_y_repeated])
        else:
            X_combined, y_combined = X_base, y_base
    else:
        X_combined, y_combined = X_base, y_base
        
    model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_combined, y_combined)
    joblib.dump(model, MENSTRUAL_MODEL_PATH)
    return model

def predict_next_cycle() -> Dict[str, Any]:
    """
    Dự đoán chu kỳ tiếp theo dựa trên lịch sử của cô ấy.
    Trả về thông tin chi tiết:
    - predicted_length: Số ngày dự đoán của chu kỳ (VD: 28 ngày)
    - latest_start_date: Ngày bắt đầu gần nhất
    - predicted_next_date: Ngày dự kiến bắt đầu chu kỳ kế tiếp
    - pms_start_date: Ngày bắt đầu giai đoạn PMS (trước 4 ngày)
    - secret_alert_date: Ngày gửi thông báo bí mật cho Bạn (trước 4 ngày)
    - days_left: Số ngày còn lại đến kỳ tiếp theo
    - status_text: Trạng thái hiện tại
    """
    model = train_or_load_menstrual_model()
    records = database.get_all_menstrual_records()
    
    if not records:
        # Nếu chưa có bản ghi nào
        return {
            "has_data": False,
            "message": "Chưa có dữ liệu chu kỳ. Hãy nhấn nút 'Hôm nay là ngày bắt đầu kỳ mới' để AI bắt đầu học nhé!"
        }
        
    latest_record = records[-1]
    latest_start_date = datetime.strptime(latest_record["start_date"], "%Y-%m-%d").date()
    
    cycle_lengths = [r["cycle_length"] for r in records if r.get("cycle_length") and 15 <= r["cycle_length"] <= 60]
    
    if len(cycle_lengths) >= 3:
        # Lấy 3 chu kỳ gần nhất làm features
        features = np.array([cycle_lengths[-3:]])
        predicted_length = float(model.predict(features)[0])
        predicted_length = int(round(predicted_length))
    elif len(cycle_lengths) > 0:
        # Nếu chỉ có 1-2 chu kỳ, lấy trung bình kết hợp baseline 28
        avg_cycle = float(np.mean(cycle_lengths))
        predicted_length = int(round(0.7 * avg_cycle + 0.3 * 28))
    else:
        predicted_length = 28
        
    # Giới hạn hợp lý về sinh lý (21 - 40 ngày)
    predicted_length = max(21, min(45, predicted_length))
    
    predicted_next_date = latest_start_date + timedelta(days=predicted_length)
    pms_start_date = predicted_next_date - timedelta(days=4)
    secret_alert_date = predicted_next_date - timedelta(days=4)
    
    today = date.today()
    days_left = (predicted_next_date - today).days
    
    # Xác định trạng thái
    if days_left < 0:
        status_text = f"Đã quá ngày dự kiến {-days_left} ngày (Kỳ trước bắt đầu: {latest_start_date.strftime('%d/%m/%Y')})"
    elif days_left == 0:
        status_text = "💖 Hôm nay là ngày dự kiến bắt đầu chu kỳ mới!"
    elif 1 <= days_left <= 4:
        status_text = f"🌸 Đang ở giai đoạn PMS (Còn {days_left} ngày nữa đến kỳ mới)"
    else:
        status_text = f"✨ Bình thường, còn {days_left} ngày nữa đến kỳ tiếp theo"
        
    return {
        "has_data": True,
        "latest_start_date": latest_start_date.strftime("%Y-%m-%d"),
        "predicted_length": predicted_length,
        "predicted_next_date": predicted_next_date.strftime("%Y-%m-%d"),
        "pms_start_date": pms_start_date.strftime("%Y-%m-%d"),
        "secret_alert_date": secret_alert_date.strftime("%Y-%m-%d"),
        "days_left": days_left,
        "status_text": status_text,
        "history_count": len(records),
        "cycle_history": cycle_lengths
    }

# Khởi tạo mô hình
train_or_load_menstrual_model()
