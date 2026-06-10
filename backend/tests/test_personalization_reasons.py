"""Unit tests for build_reasons (app/llm/personalization_reasons.py)."""
from app.llm.personalization_reasons import build_reasons


def labels(reasons):
    return [r["label"] for r in reasons]


class TestBuildReasons:
    def test_none_profile_returns_empty(self):
        assert build_reasons(None, None) == []

    def test_empty_profile_returns_empty(self):
        assert build_reasons({}, None) == []

    def test_learning_style_reason(self):
        reasons = build_reasons({"learning_style": "EXAMPLE_FIRST"}, None)
        assert "Example-first" in labels(reasons)

    def test_each_reason_has_label_and_detail(self):
        reasons = build_reasons({"learning_style": "VISUAL"}, None)
        assert reasons
        for r in reasons:
            assert r["label"] and r["detail"]

    def test_weaknesses_and_strengths(self):
        reasons = build_reasons(
            {"weaknesses": ["Recursion"], "strengths": ["Arrays"]}, None
        )
        assert "Extra care" in labels(reasons)
        assert "Built on strengths" in labels(reasons)

    def test_learner_summary_adds_remembered(self):
        reasons = build_reasons({"learner_summary": "Likes analogies"}, None)
        assert "Remembered you" in labels(reasons)

    def test_retrieved_chunks_add_grounded(self):
        reasons = build_reasons(
            {"learning_style": "READING"},
            [{"text": "a"}, {"text": "b"}],
        )
        grounded = [r for r in reasons if r["label"] == "Grounded"]
        assert grounded
        assert "2 reference explanations" in grounded[0]["detail"]

    def test_single_chunk_singular_wording(self):
        reasons = build_reasons({"learning_style": "READING"}, [{"text": "a"}])
        grounded = next(r for r in reasons if r["label"] == "Grounded")
        assert "1 reference explanation." in grounded["detail"]

    def test_capped_at_four(self):
        # Provide enough signals to exceed 4 reasons; expect truncation.
        profile = {
            "learning_style": "EXAMPLE_FIRST",
            "weaknesses": ["Recursion", "Graphs"],
            "strengths": ["Arrays"],
            "learner_summary": "summary",
            "pace_preference": "QUICK",
        }
        reasons = build_reasons(profile, [{"text": "a"}])
        assert len(reasons) == 4

    def test_quick_pace_reason(self):
        reasons = build_reasons({"pace_preference": "QUICK"}, None)
        assert "Concise pace" in labels(reasons)
