"""
Unit tests for the shared structured-generation retry ladder
(app/llm/structured.generate_structured).

Driven by a fake provider that replays a scripted sequence of outputs, so the
retry behaviour is pinned without touching Groq. These guard the extraction
that pulled two near-identical private methods out of ChatService and
QuizService.
"""
import pytest

from app.llm.response_parser import parse_explanation_response, parse_quiz_response
from app.llm.structured import generate_structured


GOOD_EXPLANATION = '{"title": "Arrays", "explanation": "Contiguous memory."}'
GOOD_QUIZ = (
    '{"question": "Q?", "options": {"A": "a", "B": "b"}, "correct_option": "A"}'
)


class FakeLLM:
    """Replays `outputs` in order; an Exception entry is raised instead."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, messages, temperature=0.7, max_tokens=2048, json_mode=False):
        self.calls.append(
            {"temperature": temperature, "json_mode": json_mode, "messages": list(messages)}
        )
        result = self.outputs.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def run(llm, **overrides):
    kwargs = {
        "parse": parse_explanation_response,
        "correction": "reply with JSON only",
        "failure_message": "could not parse",
    }
    kwargs.update(overrides)
    return generate_structured(llm, [{"role": "user", "content": "explain arrays"}], **kwargs)


class TestFirstAttempt:
    def test_valid_output_returns_immediately(self):
        llm = FakeLLM([GOOD_EXPLANATION])
        assert run(llm)["title"] == "Arrays"
        assert len(llm.calls) == 1

    def test_json_mode_is_requested(self):
        llm = FakeLLM([GOOD_EXPLANATION])
        run(llm)
        assert llm.calls[0]["json_mode"] is True


class TestRetry:
    def test_malformed_output_triggers_one_retry(self):
        llm = FakeLLM(["not json at all", GOOD_EXPLANATION])
        assert run(llm)["title"] == "Arrays"
        assert len(llm.calls) == 2

    def test_retry_runs_cooler(self):
        llm = FakeLLM(["not json at all", GOOD_EXPLANATION])
        run(llm)
        assert llm.calls[1]["temperature"] < llm.calls[0]["temperature"]

    def test_retry_replays_the_bad_output_and_the_correction(self):
        llm = FakeLLM(["garbage", GOOD_EXPLANATION])
        run(llm)
        roles = [m["role"] for m in llm.calls[1]["messages"]]
        assert roles == ["user", "assistant", "user"]
        assert llm.calls[1]["messages"][1]["content"] == "garbage"
        assert llm.calls[1]["messages"][2]["content"] == "reply with JSON only"

    def test_provider_rejection_has_no_output_to_replay(self):
        """
        Groq's server-side validator raises before returning text, so there is
        no assistant turn to show the model on the retry.
        """
        llm = FakeLLM([ValueError("json_validate_failed"), GOOD_EXPLANATION])
        run(llm)
        roles = [m["role"] for m in llm.calls[1]["messages"]]
        assert roles == ["user", "user"]

    def test_incomplete_json_is_treated_as_malformed(self):
        # Parses as JSON but violates the contract — must still retry.
        llm = FakeLLM(['{"title": "T", "explanation": ""}', GOOD_EXPLANATION])
        assert run(llm)["explanation"] == "Contiguous memory."
        assert len(llm.calls) == 2


class TestGivingUp:
    def test_second_failure_raises_the_friendly_message(self):
        llm = FakeLLM(["nope", "still nope"])
        with pytest.raises(ValueError, match="could not parse"):
            run(llm)

    def test_original_error_is_chained(self):
        llm = FakeLLM(["nope", "still nope"])
        with pytest.raises(ValueError) as exc:
            run(llm)
        assert exc.value.__cause__ is not None

    def test_never_attempts_more_than_twice(self):
        llm = FakeLLM(["nope", "still nope"])
        with pytest.raises(ValueError):
            run(llm)
        assert len(llm.calls) == 2


class TestQuizPath:
    def test_custom_temperatures_are_honoured(self):
        llm = FakeLLM(["bad", GOOD_QUIZ])
        generate_structured(
            llm,
            [{"role": "user", "content": "make a quiz"}],
            parse=parse_quiz_response,
            correction="json only",
            failure_message="bad quiz",
            temperature=0.8,
            retry_temperature=0.3,
        )
        assert [c["temperature"] for c in llm.calls] == [0.8, 0.3]
