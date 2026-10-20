import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from config import DEADLINE_MODEL_PATH

def generate_initial_training_data():
    """
    Tạo bộ dữ liệu mô phỏng tình huống học tập sinh viên:
    Features:
    - classes_today: Số ca học trong ngày (0 đến 4 ca)
    - free_hours_left: Số giờ rảnh còn lại trước deadline (0.5 đến 48 giờ)
    - estimated_hours: Khối lượng công việc cần làm (0.5 đến 20 giờ)
    
    Target:
    - 1: Nguy cơ trễ hạn cao
    - 0: Kịp tiến độ an toàn
    """
    np.random.seed(42)
    n_samples = 1200
    
    classes_today = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=[0.2, 0.3, 0.25, 0.15, 0.1])
    free_hours_left = np.random.uniform(0.5, 48.0, size=n_samples)
    estimated_hours = np.random.uniform(0.5, 18.0, size=n_samples)
    
    # Logic xác định nhãn: Nếu thời gian rảnh trừ đi số giờ học thực tế < estimated_hours * 1.3 -> trễ hạn
    # Mỗi ca học chiếm khoảng 2.5 - 3 giờ
    effective_free = free_hours_left - (classes_today * 2.2)
    risk_score = estimated_hours / (effective_free + 0.5)
    
    # Nhãn trễ hạn nếu risk_score > 0.85 hoặc effective_free < estimated_hours
    labels = np.where((risk_score > 0.85) | (effective_free < estimated_hours), 1, 0)
    
    X = np.column_stack([classes_today, free_hours_left, estimated_hours])
    y = labels
    return X, y

def train_or_load_deadline_model() -> RandomForestClassifier:
    """Tải mô hình nếu đã lưu, hoặc tự động huấn luyện mô hình mới."""
    if DEADLINE_MODEL_PATH.exists():
        try:
            model = joblib.load(DEADLINE_MODEL_PATH)
            return model
        except Exception:
            pass
            
    # Huấn luyện mô hình RandomForestClassifier mới
    X, y = generate_initial_training_data()
    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X, y)
    
    DEADLINE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, DEADLINE_MODEL_PATH)
    return model

def predict_deadline_risk(task_name: str, classes_today: int, free_hours_left: float, estimated_hours: float) -> dict:
    """
    Dự đoán xác suất trễ hạn của một task.
    Trả về:
    - risk_percentage: Tỷ lệ % nguy cơ trễ hạn (0 - 100%)
    - warning_level: 'AN TOÀN', 'CHÚ Ý', 'NGUY CƠ CAO'
    - warning_message: Câu cảnh báo yêu thương theo định dạng SRS
    """
    model = train_or_load_deadline_model()
    
    X_input = np.array([[classes_today, max(0.1, free_hours_left), max(0.1, estimated_hours)]])
    probabilities = model.predict_proba(X_input)[0]
    
    # probabilities[1] là xác suất class 1 (trễ hạn)
    risk_percentage = round(probabilities[1] * 100, 1)
    
    # Điều chỉnh thực tế nếu số giờ rảnh ít hơn hẳn khối lượng việc
    if free_hours_left < estimated_hours:
        risk_percentage = max(risk_percentage, 85.0)
    elif free_hours_left > estimated_hours * 3 and classes_today <= 1:
        risk_percentage = min(risk_percentage, 20.0)
        
    risk_percentage = min(99.0, max(1.0, risk_percentage))
    
    if risk_percentage >= 70:
        warning_level = "NGUY CƠ CAO"
        warning_message = (
            f"⚠️ CẢNH BÁO: Task '{task_name}' có {risk_percentage:.0f}% nguy cơ trễ hạn do "
            f"hôm đó cậu có {classes_today} ca học và chỉ còn {free_hours_left:.1f} giờ rảnh "
            f"(khối lượng dự kiến: {estimated_hours:.1f}h). Hãy làm sớm nhé! 🌸"
        )
    elif risk_percentage >= 40:
        warning_level = "CHÚ Ý"
        warning_message = (
            f"⚡ LƯU Ý: Task '{task_name}' có {risk_percentage:.0f}% nguy cơ trễ hạn. "
            f"Cậu còn {free_hours_left:.1f} giờ rảnh và {classes_today} ca học. Hãy sắp xếp thời gian làm sớm nha! 💖"
        )
    else:
        warning_level = "AN TOÀN"
        warning_message = (
            f"✅ TIẾN ĐỘ TỐT: Task '{task_name}' chỉ có {risk_percentage:.0f}% rủi ro. "
            f"Thời gian còn lại rất thoải mái ({free_hours_left:.1f}h rảnh). Cố lên cậu nhé! ✨"
        )
        
    return {
        "risk_percentage": risk_percentage,
        "warning_level": warning_level,
        "warning_message": warning_message,
        "classes_today": classes_today,
        "free_hours_left": free_hours_left,
        "estimated_hours": estimated_hours
    }

# Khởi tạo mô hình ngay khi import
train_or_load_deadline_model()
