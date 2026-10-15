import re
from pathlib import Path
from typing import Dict, Any, List

# Kiểm tra sự sẵn có của các thư viện OCR
HAVE_EASYOCR = False
HAVE_PYTESSERACT = False

try:
    import easyocr
    HAVE_EASYOCR = True
except Exception:
    HAVE_EASYOCR = False

if not HAVE_EASYOCR:
    try:
        import pytesseract
        from PIL import Image
        HAVE_PYTESSERACT = True
    except Exception:
        HAVE_PYTESSERACT = False

# Biến toàn cục lưu reader để không phải tải lại model OCR nhiều lần
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None and HAVE_EASYOCR:
        try:
            # Tải EasyOCR với tiếng Việt ('vi') và tiếng Anh ('en')
            _easyocr_reader = easyocr.Reader(['vi', 'en'], gpu=False)
        except Exception as e:
            print(f"Không thể khởi tạo EasyOCR: {e}")
            _easyocr_reader = None
    return _easyocr_reader

def extract_text_from_image(image_path: str) -> str:
    """Quét và trích xuất toàn bộ văn bản từ ảnh chụp vỏ thuốc hoặc đơn thuốc."""
    text_content = ""
    
    # Cách 1: Thử EasyOCR
    if HAVE_EASYOCR:
        try:
            reader = get_easyocr_reader()
            if reader:
                results = reader.readtext(image_path, detail=0)
                text_content = " ".join(results)
                if text_content.strip():
                    return text_content
        except Exception as e:
            print(f"EasyOCR quét lỗi: {e}")
            
    # Cách 2: Thử PyTesseract
    if HAVE_PYTESSERACT:
        try:
            from PIL import Image
            img = Image.open(image_path)
            text_content = pytesseract.image_to_string(img, lang='vie+eng')
            if text_content.strip():
                return text_content
        except Exception as e:
            print(f"PyTesseract quét lỗi: {e}")
            
    return text_content

def parse_medicine_info(text: str) -> Dict[str, Any]:
    """
    Phân tích văn bản OCR để nhận diện thông minh các từ khóa:
    - Tên thuốc (Panadol, Paracetamol, Hapacol, Decolgen, Amoxicillin, Berberin, Vitamin C, ...)
    - Liều lượng (1 viên, 2 viên, 1 gói, 5ml, sau ăn, trước ăn...)
    - Các mốc giờ uống (sáng -> 08:00, trưa -> 12:30, chiều/tối -> 19:30, hoặc giờ cụ thể)
    - Số ngày uống (uống trong 3 ngày, 5 ngày, 7 ngày...)
    """
    raw_text = text.lower()
    
    # 1. Nhận diện tên thuốc phổ biến
    common_medicines = [
        "Panadol Extra", "Panadol", "Paracetamol", "Hapacol", "Decolgen", 
        "Tiffy", "Amoxicillin", "Augmentin", "Cephalexin", "Berberin", 
        "Smecta", "Efferalgan", "Vitamin C", "Kẽm Zinc", "Omega 3", 
        "Bổ sung Sắt", "Men vi sinh", "Thuốc nhỏ mắt", "Gaviscon", "Strepsils"
    ]
    detected_name = ""
    for med in common_medicines:
        if re.search(r'\b' + re.escape(med.lower()) + r'\b', raw_text):
            detected_name = med
            break
            
    # Nếu chưa tìm thấy trong từ điển, tìm từ viết hoa hoặc dòng đầu
    if not detected_name:
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
        if lines:
            detected_name = lines[0][:40]
        else:
            words = text.split()
            detected_name = " ".join(words[:3]) if words else "Thuốc theo đơn"

    # 2. Nhận diện liều lượng (số viên / gói / thìa + sau ăn / trước ăn)
    quantity = "1 viên"
    qty_match = re.search(r'(\d+)\s*(viên|gói|ống|ml|muỗng)', raw_text)
    if qty_match:
        quantity = f"{qty_match.group(1)} {qty_match.group(2)}"
        
    timing_note = "sau ăn"
    if "trước ăn" in raw_text or "trước bữa ăn" in raw_text or "khi đói" in raw_text:
        timing_note = "trước ăn"
    elif "sau ăn" in raw_text or "sau bữa ăn" in raw_text or "no" in raw_text:
        timing_note = "sau ăn"
    elif "khi sốt" in raw_text or "khi đau" in raw_text:
        timing_note = "khi đau sốt"
        
    dosage = f"{quantity} ({timing_note})"

    # 3. Nhận diện các mốc giờ uống
    times = []
    # Tìm giờ cụ thể dạng 08:00 hoặc 8h
    hour_matches = re.findall(r'(\d{1,2})[h:](\d{2})?', raw_text)
    
    has_sang = bool(re.search(r'\b(sáng|morning)\b', raw_text))
    has_trua = bool(re.search(r'\b(trưa|noon)\b', raw_text))
    has_chieu = bool(re.search(r'\b(chiều|afternoon)\b', raw_text))
    has_toi = bool(re.search(r'\b(tối|đêm|night)\b', raw_text))
    
    if has_sang:
        times.append("08:00")
    if has_trua:
        times.append("12:30")
    if has_chieu:
        times.append("17:00")
    if has_toi:
        times.append("20:00")
        
    # Nếu không có từ sáng trưa tối, kiểm tra tần suất ví dụ "ngày 2 lần", "ngày 3 lần"
    if not times:
        if "3 lần" in raw_text or "ngày 3" in raw_text:
            times = ["08:00", "13:00", "20:00"]
        elif "2 lần" in raw_text or "ngày 2" in raw_text:
            times = ["08:00", "19:00"]
        elif "1 lần" in raw_text or "ngày 1" in raw_text:
            times = ["08:30"]
        else:
            # Mặc định thông dụng
            times = ["08:00", "19:30"]
            
    times_str = ", ".join(times)

    # 4. Nhận diện số ngày uống
    days_count = 5
    days_match = re.search(r'(\d+)\s*(ngày|day)', raw_text)
    if days_match:
        try:
            d_val = int(days_match.group(1))
            if 1 <= d_val <= 30:
                days_count = d_val
        except Exception:
            pass

    return {
        "name": detected_name,
        "dosage": dosage,
        "times": times_str,
        "days_count": days_count,
        "raw_text": text
    }

def process_medicine_image(image_path: str) -> Dict[str, Any]:
    """Hàm tổng hợp: Quét ảnh và trích xuất gợi ý lịch uống thuốc."""
    raw_text = extract_text_from_image(image_path)
    return parse_medicine_info(raw_text)
