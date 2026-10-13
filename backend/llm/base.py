"""
Abstract base class cho LLM clients.
"""
from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    @abstractmethod
    async def chat(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 300,
    ) -> str:
        """Gửi prompt tới LLM, trả về chuỗi phản hồi."""
        pass
