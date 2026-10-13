"""
Lớp 4 — Cảnh báo khủng hoảng: template cố định + thông báo GVCN.
"""
from datetime import datetime


CRISIS_TEMPLATE = """Em ơi, mình rất lo cho em lúc này. Điều em đang gánh đang quá lớn để tự mình xoay xở — và KHÔNG phải lỗi của em.

👉 Gọi ngay Tổng đài Quốc gia Bảo vệ Trẻ em 111 (miễn phí, 24/7)
👉 Hoặc tìm ngay cô Dung hoặc người lớn mà em tin nhất.

Mình vẫn ở đây. Em kể thêm cho mình nghe được không?"""


def get_crisis_template() -> str:
    """Trả về template khủng hoảng cố định."""
    return CRISIS_TEMPLATE


def format_teacher_alert(level: int, session_id: str) -> dict:
    """
    Tạo thông báo cho GVCN — chỉ gồm mức độ + thời gian, không có nội dung chi tiết.
    """
    level_names = {0: "An toàn", 1: "Cảnh báo", 2: "Khẩn cấp"}
    return {
        "level": level,
        "level_name": level_names.get(level, "Không xác định"),
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "message": f"Cảnh báo mức {level} ({level_names.get(level, '')}) từ session {session_id[:8]}...",
    }
