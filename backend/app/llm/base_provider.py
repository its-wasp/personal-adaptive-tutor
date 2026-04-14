from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """
        Send a list of messages to the LLM and return the response text.

        Args:
            messages: List of dicts with 'role' and 'content' keys.
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens in the response.
            json_mode: If True, ask the provider to constrain output to valid JSON.
                Providers that support it (Groq, OpenAI) will use server-side
                structured output; providers that don't can ignore this flag
                (we'll still fall back to the response parser).

        Returns:
            The LLM's response as a string.
        """
        pass
