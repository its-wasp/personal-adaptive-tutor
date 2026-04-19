from groq import Groq
from app.llm.base_provider import BaseLLMProvider
from app.config import settings


class GroqProvider(BaseLLMProvider):

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
