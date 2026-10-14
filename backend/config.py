"""
Cấu hình dự án — đọc từ .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
ZALO_AI_API_KEY = os.getenv("ZALO_AI_API_KEY")
ZALO_AI_ENDPOINT = os.getenv("ZALO_AI_ENDPOINT")
FPT_AI_API_KEY = os.getenv("FPT_AI_API_KEY")
FPT_AI_ENDPOINT = os.getenv("FPT_AI_ENDPOINT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Teacher
TEACHER_EMAIL = os.getenv("TEACHER_EMAIL", "teacher@example.com")
TEACHER_EMAILS = [e.strip() for e in os.getenv("TEACHER_EMAILS", TEACHER_EMAIL).split(",") if e.strip()]
TEACHER_ZALO_WEBHOOK = os.getenv("TEACHER_ZALO_WEBHOOK")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# App
APP_NAME = os.getenv("APP_NAME", "Người bạn nhỏ AI")

# Session
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))

# Rate limit
RATE_LIMIT_PER_HOUR = 20

# File paths
PROMPT_FILE = BASE_DIR / "backend" / "prompts" / "system.md"
FEW_SHOTS_FILE = BASE_DIR / "backend" / "prompts" / "few_shots.json"
CRISIS_KEYWORDS_FILE = BASE_DIR / "config" / "crisis_keywords.txt"
BLACKLIST_FILE = BASE_DIR / "config" / "blacklist.txt"

# Load prompts and keywords
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

with open(CRISIS_KEYWORDS_FILE, "r", encoding="utf-8") as f:
    CRISIS_KEYWORDS = [line.strip() for line in f if line.strip()]

with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
    BLACKLIST = [line.strip() for line in f if line.strip()]
