"""
Thông báo cho GVCN — email qua Brevo API (HTTP) hoặc webhook Zalo.
"""
import asyncio
import sys
import httpx
from datetime import datetime, timezone, timedelta
from backend.config import (
    TEACHER_EMAIL,
    TEACHER_EMAILS,
    TEACHER_ZALO_WEBHOOK,
    BREVO_API_KEY,
    EMAIL_FROM,
    APP_NAME,
)
from backend.storage.sessions import get_alert_emails

# In-memory log buffer (tối đa 100 dòng)
_email_logs = []
MAX_LOGS = 100

VN_TZ = timezone(timedelta(hours=7))

def _add_log(status: str, message: str):
    """Thêm log vào buffer."""
    _email_logs.append({
        "time": datetime.now(VN_TZ).strftime("%H:%M:%S %d/%m/%Y"),
        "status": status,
        "message": message,
    })
    if len(_email_logs) > MAX_LOGS:
        _email_logs.pop(0)

def get_email_logs() -> list[dict]:
    """Trả về danh sách log gần đây (mới nhất trước)."""
    return list(reversed(_email_logs))


async def notify_teacher(alert: dict):
    """
    Gửi cảnh báo khủng hoảng cho GVCN.
    Ưu tiên: Brevo API → Webhook Zalo → Console log.
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
    _add_log("ALERT", f"Canh bao muc {alert['level']} ({alert['level_name']}) - Session {alert['session_id'][:8]}...")

    # Lấy danh sách email từ DB (ưu tiên) hoặc config
    db_emails = await get_alert_emails()
    emails_to_send = db_emails if db_emails else TEACHER_EMAILS

    # 1. Gửi email qua Brevo API — chạy nền, không block phản hồi
    if emails_to_send and BREVO_API_KEY:
        async def _send_all():
            for email in emails_to_send:
                try:
                    await asyncio.wait_for(_send_brevo_email(alert, email), timeout=10.0)
                    print(f"[OK] Da gui email toi {email}")
                    _add_log("OK", f"Da gui email toi {email}")
                except asyncio.TimeoutError:
                    print(f"[ERROR] Timeout gui email toi {email}")
                    _add_log("ERROR", f"Timeout gui email toi {email} (Brevo API mat qua 10s)")
                except Exception as e:
                    print(f"[ERROR] Khong gui duoc email toi {email}: {e}")
                    _add_log("ERROR", f"Khong gui duoc email toi {email}: {e}")

        asyncio.create_task(_send_all())
    elif emails_to_send:
        for email in emails_to_send:
            print(f"[MOCK] Gui email toi {email}: {alert['message']}")
            _add_log("MOCK", f"Gui email toi {email}: {alert['message']}")
        print(f"       ⚠️  CHUA CO BREVO_API_KEY — can them BREVO_API_KEY vao file .env")
        _add_log("MOCK", "CHUA CO BREVO_API_KEY — can them BREVO_API_KEY vao file .env")

    # 2. Gửi webhook Zalo (nếu có URL thật) — cũng chạy nền
    if TEACHER_ZALO_WEBHOOK and TEACHER_ZALO_WEBHOOK.startswith("http"):
        async def _send_zalo():
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(TEACHER_ZALO_WEBHOOK, json=alert, timeout=5.0)
                    if resp.status_code == 200:
                        print(f"[OK] Da gui webhook Zalo")
                        _add_log("OK", "Da gui webhook Zalo")
                    else:
                        print(f"[ERROR] Webhook Zalo tra ve {resp.status_code}")
                        _add_log("ERROR", f"Webhook Zalo tra ve {resp.status_code}")
            except Exception as e:
                print(f"[ERROR] Khong gui duoc webhook Zalo: {e}")
                _add_log("ERROR", f"Khong gui duoc webhook Zalo: {e}")

        asyncio.create_task(_send_zalo())
    elif TEACHER_ZALO_WEBHOOK:
        print(f"[MOCK] Gui webhook Zalo: {TEACHER_ZALO_WEBHOOK}")
        _add_log("MOCK", f"Gui webhook Zalo: {TEACHER_ZALO_WEBHOOK}")
    else:
        print(f"[MOCK] Gui webhook Zalo: CHUA CAU HINH — can them TEACHER_ZALO_WEBHOOK vao file .env")
        _add_log("MOCK", "CHUA CAU HINH Zalo webhook")


async def _send_brevo_email(alert: dict, to_email: str):
    """Gửi email cảnh báo qua Brevo Transactional Email API."""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {
            "name": APP_NAME,
            "email": EMAIL_FROM or "khanhnhh209@gmail.com",
        },
        "to": [{"email": to_email}],
        "subject": f"🚨 [{alert['level_name']}] Cảnh báo {APP_NAME}",
        "htmlContent": f"""\
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e74c3c; border-radius: 8px;">
    <h2 style="color: #e74c3c; margin-top: 0;">🚨 Cảnh báo khủng hoảng</h2>
    <p><strong>Từ chatbot:</strong> {APP_NAME}</p>
    <p><strong>Mức độ:</strong> {alert['level_name']} (Level {alert['level']})</p>
    <p><strong>Session:</strong> {alert['session_id'][:12]}...</p>
    <p><strong>Thờn gian:</strong> {alert['timestamp']} (giờ Việt Nam)</p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 16px 0;">
    <p><strong>Nội dung cảnh báo:</strong></p>
    <p style="background: #fdf2f2; padding: 12px; border-radius: 4px; border-left: 4px solid #e74c3c;">
      {alert['message']}
    </p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 16px 0;">
    <p style="font-size: 14px; color: #666;">
      <em>Lưu ý: Đây là cảnh báo ẩn danh. Vui lòng kiểm tra sức khỏe học sinh cả lớp,
      không truy tìm cá nhân.</em>
    </p>
    <p style="font-size: 12px; color: #999; margin-bottom: 0;">
      {APP_NAME} — Sáng kiến CN03, THCS Hưng Chính
    </p>
  </div>
</body>
</html>""",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
        resp.raise_for_status()
