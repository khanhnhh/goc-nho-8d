"""
LLM client — abstraction để đổi provider mà không đụng code khác.
"""
from .base import LLMClient
from .mock import MockLLM
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient
from .groq_client import GroqClient

def get_llm() -> LLMClient:
    from backend.config import LLM_PROVIDER
    
    providers = {
        "mock": MockLLM,
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "ollama": OllamaClient,
        "gemini": GeminiClient,
        "groq": GroqClient,
    }
    
    provider = LLM_PROVIDER.lower()
    if provider not in providers:
        raise ValueError(f"LLM provider không hỗ trợ: {provider}. Chọn: {list(providers.keys())}")
    
    return providers[provider]()
