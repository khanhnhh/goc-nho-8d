"""
FastAPI backend â trÃ¡i tim cá»§a há» thá»ng, Äiá»u phá»i 4 lá»p phÃ²ng thá»§.
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
from backend.notify.teacher import notify_teacher, get_email_logs
from backend.api.alerts import router as alerts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khá»i táº¡o DB khi startup."""
    await init_db()
    await cleanup_old_sessions()
    yield


app = FastAPI(
    title="NgườI bạn nhỏ AI â Chatbot há» trá»£ tÃ¢m lÃ½",
    description="Chatbot áº©n danh há» trá»£ tÃ¢m lÃ½ cho há»c sinh lá»p 8",
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
    Xá»­ lÃ½ 1 tin nháº¯n tá»« há»c sinh qua 4 lá»p phÃ²ng thá»§:
    1. Rate limit + crisis detection (Äáº§u vÃ o)
    2. PII masking + prompt injection protection
    3. Gá»i LLM vá»i system prompt
    4. Output validation + crisis response
    """
    
    # Táº¡o session ID náº¿u chÆ°a cÃ³
    session_id = req.session_id or str(uuid.uuid4())
    
    # === Lá»P 1: Rate limit ===
    if not check_rate_limit(session_id):
        return ChatResponse(
            session_id=session_id,
            reply="MÃ¬nh tháº¥y em nháº¯n nhiá»u quÃ¡ rá»i. MÃ¬nh nghá» ngÆ¡i má»t chÃºt rá»i nÃ³i chuyá»n tiáº¿p nhÃ©?",
        )
    
    # === Lá»P 1: Crisis detection ===
    crisis_level = detect_crisis(req.message)
    if crisis_level > 0:
        # KHÃNG gá»i LLM â tráº£ template cá» Äá»nh + cáº£nh bÃ¡o GVCN
        alert = format_teacher_alert(crisis_level, session_id)
        await notify_teacher(alert)

        # LÆ°u cáº£nh bÃ¡o vÃ o DB Äá» dashboard GVCN xem láº¡i
        await log_crisis_alert(
            session_id, crisis_level, alert["level_name"], alert["message"]
        )
        
        # LÆ°u vÃ o DB
        await get_or_create_session(session_id)
        await append_message(session_id, "user", req.message)
        await append_message(session_id, "assistant", get_crisis_template())
        
        return ChatResponse(
            session_id=session_id,
            reply=get_crisis_template(),
            is_crisis=True,
        )
    
    # === Lá»P 1: PII masking ===
    clean_message = mask_pii(req.message)
    
    # === Lá»P 1: Prompt injection protection ===
    wrapped_message = wrap_user_message(clean_message)
    
    # === Lá»P 2: Gá»i LLM ===
    llm = get_llm()
    
    # Láº¥y lá»ch sá»­ há»i thoáº¡i
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
        # Fallback náº¿u LLM lá»i
        response = "Xin lá»i, mÃ¬nh Äang gáº·p sá»± cá» ká»¹ thuáº­t. Em thá»­ nháº¯n láº¡i sau nhÃ©, hoáº·c nÃ³i chuyá»n vá»i cÃ´ Dung hay ngÆ°á» lá»n em tin cáº­y."
        await log_blocked(session_id, f"LLM error: {str(e)}")
    
    # === Lá»P 3: Output validation ===
    is_valid, reason = validate_output(response)
    if not is_valid:
        # Thá»­ regenerate 1 láº§n
        try:
            response = await llm.chat(
                system=SYSTEM_PROMPT,
                messages=history,
                temperature=0.4,
                max_tokens=300,
            )
            is_valid, reason = validate_output(response)
            if not is_valid:
                # Váº«n fail â dÃ¹ng fallback
                response = "MÃ¬nh hiá»u rá»i. Em ká» thÃªm cho mÃ¬nh nghe Äi, mÃ¬nh Äang láº¯ng nghe ÄÃ¢y."
        except:
            response = "MÃ¬nh hiá»u rá»i. Em ká» thÃªm cho mÃ¬nh nghe Äi, mÃ¬nh Äang láº¯ng nghe ÄÃ¢y."
        
        await log_blocked(session_id, reason)
    
    # Strip [USER] tags khá»i response (Äá» phÃ²ng LLM echo láº¡i)
    response = re.sub(r'\[/?USER\]', '', response)
    
    # === LÆ°u vÃ o DB ===
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
    """Thá»ng kÃª tuáº§n cho dashboard GVCN."""
    return await get_weekly_stats()


@app.get("/api/email-logs")
async def email_logs():
    """Láº¥y log gá»­i email gáº§n ÄÃ¢y."""
    return {"logs": get_email_logs()}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "NgườI bạn nhỏ AI"}


# Serve frontend
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")


@app.get("/")
async def root():
    """Trang chá»§ â web chat."""
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/dashboard.html")
async def dashboard_html():
    """Dashboard GVCN â thá»ng kÃª tuáº§n (URL cÅ©, giá»¯ Äá» tÆ°Æ¡ng thÃ­ch)."""
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html")


@app.get("/dashboard")
async def dashboard():
    """Dashboard cho GVCN (URL cÅ©, giá»¯ Äá» tÆ°Æ¡ng thÃ­ch)."""
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html")


@app.get("/thongke")
async def thongke():
    """Dashboard cho GVCN â URL chÃ­nh: /thongke."""
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html")
