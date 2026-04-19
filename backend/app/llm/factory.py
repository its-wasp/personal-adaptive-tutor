from app.llm.base_provider import BaseLLMProvider
from app.config import settings


def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER.lower() == "groq":
        from app.llm.groq_provider import GroqProvider
        return GroqProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
