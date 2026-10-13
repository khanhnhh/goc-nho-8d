"""
OpenAI client — dùng GPT-4o-mini hoặc các model rẻ khác.
"""
import httpx
from .base import LLMClient
from backend.config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIClient(LLMClient):
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.endpoint = "https://api.openai.com/v1/chat/completions"
    
    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình trong .env")
        
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
