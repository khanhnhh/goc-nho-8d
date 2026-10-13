"""
Ollama client — chạy local, miễn phí, không cần API key.
Cần cài Ollama trước: https://ollama.com
Pull model: ollama pull qwen2.5 (hỗ trợ tiếng Việt)
"""
import httpx
from .base import LLMClient

OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5"


class OllamaClient(LLMClient):
    def __init__(self, model: str = OLLAMA_MODEL, endpoint: str = OLLAMA_ENDPOINT):
        self.model = model
        self.endpoint = endpoint

    async def chat(self, system, messages, temperature=0.3, max_tokens=300):
        # Kiểm tra Ollama đang chạy
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                check = await client.get("http://localhost:11434/api/tags")
                if check.status_code != 200:
                    raise RuntimeError("Ollama chưa chạy. Hãy chạy: ollama serve")
        except httpx.ConnectError:
            raise RuntimeError(
                "Không kết nối được Ollama (http://localhost:11434). "
                "Hãy cài Ollama từ https://ollama.com và chạy 'ollama serve'."
            )

        # Format messages cho Ollama
        ollama_messages = [{"role": "system", "content": system}] + messages

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
