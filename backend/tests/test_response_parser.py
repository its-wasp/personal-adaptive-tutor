"""Unit tests for LLM JSON extraction/parsing (app/llm/response_parser.py)."""
import pytest

from app.llm.response_parser import (
    _extract_json,
    parse_explanation_response,
    parse_quiz_response,
)


class TestExtractJson:
    def test_direct_json(self):
        assert _extract_json('{"a": 1, "b": 2}') == {"a": 1, "b": 2}

    def test_json_in_code_fence(self):
        raw = 'Here you go:\n```json\n{"a": 1}\n```\nHope that helps!'
        assert _extract_json(raw) == {"a": 1}

    def test_json_in_bare_fence(self):
        raw = "```\n{\"a\": 1}\n```"
        assert _extract_json(raw) == {"a": 1}

    def test_json_with_surrounding_prose(self):
        raw = 'Sure! {"a": 1, "b": "two"} that is the answer.'
        assert _extract_json(raw) == {"a": 1, "b": "two"}

    def test_unescaped_newlines_in_values(self):
        raw = '{"title": "Intro", "explanation": "line one\nline two"}'
        result = _extract_json(raw)
        assert result["title"] == "Intro"
        assert "line one" in result["explanation"]

    def test_unparseable_raises(self):
        with pytest.raises(ValueError):
            _extract_json("there is no json here at all")


class TestParseExplanationResponse:
    def test_valid(self):
        result = parse_explanation_response('{"title": "T", "explanation": "E"}')
        assert result["title"] == "T"
        assert result["explanation"] == "E"

    def test_strips_whitespace(self):
        result = parse_explanation_response('{"title": "  T  ", "explanation": " E "}')
        assert result["title"] == "T"
        assert result["explanation"] == "E"

    def test_missing_field_raises(self):
        with pytest.raises(ValueError):
            parse_explanation_response('{"title": "T", "explanation": ""}')


class TestParseQuizResponse:
    def test_valid(self):
        raw = (
            '{"question": "Q?", "options": {"A": "a", "B": "b", "C": "c", "D": "d"},'
            ' "correct_option": "A"}'
        )
        result = parse_quiz_response(raw)
        assert result["question"] == "Q?"
        assert result["correct_option"] == "A"

    def test_too_few_options_raises(self):
        raw = '{"question": "Q?", "options": {"A": "a"}, "correct_option": "A"}'
        with pytest.raises(ValueError):
            parse_quiz_response(raw)

    def test_missing_correct_option_raises(self):
        raw = '{"question": "Q?", "options": {"A": "a", "B": "b"}}'
        with pytest.raises(ValueError):
            parse_quiz_response(raw)


class TestRawControlCharacterRepair:
    """
    Regression tests for explanations arriving with literal backslash-n.

    A model writing a multi-line code sample inside an "explanation" string can
    emit a real newline, which makes the payload invalid JSON. The recovery path
    used to hand back the raw substring without decoding escape sequences, so
    every correctly-escaped \\n in the same string reached the UI as two literal
    characters and the markdown rendered as one long line.
    """

    RAW_NEWLINE = (
        '{"title": "Binary Search", "explanation": "Fast.\\n\\n'
        "## Example\\n```python\\narr=[1,3,5]\\n```\\n"
        '\nOops, a raw newline above.\\n\\nDone!"}'
    )

    def test_recovers_from_a_raw_newline(self):
        result = _extract_json(self.RAW_NEWLINE)
        assert result["title"] == "Binary Search"

    def test_escape_sequences_are_decoded_not_passed_through(self):
        explanation = _extract_json(self.RAW_NEWLINE)["explanation"]
        assert "\\n" not in explanation, "escape sequences reached the UI verbatim"
        assert "\n" in explanation

    def test_markdown_fences_survive_recovery(self):
        explanation = _extract_json(self.RAW_NEWLINE)["explanation"]
        assert "```python" in explanation

    def test_raw_tab_is_repaired(self):
        raw = '{"title": "T", "explanation": "col1\tcol2\\nnext"}'
        assert "\t" in _extract_json(raw)["explanation"]

    def test_clean_json_is_untouched(self):
        raw = '{"title": "T", "explanation": "one\\ntwo\\n\\n```python\\nx=1\\n```"}'
        explanation = _extract_json(raw)["explanation"]
        assert "\\n" not in explanation
        assert explanation.count("\n") == 5

    def test_inner_fence_does_not_derail_a_fenced_response(self):
        raw = (
            "Here you go:\n```json\n"
            '{"title": "T", "explanation": "see\\n```python\\nx=1\\n```\\ndone"}'
            "\n```"
        )
        assert _extract_json(raw)["title"] == "T"
