"""
FastAPI backend — trái tim của hệ thống, điều phối 4 lớp phòng thủ.
"""
import re
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from backend.config import SYSTEM_PROMPT, BASE_DIR
from backend.llm import get_llm
from backend.guardrails.input_filter import (
    detect_crisis,
    mask_pii,
    wrap_user_message,
    check_rate_limit,
)
from backend.guardrails.output_validator import validate_output
from backend.guardrails.crisis import get_crisis_template, format_teacher_alert
from backend.storage.sessions import (
    init_db,
    get_or_create_session,
    append_message,
    get_recent_messages,
    log_blocked,
    log_crisis_alert,
    get_weekly_stats,
    cleanup_old_sessions,
)
from backend.notify.teacher import notify_teacher
from backend.api.alerts import router as alerts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo DB khi startup."""
    await init_db()
    await cleanup_old_sessions()
    yield


app = FastAPI(
    title="Ngườ bạn nhỏ AI — Chatbot hỗ trợ tâm lý",
    description="Chatbot ẩn danh hỗ trợ tâm lý cho học sinh lớp 8",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(alerts_router)


# ============ MODELS ============

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    is_crisis: bool = False


class StatsResponse(BaseModel):
    active_sessions: int
    message_count: int
    blocked_count: int
    period: str


# ============ ENDPOINTS ============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Xử lý 1 tin nhắn từ học sinh qua 4 lớp phòng thủ:
    1. Rate limit + crisis detection (đầu vào)
    2. PII masking + prompt injection protection
    3. Gọi LLM với system prompt
    4. Output validation + crisis response
    """
    
    # Tạo session ID nếu chưa có
    session_id = req.session_id or str(uuid.uuid4())
    
    # === LỚP 1: Rate limit ===
    if not check_rate_limit(session_id):
        return ChatResponse(
            session_id=session_id,
            reply="Mình thấy em nhắn nhiều quá rồi. Mình nghỉ ngơi một chút rồi nói chuyện tiếp nhé?",
        )
    
    # === LỚP 1: Crisis detection ===
    crisis_level = detect_crisis(req.message)
    if crisis_level > 0:
        # KHÔNG gọi LLM — trả template cố định + cảnh báo GVCN
        alert = format_teacher_alert(crisis_level, session_id)
        await notify_teacher(alert)

        # Lưu cảnh báo vào DB để dashboard GVCN xem lại
        await log_crisis_alert(
            session_id, crisis_level, alert["level_name"], alert["message"]
        )
        
        # Lưu vào DB
        await get_or_create_session(session_id)
        await append_message(session_id, "user", req.message)
        await append_message(session_id, "assistant", get_crisis_template())
        
        return ChatResponse(
            session_id=session_id,
            reply=get_crisis_template(),
            is_crisis=True,
        )
    
    # === LỚP 1: PII masking ===
    clean_message = mask_pii(req.message)
    
    # === LỚP 1: Prompt injection protection ===
    wrapped_message = wrap_user_message(clean_message)
    
    # === LỚP 2: Gọi LLM ===
    llm = get_llm()
    
    # Lấy lịch sử hội thoại
    history = await get_recent_messages(session_id, limit=10)
    history.append({"role": "user", "content": wrapped_message})
    
    try:
        response = await llm.chat(
            system=SYSTEM_PROMPT,
            messages=history,
            temperature=0.3,
            max_tokens=300,
        )
    except Exception as e:
        # Fallback nếu LLM lỗi
        response = "Xin lỗi, mình đang gặp sự cố kỹ thuật. Em thử nhắn lại sau nhé, hoặc nói chuyện với cô Dung hay người lớn em tin cậy."
        await log_blocked(session_id, f"LLM error: {str(e)}")
    
    # === LỚP 3: Output validation ===
    is_valid, reason = validate_output(response)
    if not is_valid:
        # Thử regenerate 1 lần
        try:
            response = await llm.chat(
                system=SYSTEM_PROMPT,
                messages=history,
                temperature=0.4,
                max_tokens=300,
            )
            is_valid, reason = validate_output(response)
            if not is_valid:
                # Vẫn fail — dùng fallback
                response = "Mình hiểu rồi. Em kể thêm cho mình nghe đi, mình đang lắng nghe đây."
        except:
            response = "Mình hiểu rồi. Em kể thêm cho mình nghe đi, mình đang lắng nghe đây."
        
        await log_blocked(session_id, reason)
    
    # Strip [USER] tags khỏi response (đề phòng LLM echo lại)
    response = re.sub(r'\[/?USER\]', '', response)
    
    # === Lưu vào DB ===
    await get_or_create_session(session_id)
    await append_message(session_id, "user", req.message)
    await append_message(session_id, "assistant", response)
    
    return ChatResponse(
        session_id=session_id,
        reply=response,
        is_crisis=False,
    )


@app.get("/api/stats", response_model=StatsResponse)
async def stats():
    """Thống kê tuần cho dashboard GVCN."""
    return await get_weekly_stats()


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "Ngườ bạn nhỏ AI"}


# Serve frontend
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")


@app.get("/")
async def root():
    """Trang chủ — web chat."""
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/dashboard.html")
async def dashboard():
    """Dashboard GVCN — thống kê tuần."""
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html")


@app.get("/dashboard")
async def dashboard():
    """Dashboard cho GVCN."""
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html")
