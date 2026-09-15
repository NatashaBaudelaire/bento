"""Pure gamification logic (no DB, no Discord dependencies)."""

from datetime import timedelta


def check_answer(question, content):
    """Evaluate a user's answer against a question dict.

    Returns (is_correct, user_answer, correct_value).
    Handles multiple-choice (by letter) and open questions.
    """
    question_type = question.get("type", "open")
    correct_value = str(question.get("correct", "")).strip().lower()
    content = content.lower().strip()

    if question_type == "multiple":
        valid_letters = {k.lower() for k in (question.get("alternatives") or {})}
        user_answer = content[:1]
        correct_letter = correct_value[:1]
        is_correct = user_answer in valid_letters and user_answer == correct_letter
        return is_correct, user_answer, correct_value

    return content == correct_value, content, correct_value


def xp_for_correct(mode):
    """XP awarded for a correct answer in a given mode."""
    return 20 if mode == "daily" else 5


def consecutive_days(dates):
    """Count consecutive days at the start of a DESC-sorted date list."""
    if not dates:
        return 0

    count = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            count += 1
        else:
            break
    return count


def achievement_criteria(data, streak=0):
    """Return {achievement_key: met?} for a user's profile data dict."""
    xp = data.get("xp", 0)
    correct = data.get("correct", 0)
    total = data.get("total_answers", 0)
    level = data.get("level", 1)

    return {
        "first_quiz": total >= 1,
        "correct_10": correct >= 10,
        "correct_50": correct >= 50,
        "xp_100": xp >= 100,
        "xp_500": xp >= 500,
        "xp_1000": xp >= 1000,
        "level_5": level >= 5,
        "level_10": level >= 10,
        "streak_3": streak >= 3,
    }