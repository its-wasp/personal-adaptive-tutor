"""
Unit tests for the SM-2 spaced-repetition math
(app/services/spaced_repetition_service.py).

We drive the pure ``update_after_review`` logic with an in-memory
``ConceptMastery`` (no DB session needed — only attributes are mutated) and a
mock ``db`` whose ``.commit()`` is a no-op.
"""
from unittest.mock import MagicMock

import pytest

from app.models.concept_mastery import ConceptMastery
from app.services.spaced_repetition_service import SpacedRepetitionService


@pytest.fixture
def service():
    return SpacedRepetitionService(db=MagicMock())


def make_mastery(mastery_level=0.5, ease_factor=2.5, review_interval_days=1.0):
    return ConceptMastery(
        mastery_level=mastery_level,
        ease_factor=ease_factor,
        review_interval_days=review_interval_days,
    )


class TestIntervalProgression:
    def test_first_correct_moves_1_to_6(self):
        m = make_mastery(review_interval_days=1.0)
        service = SpacedRepetitionService(db=MagicMock())
        service.update_after_review(m, is_correct=True)
        assert m.review_interval_days == 6.0

    def test_second_correct_multiplies_by_ease_factor(self, service):
        m = make_mastery(review_interval_days=6.0, ease_factor=2.5)
        service.update_after_review(m, is_correct=True)
        # 6 * new_ease_factor, rounded to 1 dp; new EF is >= 2.5 for a correct answer.
        assert m.review_interval_days == round(6.0 * m.ease_factor, 1)
        assert m.review_interval_days > 6.0

    def test_incorrect_resets_interval_to_one_day(self, service):
        m = make_mastery(review_interval_days=42.0)
        service.update_after_review(m, is_correct=False)
        assert m.review_interval_days == 1.0


class TestEaseFactor:
    def test_ease_factor_never_below_floor(self, service):
        m = make_mastery(ease_factor=1.3)
        # Repeated wrong answers must never push EF under the 1.3 SM-2 floor.
        for _ in range(5):
            service.update_after_review(m, is_correct=False)
        assert m.ease_factor >= 1.3

    def test_high_mastery_correct_increases_ease_factor(self, service):
        # mastery_level >= 0.7 maps to quality 5, which nudges EF upward.
        m = make_mastery(mastery_level=0.9, ease_factor=2.5)
        service.update_after_review(m, is_correct=True)
        assert m.ease_factor > 2.5


class TestSchedulingSideEffects:
    def test_sets_next_review_after_last_reviewed(self, service):
        m = make_mastery()
        service.update_after_review(m, is_correct=True)
        assert m.last_reviewed_at is not None
        assert m.next_review_at is not None
        assert m.next_review_at > m.last_reviewed_at

    def test_commit_is_called(self):
        db = MagicMock()
        service = SpacedRepetitionService(db=db)
        service.update_after_review(make_mastery(), is_correct=True)
        db.commit.assert_called_once()
