"""
Lớp 1 — Lọc đầu vào: phát hiện khủng hoảng, che PII, chống injection, rate limit.
"""
import re
import time
import unicodedata
from collections import defaultdict
from backend.config import CRISIS_KEYWORDS, RATE_LIMIT_PER_HOUR


# ============ HELPERS ============

def normalize_text(text: str) -> str:
    """
    Bỏ dấu + lowercase + chuẩn hóa Telex.
    Ví dụ: "gieest nguoif" → "giet nguoi"
    """
    text = text.lower()
    
    # Bỏ dấu Unicode
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Xóa chữ cái lặp (Telex: gieest→giet, nguoif→nguoi)
    text = re.sub(r'([a-z])\1', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============ CRISIS DETECTION ============

# Mức 2 — khẩn cấp: tự tử + bạo lực (cả có dấu + không dấu)
CRITICAL_KW = [
    "muon chet", "tu tu", "chet di", "tu van", "tu giet", "ket lieu",
    "giet nguoi", "muon giet", "dam nguoi", "tan cong nguoi",
    "giet",  # "gieest" → normalize → "giet"
]

# Mức 1 — cảnh báo
WARNING_KW = [
    "khong muon song", "song chang co y nghia", "bien mat", "chan song",
    "danh nguoi", "lam hai nguoi khac", "bao luc", "tra thu", "muon danh",
    "giet chet", "giet may", "giet no", "giet han",
    "cat tay", "tu lam dau", "tu huy",
]


def detect_crisis(text: str) -> int:
    """
    So sánh cả dạng có dấu lẫn không dấu (đề phòng gõ Telex chưa convert).
    Trả về: 0 = an toàn, 1 = cảnh báo, 2 = khẩn cấp.
    """
    text_lower = text.lower()
    text_norm = normalize_text(text)

    # Mức 2
    if any(kw in text_lower for kw in [
        "muốn chết", "tự tử", "chết đi", "tự vẫn", "tự giết", "kết liễu",
        "giết người", "muốn giết", "đâm người", "tấn công người",
    ]):
        return 2
    if any(kw in text_norm for kw in CRITICAL_KW):
        return 2

    # Mức 1
    if any(kw in text_lower for kw in [
        "không muốn sống", "sống chẳng có ý nghĩa", "biến mất", "chán sống",
        "đánh người", "làm hại người khác", "bạo lực", "trả thù", "muốn đánh",
        "giết chết", "cắt tay", "tự làm đau",
    ]):
        return 1
    if any(kw in text_norm for kw in WARNING_KW):
        return 1

    # Fallback: file config
    for kw in CRISIS_KEYWORDS:
        if kw in text_lower or normalize_text(kw) in text_norm:
            return 1

    return 0


# ============ STRIP USER TAGS ============

def strip_user_tags(text: str) -> str:
    """Bỏ thẻ [USER]...[/USER] (đề phòng LLM echo lại)."""
    return re.sub(r'\[/?USER\]', '', text).strip()


# ============ PII MASKING ============

def mask_pii(text: str) -> str:
    phone_pattern = r'\b0\d{9,10}\b'
    text = re.sub(phone_pattern, '[SĐT_ĐÃ_CHE]', text)

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, '[EMAIL_ĐÃ_CHE]', text)

    addr_pattern = r'\b\d+\s+[A-Za-zÀ-ỹ\s]+(đường|phố|tổ|khu phố|ấp)\b'
    text = re.sub(addr_pattern, '[ĐỊA_CHỈ_ĐÃ_CHE]', text, flags=re.IGNORECASE)

    return text


# ============ PROMPT INJECTION ============

def wrap_user_message(text: str) -> str:
    return f"[USER]{text}[/USER]"


# ============ RATE LIMIT ============

_rate_limit_store = defaultdict(list)

def check_rate_limit(session_id: str) -> bool:
    now = time.time()
    hour_ago = now - 3600

    _rate_limit_store[session_id] = [
        t for t in _rate_limit_store[session_id] if t > hour_ago
    ]

    if len(_rate_limit_store[session_id]) >= RATE_LIMIT_PER_HOUR:
        return False

    _rate_limit_store[session_id].append(now)
    return True
