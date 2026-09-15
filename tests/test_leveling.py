"""Tests for the XP/level progression logic."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import calculate_level, calculate_xp_for_level, get_level_progress  # noqa: E402


def test_new_user_starts_at_level_1():
    assert calculate_level(0) == 1


def test_level_progress_is_consistent():
    level, xp_in, xp_needed = get_level_progress(0)
    assert level == 1
    assert xp_in == 0
    assert xp_needed == 50


def test_xp_for_level_interfaces():
    assert calculate_xp_for_level(1) == 0
    assert calculate_xp_for_level(2) == 50
    assert calculate_xp_for_level(3) == 200
    assert calculate_xp_for_level(4) == 450


def test_progression_is_monotonic():
    for xp in [0, 10, 49, 50, 51, 99, 200, 9999]:
        level, _, _ = get_level_progress(xp)
        assert level >= 1


def test_crossing_level_boundary():
    level_before, _, _ = get_level_progress(49)
    level_after, xp_in, _ = get_level_progress(50)
    assert level_before == 1
    assert level_after == 2
    assert xp_in == 0


def test_high_level_requires_more_xp():
    l1_gap = get_level_progress(60)[2]
    l10_gap = get_level_progress(5000)[2]
    assert l10_gap > l1_gap


def test_xp_in_level_never_negative():
    for xp in [0, 30, 200, 450, 1000]:
        _, xp_in, _ = get_level_progress(xp)
        assert xp_in >= 0