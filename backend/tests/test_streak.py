"""
Unit tests for study-streak derivation
(app/services/learner_profile_service.compute_streak).

compute_streak is deliberately a pure function over dates, so every calendar
edge case is exercised here without a database or a fixed clock.
"""
from datetime import date, timedelta

from app.services.learner_profile_service import compute_streak


TODAY = date(2026, 7, 10)


def days_ago(*offsets):
    return [TODAY - timedelta(days=n) for n in offsets]


class TestStreakLength:
    def test_no_activity_is_zero(self):
        assert compute_streak([], today=TODAY) == 0

    def test_active_today_only(self):
        assert compute_streak(days_ago(0), today=TODAY) == 1

    def test_consecutive_run(self):
        assert compute_streak(days_ago(0, 1, 2, 3), today=TODAY) == 4

    def test_stops_at_the_first_gap(self):
        # Active today, yesterday, then a missed day before that.
        assert compute_streak(days_ago(0, 1, 3, 4), today=TODAY) == 2

    def test_unordered_input(self):
        assert compute_streak(days_ago(2, 0, 1), today=TODAY) == 3

    def test_duplicate_dates_count_once(self):
        assert compute_streak(days_ago(0, 0, 0, 1), today=TODAY) == 2

    def test_none_entries_are_ignored(self):
        assert compute_streak([None, *days_ago(0, 1)], today=TODAY) == 2


class TestStreakCurrency:
    def test_yesterday_still_counts_as_current(self):
        """A streak shouldn't die at midnight before the learner can study."""
        assert compute_streak(days_ago(1, 2, 3), today=TODAY) == 3

    def test_two_days_ago_breaks_the_streak(self):
        assert compute_streak(days_ago(2, 3, 4), today=TODAY) == 0

    def test_long_dormant_history_is_zero(self):
        assert compute_streak(days_ago(40, 41, 42), today=TODAY) == 0
