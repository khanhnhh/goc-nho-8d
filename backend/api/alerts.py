"""
API routes — quản lý cảnh báo và email nhận cảnh báo cho dashboard.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from backend.storage.sessions import (
    get_recent_alerts,
    get_alert_emails,
    add_alert_email,
    remove_alert_email,
)

router = APIRouter()


class EmailRequest(BaseModel):
    email: EmailStr


@router.get("/api/alerts")
async def alerts(limit: int = 20):
    """Lấy danh sách cảnh báo gần đây (ẩn danh)."""
    return {"alerts": await get_recent_alerts(limit)}


@router.get("/api/alert-emails")
async def list_emails():
    """Lấy danh sách email nhận cảnh báo."""
    return {"emails": await get_alert_emails()}


@router.post("/api/alert-emails")
async def add_email(req: EmailRequest):
    """Thêm email nhận cảnh báo."""
    await add_alert_email(req.email)
    return {"ok": True, "email": req.email}


@router.delete("/api/alert-emails/{email}")
async def delete_email(email: str):
    """Xóa email nhận cảnh báo."""
    await remove_alert_email(email)
    return {"ok": True, "email": email}
