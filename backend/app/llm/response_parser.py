import json
import re


def _try_parse(text: str) -> dict | None:
    """Try to parse JSON, return None on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _extract_json(raw: str) -> dict:
    """
    Try multiple strategies to extract JSON from an LLM response.
    LLMs often wrap JSON in markdown fences, add extra text,
    or produce JSON with unescaped newlines in string values.
    """
    # Strategy 1: Direct parse
    result = _try_parse(raw)
    if result:
        return result

    # Strategy 2: Extract from ```json ... ``` fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
    if match:
        result = _try_parse(match.group(1))
        if result:
            return result

    # Strategy 3: Find the first { ... } block and try parsing
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        block = match.group(0)
        result = _try_parse(block)
        if result:
            return result

        # Strategy 4: LLMs often produce JSON with unescaped newlines in strings.
        # Try to extract key-value pairs manually for known structures.
        result = _extract_json_with_unescaped_newlines(block)
        if result:
            return result

    # All strategies failed
    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:500]}")


def _extract_json_with_unescaped_newlines(block: str) -> dict | None:
    """
    Handle LLM JSON where string values contain literal newlines.
    Works for simple flat objects like {"title": "...", "explanation": "..."}.
    """
    result = {}
    # Match "key": "value" where value may span multiple lines
    # Find all keys first
    keys = re.findall(r'"(\w+)"\s*:', block)
    if not keys:
        return None

    for i, key in enumerate(keys):
        # Find the start of this key's value
        pattern = rf'"{re.escape(key)}"\s*:\s*"'
        match = re.search(pattern, block)
        if not match:
            continue

        value_start = match.end()

        # Find the closing quote — it's followed by either , "next_key": or }
        if i + 1 < len(keys):
            next_key = keys[i + 1]
            end_pattern = rf'"\s*,\s*"{re.escape(next_key)}"'
            end_match = re.search(end_pattern, block[value_start:])
            if end_match:
                value = block[value_start:value_start + end_match.start()]
            else:
                continue
        else:
            # Last key — find the last unescaped quote before }
            remaining = block[value_start:]
            # Find last " before the final }
            last_quote = remaining.rfind('"')
            if last_quote >= 0:
                value = remaining[:last_quote]
            else:
                continue

        result[key] = value

    return result if result else None


def parse_explanation_response(raw_response: str) -> dict:
    return _extract_json(raw_response)


def parse_quiz_response(raw_response: str) -> dict:
    return _extract_json(raw_response)
