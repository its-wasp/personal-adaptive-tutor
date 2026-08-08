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
