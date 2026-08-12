"""
One retry ladder for every structured (JSON) generation.

The opening explanation and the quiz generator both ask the model for a single
JSON object, and both need identical recovery when it doesn't comply: retry
once at a lower temperature with an explicit correction, then give up with a
message the router can put in front of the user. The two had drifted into
near-identical private methods on their respective services.
"""
from typing import Callable


def generate_structured(
    llm,
    messages: list[dict],
    parse: Callable[[str], dict],
    correction: str,
    failure_message: str,
    temperature: float = 0.7,
    retry_temperature: float = 0.2,
    json_mode: bool = True,
) -> dict:
    """
    Generate JSON and parse it, retrying once on malformed output.

    `parse` signals unusable output by raising ValueError. So does the Groq
    provider when the server-side JSON validator rejects a generation
    (code: json_validate_failed), which is why both paths land here and get
    the same second chance.

    Raises ValueError carrying `failure_message` if the retry also fails; the
    original error is chained as __cause__ for the logs.
    """
    raw = None
    first_err: Exception | None = None
    try:
        raw = llm.generate(
            messages=messages, temperature=temperature, json_mode=json_mode
        )
        return parse(raw)
    except ValueError as e:
        first_err = e

    retry_messages = list(messages)
    # Only replay the bad output when there was some — a provider-side
    # rejection fails before returning any text.
    if raw is not None:
        retry_messages.append({"role": "assistant", "content": raw})
    retry_messages.append({"role": "user", "content": correction})

    try:
        raw_retry = llm.generate(
            messages=retry_messages, temperature=retry_temperature, json_mode=json_mode
        )
        return parse(raw_retry)
    except ValueError:
        raise ValueError(failure_message) from first_err
