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

        # Strategy 4: repair raw control characters inside string values, then
        # parse normally. This is the common failure — a model writing a
        # multi-line code sample emits a real newline mid-string, which is
        # invalid JSON but trivially fixable.
        result = _try_parse(_escape_raw_control_chars(block))
        if result:
            return result

        # Strategy 5: last resort, pull the key/value pairs out by hand.
        result = _extract_json_with_unescaped_newlines(block)
        if result:
            return result

    # All strategies failed
    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:500]}")


def _escape_raw_control_chars(block: str) -> str:
    """
    Escape control characters that appear raw inside JSON string values.

    A model writing a multi-line code sample inside an "explanation" string
    emits a literal newline, which json.loads rejects. Escaping those in place
    keeps everything else — crucially the escape sequences the model got right
    — intact, so the result decodes through the normal parser rather than being
    reconstructed by hand.

    Walks character by character tracking string state, because a regex cannot
    tell a newline inside a string from one between fields.
    """
    ESCAPES = {"\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}

    out = []
    in_string = False
    escaped = False

    for ch in block:
        if escaped:
            # Previous character was a backslash, so this one is part of an
            # escape sequence the model already wrote correctly. Leave it.
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in ESCAPES:
            out.append(ESCAPES[ch])
            continue
        if in_string and ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
            continue
        out.append(ch)

    return "".join(out)


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


TITLE_RE = re.compile(r"^[ \t]*TITLE[ \t]*:[ \t]*(.+?)[ \t]*$", re.MULTILINE | re.IGNORECASE)
SEPARATOR_RE = re.compile(r"^[ \t]*-{3,}[ \t]*$", re.MULTILINE)


def _strip_outer_fence(text: str) -> str:
    """Drop a code fence wrapping the entire reply, if the model added one."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*\n?", "", stripped)
        stripped = re.sub(r"\n?\s*```\s*$", "", stripped)
    return stripped


def _parse_delimited_explanation(raw: str) -> dict | None:
    """
    Parse the TITLE / --- / body format the explanation prompt asks for.

    Returns None when the shape isn't present, so the caller can fall back to
    JSON — older sessions and any model that ignores the instruction still work.
    """
    text = _strip_outer_fence(raw)
    title_match = TITLE_RE.search(text)
    if not title_match:
        return None

    title = title_match.group(1).strip().strip('"').strip()
    remainder = text[title_match.end():]

    separator = SEPARATOR_RE.search(remainder)
    if separator:
        remainder = remainder[separator.end():]

    explanation = remainder.strip()
    if not title or not explanation:
        return None
    return {"title": title, "explanation": explanation}


def _decode_over_escaped(text: str) -> str:
    """
    Repair a reply whose newlines arrived as the two characters backslash-n.

    Happens when a model is told its previous output was invalid JSON and
    over-corrects by escaping the escape. The result parses cleanly but renders
    as one unbroken paragraph.

    Deliberately conservative: only fires when literal sequences clearly
    outnumber real newlines, so an explanation that legitimately discusses
    escape sequences is left alone.
    """
    literal = text.count("\\n")
    if literal < 3 or text.count("\n") >= literal:
        return text
    return text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")


def parse_explanation_response(raw_response: str) -> dict:
    """
    Parse an opening explanation into {title, explanation}.

    Prefers the delimited format the prompt asks for and falls back to JSON.
    Both title and explanation must be non-empty: blank fields used to produce
    sessions whose opening message was empty, after which the model invented
    context on the first real turn.
    """
    result = _parse_delimited_explanation(raw_response)
    if result is None:
        result = _extract_json(raw_response)

    title = (result.get("title") or "").strip()
    explanation = _decode_over_escaped((result.get("explanation") or "").strip())
    if not title or not explanation:
        raise ValueError(
            f"Explanation response missing required fields (title/explanation): {result}"
        )
    result["title"] = title
    result["explanation"] = explanation
    return result


def parse_quiz_response(raw_response: str) -> dict:
    """
    Parse a quiz response and enforce the minimum contract: question,
    options (dict of 4 choices), and correct_option. Missing fields
    trigger a retry rather than a half-populated Quiz row.
    """
    result = _extract_json(raw_response)
    question = (result.get("question") or "").strip()
    options = result.get("options")
    correct = result.get("correct_option")
    if not question or not isinstance(options, dict) or len(options) < 2 or not correct:
        raise ValueError(
            f"Quiz response missing required fields (question/options/correct_option): {result}"
        )
    result["question"] = question
    return result
