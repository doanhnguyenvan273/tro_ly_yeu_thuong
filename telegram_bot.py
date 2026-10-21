"""
telegram_bot.py - Telegram Chatbot Trợ Lý Yêu Thương (python-telegram-bot v20+)
Tích hợp ConversationHandler & InlineKeyboardMarkup ghi nhận Cảm xúc (Mood Tracker).
"""
import os
import sys
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Thiết lập encoding UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Đảm bảo đường dẫn import
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

import config
import database
import notifier
import bot_interactive

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Cấu hình logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Các trạng thái của ConversationHandler
WAITING_MOOD_SELECTION, WAITING_MOOD_NOTE = range(2)

# Bản đồ tên cảm xúc
MOOD_MAP = {
    "Happy": {"name": "Vui vẻ 😄", "icon": "😄"},
    "Sad": {"name": "Buồn 😔", "icon": "😔"},
    "Stressed": {"name": "Stress 😫", "icon": "😫"},
    "Angry": {"name": "Bực bội 😡", "icon": "😡"},
    "Tired": {"name": "Mệt mỏi 😴", "icon": "😴"},
}

def get_ai_responses(her_name: str = None, my_name: str = None) -> dict:
    if not her_name or not my_name:
        h, m = config.get_display_names()
        her_name = her_name or h
        my_name = my_name or m
    return {
        "Happy": f"Tuyệt vời quá! Chúc {her_name} luôn giữ nụ cười tươi tắn này nhé! 🥰",
        "Sad": f"Thương {her_name} lắm! Đừng buồn nhé, có {my_name} và Bác sĩ Mèo luôn ở bên {her_name} này! Nghỉ ngơi một chút và uống nước ấm nha {her_name}! 💖",
        "Stressed": f"Thương {her_name} lắm! Đừng quá sức nhé, nghỉ ngơi một chút và uống nước ấm nha {her_name}! 💖",
        "Angry": f"Thương {her_name} lắm! Hít thở thật sâu một chút nhé, đừng để chuyện bực mình làm ảnh hưởng đến sức khỏe nha {her_name}! 💖",
        "Tired": f"Thương {her_name} nhiều! Đừng làm việc quá sức nha, nghỉ ngơi một chút và uống nước ấm nhé {her_name}! 🍵💤💖",
    }

AI_RESPONSES = get_ai_responses()


