"""
Anthropic client — dùng Claude Haiku hoặc Sonnet.
"""
import httpx
from .base import LLMClient
from backend.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


class AnthropicClient(LLMClient):
    def __init__(self):
        self.api_key = ANTHROPIC_API_KEY
        self.model = ANTHROPIC_MODEL
        self.endpoint = "https://api.anthropic.com/v1/messages"
    
    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY chưa được cấu hình trong .env")
        
        payload = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.endpoint,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
