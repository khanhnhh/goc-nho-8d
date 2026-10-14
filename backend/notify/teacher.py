"""
Thông báo cho GVCN — email (nhiều ngườ nhận) hoặc webhook Zalo.
"""
import sys
import httpx
import aiosmtplib
from email.message import EmailMessage
from backend.config import (
    TEACHER_EMAIL,
    TEACHER_EMAILS,
    TEACHER_ZALO_WEBHOOK,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM,
    APP_NAME,
)
from backend.storage.sessions import get_alert_emails


async def notify_teacher(alert: dict):
    """
    Gửi cảnh báo khủng hoảng cho GVCN.
    Ưu tiên: Email SMTP → Webhook Zalo → Console log.
    """
    # Force UTF-8 cho console Windows (cp1252 không hỗ trợ tiếng Việt + emoji)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print(f"\n{'='*60}")
    print("[!] CANH BAO KHUNG HOANG")
    print(f"Muc do: {alert['level_name']}")
    print(f"Session: {alert['session_id']}")
    print(f"Thoi gian: {alert['timestamp']}")
    print(f"{'='*60}\n")

    # Lấy danh sách email từ DB (ưu tiên) hoặc config
    db_emails = await get_alert_emails()
    emails_to_send = db_emails if db_emails else TEACHER_EMAILS

    # 1. Gửi email thật (nếu có SMTP config)
    if emails_to_send and SMTP_USER and SMTP_PASSWORD:
        for email in emails_to_send:
            try:
                await _send_email(alert, email)
                print(f"[OK] Da gui email toi {email}")
            except Exception as e:
                print(f"[ERROR] Khong gui duoc email toi {email}: {e}")
    elif emails_to_send:
        for email in emails_to_send:
            print(f"[MOCK] Gui email toi {email}: {alert['message']}")
        print(f"       ⚠️  CHUA CO SMTP CONFIG — can them SMTP_USER va SMTP_PASSWORD vao file .env")

    # 2. Gửi webhook Zalo (nếu có URL thật)
    if TEACHER_ZALO_WEBHOOK and TEACHER_ZALO_WEBHOOK.startswith("http"):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(TEACHER_ZALO_WEBHOOK, json=alert, timeout=5.0)
                if resp.status_code == 200:
                    print(f"[OK] Da gui webhook Zalo")
                else:
                    print(f"[ERROR] Webhook Zalo tra ve {resp.status_code}")
        except Exception as e:
            print(f"[ERROR] Khong gui duoc webhook Zalo: {e}")
    elif TEACHER_ZALO_WEBHOOK:
        print(f"[MOCK] Gui webhook Zalo: {TEACHER_ZALO_WEBHOOK}")
    else:
        print(f"[MOCK] Gui webhook Zalo: CHUA CAU HINH — can them TEACHER_ZALO_WEBHOOK vao file .env")


async def _send_email(alert: dict, to_email: str):
    """Gửi email cảnh báo qua SMTP (Gmail App Password)."""
    msg = EmailMessage()
    msg["Subject"] = f"🚨 [{alert['level_name']}] Cảnh báo {APP_NAME}"
    msg["From"] = EMAIL_FROM or SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"""Cảnh báo khủng hoảng từ chatbot {APP_NAME}

Mức độ: {alert['level_name']} (Level {alert['level']})
Session: {alert['session_id'][:12]}...
Thờn gian: {alert['timestamp']}

Nội dung cảnh báo:
{alert['message']}

Lưu ý: Đây là cảnh báo ẩn danh. Vui lòng kiểm tra sức khỏe học sinh cả lớp,
không truy tìm cá nhân.

---
{APP_NAME} — Sáng kiến CN03, THCS Hưng Chính
"""
    )

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST or "smtp.gmail.com",
        port=SMTP_PORT or 587,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        start_tls=True,
    )
