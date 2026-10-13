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
