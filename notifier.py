import os
import time
import requests
from typing import Optional, Union
from pathlib import Path
from config import load_settings, TELEGRAM_BOT_TOKEN, HER_CHAT_ID, YOUR_CHAT_ID

def send_telegram_message(chat_id: Union[str, int], text: str, parse_mode: str = "HTML", reply_markup: Optional[dict] = None, max_retries: int = 3) -> bool:
    """
    Gửi tin nhắn văn bản đến Telegram với khối try-except chống sập và cơ chế retry khi mất mạng.
    Hỗ trợ reply_markup (InlineKeyboardMarkup).
    """
    bot_token = (TELEGRAM_BOT_TOKEN or load_settings().get("telegram_bot_token", "")).strip()
    
    if not bot_token or not chat_id:
        # Không có cấu hình token hoặc chat_id, ghi log nhẹ và không làm crash ứng dụng
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                # Nếu lỗi do HTML format, thử gửi lại với plain text
                if attempt == 1 and "can't parse entities" in response.text.lower():
                    payload.pop("parse_mode", None)
                    continue
                print(f"[Telegram Notifier] Lỗi gửi tin nhắn (Lần {attempt}): {response.text}")
        except (requests.ConnectionError, requests.Timeout) as net_err:
            print(f"[Telegram Notifier] Mất mạng hoặc rớt kết nối (Lần {attempt}/{max_retries}): {net_err}")
            time.sleep(2)
        except Exception as e:
            print(f"[Telegram Notifier] Lỗi không mong đợi: {e}")
            break
            
    return False

def send_telegram_photo(chat_id: Union[str, int], photo_path: Union[str, Path], caption: str = "", parse_mode: str = "HTML", max_retries: int = 3) -> bool:
    """
    Gửi ảnh (ví dụ vỏ thuốc) kèm chú thích tới Telegram.
    Nếu gửi ảnh thất bại hoặc không có file ảnh, fallback gửi tin nhắn văn bản.
    """
    bot_token = (TELEGRAM_BOT_TOKEN or load_settings().get("telegram_bot_token", "")).strip()
    
    if not bot_token or not chat_id:
        return False

    photo_path = Path(photo_path) if photo_path else None
    
    if not photo_path or not photo_path.exists():
        # Fallback gửi tin nhắn chữ
        return send_telegram_message(chat_id, caption, parse_mode=parse_mode)

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    for attempt in range(1, max_retries + 1):
        try:
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode}
                response = requests.post(url, data=data, files=files, timeout=20)
                if response.status_code == 200:
                    return True
                else:
                    print(f"[Telegram Photo] Lỗi gửi ảnh: {response.text}")
        except (requests.ConnectionError, requests.Timeout) as net_err:
            print(f"[Telegram Photo] Lỗi mạng khi gửi ảnh: {net_err}")
            time.sleep(2)
        except Exception as e:
            print(f"[Telegram Photo] Lỗi ngoại lệ: {e}")
            break
            
    # Nếu gửi ảnh thất bại sau các lần thử, thử gửi caption dạng text
    return send_telegram_message(chat_id, caption, parse_mode=parse_mode)

def send_telegram_document(chat_id: Union[str, int], file_path: Union[str, Path], caption: str = "", parse_mode: str = "HTML", max_retries: int = 3) -> bool:
    """
    Gửi file tài liệu (ví dụ file sao lưu backup CSDL) tới Telegram.
    """
    bot_token = (TELEGRAM_BOT_TOKEN or load_settings().get("telegram_bot_token", "")).strip()
    if not bot_token or not chat_id:
        return False

    file_path = Path(file_path)
    if not file_path.exists():
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    for attempt in range(1, max_retries + 1):
        try:
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode}
                response = requests.post(url, data=data, files=files, timeout=30)
                if response.status_code == 200:
                    return True
                else:
                    print(f"[Telegram Document] Lỗi gửi tài liệu: {response.text}")
        except Exception as e:
            print(f"[Telegram Document] Lỗi ngoại lệ (Lần {attempt}): {e}")
            time.sleep(2)

    return False

def notify_her(message: str, photo_path: Optional[str] = None) -> bool:
    """Gửi thông báo tới Cậu."""
    her_chat_id = (HER_CHAT_ID or load_settings().get("telegram_her_chat_id", "")).strip()
    if not her_chat_id:
        return False
        
    if photo_path and os.path.exists(photo_path):
        return send_telegram_photo(her_chat_id, photo_path, caption=message)
    return send_telegram_message(her_chat_id, message)

def notify_you_secret(message: str) -> bool:
    """Gửi thông báo BÍ MẬT tới Bạn (Secret Mode)."""
    settings = load_settings()
    if not settings.get("secret_mode_enabled", True):
        return False
        
    my_chat_id = (YOUR_CHAT_ID or settings.get("telegram_my_chat_id", "")).strip()
    if not my_chat_id:
        return False
        
    return send_telegram_message(my_chat_id, message)

def test_telegram_connection(bot_token: str, chat_id: str) -> dict:
    """Kiểm tra tính hợp lệ của Bot Token và Chat ID."""
    if not bot_token:
        return {"success": False, "message": "Chưa nhập Bot Token!"}
        
    try:
        # Kiểm tra getMe
        me_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=8)
        if me_resp.status_code != 200:
            return {"success": False, "message": "Bot Token không hợp lệ!"}
        
        bot_info = me_resp.json().get("result", {})
        bot_name = bot_info.get("first_name", "Bot")
        bot_username = bot_info.get("username", "")

        # Nếu có chat_id thì thử gửi tin nhắn test
        if chat_id:
            her_name = config.get_her_name()
            test_msg = f"💖 Kết nối thành công với Bot @{bot_username}!\nTrợ Lý Yêu Thương đã sẵn sàng phục vụ {her_name} rồi nha! 🌸"
            send_resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": test_msg},
                timeout=8
            )
            if send_resp.status_code == 200:
                return {
                    "success": True, 
                    "message": f"Kết nối hoàn hảo! Đã gửi tin nhắn test thành công tới Chat ID qua Bot @{bot_username}."
                }
            else:
                return {
                    "success": False,
                    "message": f"Bot @{bot_username} hoạt động nhưng không gửi được tới Chat ID (Hãy chắc chắn bạn đã nhấn /start với bot)."
                }
                
        return {"success": True, "message": f"Bot @{bot_username} hợp lệ!"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi kết nối mạng: {e}"}
