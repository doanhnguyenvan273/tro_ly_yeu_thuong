"""
Module tương thích ngược cho telegram_listener.
Chuyển tiếp trực tiếp sang bot_interactive.py.
"""
from bot_interactive import (
    start_telegram_listener,
    stop_telegram_listener,
    lang_nghe_tin_nhan,
    handle_incoming_message,
    build_schedule_response,
    build_medicine_response,
    build_deadline_response,
    build_help_response,
    DAY_NAMES
)

__all__ = [
    "start_telegram_listener",
    "stop_telegram_listener",
    "lang_nghe_tin_nhan",
    "handle_incoming_message",
    "build_schedule_response",
    "build_medicine_response",
    "build_deadline_response",
    "build_help_response",
    "DAY_NAMES"
]
