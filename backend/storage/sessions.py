"""
Storage — SQLite ẩn danh, TTL 30 ngày.
"""
import aiosqlite
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from backend.config import SESSION_TTL_DAYS


DB_PATH = Path(__file__).parent / "goc_nho.db"


async def init_db():
    """Khởi tạo bảng nếu chưa có."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Bảng phiên — ẩn danh, chỉ có session_id
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                sentiment_scores TEXT DEFAULT '[]'
            )
        """)
        
        # Bảng tin nhắn — lưu nội dung để GVCN review (ẩn danh)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Bảng log chặn — để GVCN rà soát
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                reason TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Bảng cảnh báo khủng hoảng — lưu lịch sử để dashboard xem
        await db.execute("""
            CREATE TABLE IF NOT EXISTS crisis_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                level INTEGER NOT NULL,
                level_name TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Bảng email nhận cảnh báo — quản lý qua dashboard
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alert_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        await db.commit()


async def get_or_create_session(session_id: str) -> dict:
    """Lấy hoặc tạo phiên mới."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT session_id, created_at, last_active FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if row:
            # Cập nhật last_active
            await db.execute(
                "UPDATE sessions SET last_active = ? WHERE session_id = ?",
                (now, session_id)
            )
            await db.commit()
            return {"session_id": row[0], "created_at": row[1], "last_active": now}
        else:
            # Tạo mới
            await db.execute(
                "INSERT INTO sessions (session_id, created_at, last_active) VALUES (?, ?, ?)",
                (session_id, now, now)
            )
            await db.commit()
            return {"session_id": session_id, "created_at": now, "last_active": now}


async def append_message(session_id: str, role: str, content: str):
    """Thêm tin nhắn vào phiên."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now().isoformat())
        )
        await db.commit()


async def get_recent_messages(session_id: str, limit: int = 10) -> list[dict]:
    """Lấy N tin nhắn gần nhất của phiên."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


async def log_blocked(session_id: str, reason: str):
    """Ghi log lần chặn."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO blocked_logs (session_id, reason, timestamp) VALUES (?, ?, ?)",
            (session_id, reason, datetime.now().isoformat())
        )
        await db.commit()


async def log_crisis_alert(session_id: str, level: int, level_name: str, message: str):
    """Lưu cảnh báo khủng hoảng vào DB."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO crisis_alerts (session_id, level, level_name, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, level, level_name, message, datetime.now().isoformat())
        )
        await db.commit()


async def get_recent_alerts(limit: int = 20) -> list[dict]:
    """Lấy danh sách cảnh báo gần đây (ẩn danh)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT session_id, level, level_name, message, timestamp FROM crisis_alerts ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [
            {
                "session_id": r[0][:12] + "...",
                "level": r[1],
                "level_name": r[2],
                "message": r[3],
                "timestamp": r[4],
            }
            for r in rows
        ]


async def get_weekly_stats() -> dict:
    """Tổng hợp thống kê tuần cho dashboard GVCN."""
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Số phiên hoạt động
        cursor = await db.execute(
            "SELECT COUNT(*) FROM sessions WHERE last_active >= ?",
            (week_ago,)
        )
        active_sessions = (await cursor.fetchone())[0]
        
        # Số tin nhắn
        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE timestamp >= ?",
            (week_ago,)
        )
        message_count = (await cursor.fetchone())[0]
        
        # Số lần chặn
        cursor = await db.execute(
            "SELECT COUNT(*) FROM blocked_logs WHERE timestamp >= ?",
            (week_ago,)
        )
        blocked_count = (await cursor.fetchone())[0]
        
        return {
            "active_sessions": active_sessions,
            "message_count": message_count,
            "blocked_count": blocked_count,
            "period": "7 ngày",
        }


async def cleanup_old_sessions():
    """Xóa phiên cũ hơn TTL."""
    cutoff = (datetime.now() - timedelta(days=SESSION_TTL_DAYS)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE session_id IN (SELECT session_id FROM sessions WHERE last_active < ?)", (cutoff,))
        await db.execute("DELETE FROM sessions WHERE last_active < ?", (cutoff,))
        await db.commit()


# ============ ALERT EMAILS ============

async def get_alert_emails() -> list[str]:
    """Lấy danh sách email nhận cảnh báo."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT email FROM alert_emails ORDER BY created_at")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def add_alert_email(email: str):
    """Thêm email nhận cảnh báo."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO alert_emails (email, created_at) VALUES (?, ?)",
            (email, datetime.now().isoformat())
        )
        await db.commit()


async def remove_alert_email(email: str):
    """Xóa email nhận cảnh báo."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM alert_emails WHERE email = ?", (email,))
        await db.commit()