def get_mood_inline_keyboard() -> InlineKeyboardMarkup:
    """Tạo bảng nút Inline Keyboard chọn cảm xúc."""
    keyboard = [
        [
            InlineKeyboardButton("😄 Vui vẻ", callback_data="mood_Happy"),
            InlineKeyboardButton("😔 Buồn", callback_data="mood_Sad"),
        ],
        [
            InlineKeyboardButton("😫 Stress", callback_data="mood_Stressed"),
            InlineKeyboardButton("😡 Bực bội", callback_data="mood_Angry"),
        ],
        [
            InlineKeyboardButton("😴 Mệt mỏi", callback_data="mood_Tired"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ======================= CONVERSATION HANDLERS =======================

async def start_mood_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bước 1: Bắt từ khóa 'cảm xúc', 'mood' và hiển thị Inline Keyboard."""
    user_id = str(update.effective_chat.id).strip()
    
    # Kiểm tra bảo mật ALLOWED_CHAT_IDS
    if config.ALLOWED_CHAT_IDS and user_id not in config.ALLOWED_CHAT_IDS:
        logger.warning(f"Từ chối chat_id lạ: {user_id}")
        return ConversationHandler.END

    her_name = config.get_her_name()
    text = (
        "🌸 <b>NHẬT KÝ CẢM XÚC HÔM NAY</b> 🐱\n\n"
        f"Bác sĩ Mèo đang lắng nghe {her_name} nè! Hôm nay tâm trạng của {her_name} thế nào?\n"
        "<i>Bấm vào một nút bên dưới để chia sẻ nhé:</i>"
    )
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=get_mood_inline_keyboard(),
            parse_mode="HTML"
        )
    return WAITING_MOOD_SELECTION


async def handle_mood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bước 2: Xử lý nút bấm cảm xúc và yêu cầu nhập ghi chú."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data or ""
    if not callback_data.startswith("mood_"):
        return ConversationHandler.END

    mood_type = callback_data.replace("mood_", "")
    context.user_data["selected_mood"] = mood_type

    mood_info = MOOD_MAP.get(mood_type, {"name": mood_type, "icon": "🌸"})
    mood_name = mood_info["name"]
    her_name = config.get_her_name()

    prompt_text = (
        f"Bác sĩ Mèo đã ghi nhận {her_name} đang <b>{mood_name}</b>! 🌸\n\n"
        f"{her_name} có muốn nhắn thêm điều gì đã xảy ra hôm nay không?\n"
        f"👉 <i>(Gõ nội dung ghi chú, hoặc gõ <code>Không</code> để bỏ qua nhé!)</i>"
    )

    await query.edit_message_text(
        prompt_text,
        parse_mode="HTML"
    )
    return WAITING_MOOD_NOTE


async def handle_mood_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bước 3: Nhận ghi chú, lưu vào Turso DB và gửi phản hồi vỗ về."""
    if not update.message or not update.message.text:
        return WAITING_MOOD_NOTE

    text_input = update.message.text.strip()
    mood_type = context.user_data.get("selected_mood", "Happy")
    mood_info = MOOD_MAP.get(mood_type, {"name": mood_type, "icon": "🌸"})
    mood_name = mood_info["name"]
    her_name, my_name = config.get_display_names()

    # Xác định ghi chú (nếu là 'Không' / 'khong' thì set None)
    if text_input.lower() in ["không", "khong", "k", "ko", "no", "skip"]:
        note: Optional[str] = None
    else:
        note = text_input

    # Câu an ủi vỗ về
    ai_resp_dict = get_ai_responses(her_name, my_name)
    ai_response = ai_resp_dict.get(mood_type, f"Thương {her_name} nhiều! Luôn giữ gìn sức khỏe nhé! 💖")
    today_str = config.get_now().strftime("%Y-%m-%d")

    # 1. Lưu an toàn vào CSDL (Turso Cloud / SQLite)
    try:
        database.add_mood_log(
            date_str=today_str,
            mood_type=mood_type,
            note=note,
            ai_response=ai_response
        )
        logger.info(f"Đã lưu mood_log: {mood_type} (note={note})")
    except Exception as e:
        logger.error(f"Lỗi khi lưu mood_log vào DB: {e}")

    # 2. Phản hồi cho người ấy
    note_str = f"\n📝 <i>Ghi chú: \"{note}\"</i>" if note else ""
    reply_msg = (
        f"🐱 <b>BÁC SĨ MÈO ĐÃ LẮNG NGHE!</b> 🌸\n\n"
        f"Tâm trạng hôm nay: <b>{mood_name}</b>{note_str}\n\n"
        f"{ai_response}"
    )
    await update.message.reply_text(reply_msg, parse_mode="HTML")

    # 3. Gửi cảnh báo bí mật cho bạn nếu tâm trạng Sad / Stressed / Angry / Tired
    if mood_type in ["Sad", "Stressed", "Angry", "Tired"]:
        try:
            note_content = note if note else "Không có ghi chú"
            secret_msg = (
                f"🤫 <b>[CẢNH BÁO TÂM LÝ BÍ MẬT DÀNH CHO {my_name.upper()}]</b>\n\n"
                f"{her_name} vừa cập nhật cảm xúc: <b>{mood_name}</b> qua Telegram.\n"
                f"📝 <b>Ghi chú:</b> {note_content}\n\n"
                f"👉 <i>{my_name} hãy nhắn tin hỏi thăm và chuẩn bị món gì đó ngon hoặc đồ ngọt cho {her_name} nhé! 🍫🧸💖</i>"
            )
            notifier.notify_you_secret(secret_msg)
        except Exception as notify_err:
            logger.error(f"Lỗi gửi cảnh báo bí mật: {notify_err}")

    # Dọn dẹp session
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_mood_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy bỏ hội thoại ghi nhận cảm xúc."""
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("Đã hủy cập nhật cảm xúc rồi nhé cậu! 🌸")
    return ConversationHandler.END


# ======================= GENERAL MESSAGE HANDLER =======================

async def general_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Chuyển tiếp các tin nhắn khác sang module bot_interactive."""
    if not update.message or not update.message.text:
        return

    # Chuyển đổi Update object sang dictionary để tương thích với bot_interactive
    msg_dict = {
        "message_id": update.message.message_id,
        "chat": {"id": update.effective_chat.id},
        "from": {
            "id": update.effective_user.id if update.effective_user else update.effective_chat.id,
            "first_name": update.effective_user.first_name if update.effective_user else "Bạn"
        },
        "text": update.message.text
    }
    try:
        bot_interactive.handle_incoming_message(msg_dict)
    except Exception as e:
        logger.error(f"Lỗi khi xử lý tin nhắn chung: {e}")


# ======================= BUILD APPLICATION =======================

def create_telegram_bot_application() -> Application:
    """Khởi tạo và cấu hình Application với ConversationHandler đầy đủ."""
    token = (config.TELEGRAM_BOT_TOKEN or config.load_settings().get("telegram_bot_token", "")).strip()
    if not token:
        raise ValueError("Chưa cấu hình TELEGRAM_BOT_TOKEN!")

    app = ApplicationBuilder().token(token).build()

    # Regex bắt các từ khóa cảm xúc
    mood_filter = filters.Regex(
        re.compile(r'(?i)\b(cảm xúc|cảm xúc hôm nay|cập nhật cảm xúc|mood|tam trang|tâm trạng)\b')
    )

    # Cấu hình ConversationHandler
    mood_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(mood_filter, start_mood_conversation),
            CommandHandler("mood", start_mood_conversation),
            CommandHandler("camxuc", start_mood_conversation),
        ],
        states={
            WAITING_MOOD_SELECTION: [
                CallbackQueryHandler(handle_mood_callback, pattern=r"^mood_")
            ],
            WAITING_MOOD_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mood_note)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_mood_conversation),
            MessageHandler(filters.Regex(re.compile(r'(?i)^(hủy|huy|cancel|bỏ qua)$')), cancel_mood_conversation)
        ],
        allow_reentry=True
    )

    app.add_handler(mood_conv_handler)
    # Các tin nhắn tra cứu khác (lịch học, deadline, thuốc, chu kỳ...)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, general_message_router))

    return app


def main():
    """Khởi chạy Telegram Bot độc lập."""
    print("=" * 60)
    print("🤖 KHỞI CHẠY TELEGRAM CHATBOT (PYTHON-TELEGRAM-BOT v20+)")
    print("=" * 60)
    database.init_db()
    app = create_telegram_bot_application()
    print("✅ Bot đang lắng nghe tin nhắn & ConversationHandler cảm xúc...")
    app.run_polling()


if __name__ == "__main__":
    main()
