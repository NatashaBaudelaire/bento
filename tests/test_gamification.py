"""Tests for pure gamification logic."""
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.gamification import (  # noqa: E402
    check_answer,
    xp_for_correct,
    consecutive_days,
    achievement_criteria,
)


# ---------- check_answer ----------

def test_multiple_choice_correct_letter():
    q = {"type": "multiple", "alternatives": {"A": "x", "B": "y", "C": "z", "D": "w"}, "correct": "B"}
    assert check_answer(q, "B") == (True, "b", "b")


def test_multiple_choice_wrong_letter():
    q = {"type": "multiple", "alternatives": {"A": "x", "B": "y", "C": "z", "D": "w"}, "correct": "B"}
    assert check_answer(q, "C")[0] is False


def test_multiple_choice_lowercase_letter():
    q = {"type": "multiple", "alternatives": {"A": "x", "B": "y", "C": "z", "D": "w"}, "correct": "B"}
    assert check_answer(q, "b") == (True, "b", "b")


def test_multiple_choice_invalid_letter():
    q = {"type": "multiple", "alternatives": {"A": "x", "B": "y", "C": "z", "D": "w"}, "correct": "B"}
    assert check_answer(q, "Q")[0] is False


def test_open_question_exact_match():
    q = {"type": "open", "correct": "Photosynthesis"}
    assert check_answer(q, "photosynthesis") == (True, "photosynthesis", "photosynthesis")


def test_open_question_wrong_answer():
    q = {"type": "open", "correct": "Photosynthesis"}
    assert check_answer(q, "Respiration")[0] is False


def test_missing_alternatives_treated_as_open():
    q = {"type": "multiple", "alternatives": None, "correct": "A"}
    assert check_answer(q, "A")[0] is False


# ---------- xp_for_correct ----------

def test_xp_daily():
    assert xp_for_correct("daily") == 20


def test_xp_quiz():
    assert xp_for_correct("study") == 5


# ---------- consecutive_days ----------

def test_no_dates():
    assert consecutive_days([]) == 0


def test_single_day():
    assert consecutive_days([date(2026, 1, 3)]) == 1


def test_three_consecutive_days():
    dates = [date(2026, 1, 3), date(2026, 1, 2), date(2026, 1, 1)]
    assert consecutive_days(dates) == 3


def test_broken_streak():
    dates = [date(2026, 1, 3), date(2026, 1, 1)]
    assert consecutive_days(dates) == 1


def test_unsorted_dates_only_count_from_start():
    dates = [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 4)]
    # First element is the newest (5); the next is 6 which is OLDER in desc order -> breaks
    assert consecutive_days(dates) == 1


# ---------- achievement_criteria ----------

def test_new_user_no_achievements():
    c = achievement_criteria({"xp": 0, "correct": 0, "total_answers": 0, "level": 1}, streak=0)
    assert not any(c.values())


def test_first_quiz_unlocked_after_one_answer():
    c = achievement_criteria({"xp": 5, "correct": 1, "total_answers": 1, "level": 1}, streak=0)
    assert c["first_quiz"] is True


def test_xp_thresholds():
    c = achievement_criteria({"xp": 100, "correct": 0, "total_answers": 0, "level": 2}, streak=0)
    assert c["xp_100"] is True
    assert c["xp_500"] is False


def test_streak_achievement():
    c = achievement_criteria({"xp": 0, "correct": 0, "total_answers": 0, "level": 1}, streak=3)
    assert c["streak_3"] is True


def test_level_achievements():
    c = achievement_criteria({"xp": 5000, "correct": 0, "total_answers": 0, "level": 10}, streak=0)
    assert c["level_10"] is True