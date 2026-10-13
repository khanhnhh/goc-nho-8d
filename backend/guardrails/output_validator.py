"""
Lớp 3 — Kiểm duyệt đầu ra: blacklist, cấu trúc, LLM-as-judge.
"""
import re
from backend.config import BLACKLIST


# ============ BLACKLIST CHECK ============

def check_blacklist(text: str) -> tuple[bool, str]:
    """
    Kiểm tra xem câu trả lời có chứa từ/cụm từ cấm không.
    Trả về: (pass, reason) — pass=True nếu OK.
    """
    text_lower = text.lower()
    for word in BLACKLIST:
        if word.lower() in text_lower:
            return False, f"Chứa từ cấm: {word}"
    return True, ""


# ============ STRUCTURE CHECK ============

def check_structure(text: str) -> tuple[bool, str]:
    """
    Kiểm tra cấu trúc câu trả lời: độ dài, URL, mã kỳ dị, tags.
    """
    # Strip [USER] tags nếu LLM echo lại
    text = re.sub(r'\[/?USER\]', '', text)
    
    # Độ dài: tối đa 6 câu
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    if len(sentences) > 6:
        return False, f"Quá dài: {len(sentences)} câu (tối đa 6)"
    
    # Không chứa URL (trừ 111)
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    allowed_urls = ["111"]
    for url in urls:
        if not any(a in url for a in allowed_urls):
            return False, f"Chứa URL không cho phép: {url}"
    
    # Không chứa mã kỳ dị (base64, hex)
    if re.search(r'[A-Za-z0-9+/]{50,}={0,2}', text):
        return False, "Chứa chuỗi mã hóa nghi vấn"
    
    return True, ""


# ============ COMBINED VALIDATION ============

def validate_output(text: str) -> tuple[bool, str]:
    """
    Chạy tất cả kiểm tra đầu ra.
    Trả về: (pass, reason) — pass=True nếu OK.
    """
    ok, reason = check_blacklist(text)
    if not ok:
        return False, reason
    
    ok, reason = check_structure(text)
    if not ok:
        return False, reason
    
    return True, ""
