"""
Groq API client - mien phi, cuc nhanh, ho tro tieng Viet.
Lay API key tai: https://console.groq.com
"""
import httpx
from .base import LLMClient
from backend.config import GROQ_API_KEY, GROQ_MODEL


class GroqClient(LLMClient):
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
    
    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY chua duoc cau hinh trong .env. Lay tai https://console.groq.com")
        
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
