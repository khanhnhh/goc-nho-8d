"""
Thông báo cho GVCN — email hoặc webhook Zalo.
"""
import httpx
from datetime import datetime
from backend.config import TEACHER_EMAIL, TEACHER_ZALO_WEBHOOK


async def notify_teacher(alert: dict):
    """
    Gửi cảnh báo khủng hoảng cho GVCN.
    Hiện tại chỉ log ra console — tích hợp email/Zalo thật khi triển khai.
    """
    print(f"\n{'='*60}")
    print(f"🚨 CẢNH BÁO KHỦNG HOẢNG")
    print(f"Mức độ: {alert['level_name']}")
    print(f"Session: {alert['session_id']}")
    print(f"Thời gian: {alert['timestamp']}")
    print(f"{'='*60}\n")
    
    # Gửi email (giả lập)
    if TEACHER_EMAIL:
        print(f"[MOCK] Gửi email tới {TEACHER_EMAIL}: {alert['message']}")
    
    # Gửi webhook Zalo (giả lập)
    if TEACHER_ZALO_WEBHOOK:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(TEACHER_ZALO_WEBHOOK, json=alert, timeout=5.0)
                print(f"[MOCK] Gửi webhook Zalo thành công")
        except Exception as e:
            print(f"[ERROR] Không gửi được webhook Zalo: {e}")
