"""
Gemini client — retry nhiều model + fallback Groq.
"""
import httpx
from .base import LLMClient
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL


# Danh sách model Gemini thử theo thứ tự ưu tiên (cho new users)
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
]


class GeminiClient(LLMClient):
    def __init__(self):
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY chưa được cấu hình trong .env. "
                "Lấy tại https://aistudio.google.com/app/apikey"
            )
        self.api_key = GEMINI_API_KEY
        self.preferred_model = GEMINI_MODEL or "gemini-3.5-flash-lite"
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def _try_gemini(self, model, messages, temperature, max_tokens, system_user_msg=None):
        """Thử 1 model Gemini. Trả về text hoặc None nếu lỗi."""
        payload = {
            "contents": [],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_JAILBREAK", "threshold": "BLOCK_LOW_AND_ABOVE"},
            ],
        }

        # Gemini API chưa hỗ trợ role="system" trong contents — đổi hết về user/model
        msgs = list(messages)
        if system_user_msg and msgs:
            msgs = [dict(msgs[0], content=system_user_msg["content"] + msgs[0]["content"])] + msgs[1:]

        for msg in msgs:
            role = msg["role"] if msg["role"] in ("user", "model") else "user"
            payload["contents"].append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        url = self.endpoint.format(model=model)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params={"key": self.api_key}, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and parts[0].get("text"):
                        return parts[0]["text"]
            return None

    async def _try_groq(self, messages, temperature, max_tokens):
        """Fallback sang Groq API nếu Gemini down."""
        if not GROQ_API_KEY:
            return None

        payload = {
            "model": GROQ_MODEL or "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            return None

    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        # Chuyển system prompt vào user turn đầu (Gemini API chưa nhận role="system")
        system_user_msg = {
            "role": "user",
            "content": f"(Hướng dẫn hành xử của bạn: {system})\n\n---\n\n",
        }

        # Thử model ưu tiên trước
        if self.preferred_model in GEMINI_MODELS:
            models_to_try = [self.preferred_model] + [m for m in GEMINI_MODELS if m != self.preferred_model]
        else:
            models_to_try = GEMINI_MODELS

        for attempt in range(2):  # 2 vòng: vòng 2 retry các model bị 503
            for model in models_to_try:
                try:
                    result = await self._try_gemini(
                        model, messages, temperature, max_tokens, system_user_msg
                    )
                    if result:
                        return result
                except (httpx.TimeoutException, httpx.ConnectError):
                    continue  # Thử model tiếp theo
                except Exception:
                    continue
            if attempt == 0:
                import asyncio
                await asyncio.sleep(2)  # Chờ 2s trước khi retry

        # Fallback sang Groq
        groq_messages = [{"role": "system", "content": system}] + messages
        groq_result = await self._try_groq(groq_messages, temperature, max_tokens)
        if groq_result:
            return groq_result

        raise RuntimeError("Tất cả LLM providers đều không phản hồi. Vui lòng thử lại sau.")
