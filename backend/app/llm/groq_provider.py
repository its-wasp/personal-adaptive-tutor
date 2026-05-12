from groq import Groq, BadRequestError
from app.llm.base_provider import BaseLLMProvider
from app.config import settings


class GroqProvider(BaseLLMProvider):

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Groq's JSON mode forces the model to emit a single valid JSON object.
        # Groq requires the word "json" to appear somewhere in the messages —
        # our structured prompts already do (they explicitly ask for JSON),
        # so no extra shim needed.
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            # Groq server-side JSON validator rejected the model's output
            # (code: json_validate_failed). Surface as ValueError so the
            # retry/parse-failure path in callers handles it uniformly —
            # services stay provider-agnostic.
            code = None
            try:
                code = (e.body or {}).get("error", {}).get("code")
            except AttributeError:
                pass
            if code == "json_validate_failed":
                raise ValueError(f"Groq JSON validation failed: {e}") from e
            raise

        return response.choices[0].message.content
