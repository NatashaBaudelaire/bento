"""Tests for the Training cog core answer-processing logic (especially the Daily bug)."""
import sys
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

import database.database as db  # noqa: E402
from cogs.training import Training  # noqa: E402


class FakeChannel:
    def __init__(self):
        self.messages = []

    async def send(self, text, **kwargs):
        self.messages.append(text)


def make_session(mode="daily", correct=0, answered=0, question=None):
    return {
        "mode": mode,
        "channel": FakeChannel(),
        "answered": answered,
        "correct": correct,
        "last": question or {
            "type": "multiple",
            "question": "What is 2+2?",
            "alternatives": {"A": "3", "B": "4", "C": "5", "D": "6"},
            "correct": "B",
        },
        "subject": "Math",
        "content": "Algebra",
    }


def patch_db(monkeypatch):
    """Neutralize all DB side-effects except the ones we assert on."""
    monkeypatch.setattr(db, "register_answer", AsyncMock())
    monkeypatch.setattr(db, "update_mission_progress", AsyncMock(return_value=[]))
    monkeypatch.setattr(db, "add_xp_to_missions", AsyncMock(return_value=[]))
    monkeypatch.setattr(db, "get_profile_data", AsyncMock(return_value={
        "xp": 0, "correct": 0, "total_answers": 0, "wrong": 0, "answers_today": 0,
    }))
    monkeypatch.setattr(db, "get_daily_completion_dates", AsyncMock(return_value=[]))
    monkeypatch.setattr(db, "unlock_achievement", AsyncMock(return_value=False))
    monkeypatch.setattr(db, "get_achievement_by_key", AsyncMock(return_value=None))


@pytest.fixture
def cog(monkeypatch):
    patch_db(monkeypatch)
    training = Training(None)
    training.send_question = AsyncMock()
    return training


@pytest.mark.asyncio
async def test_daily_wrong_answer_does_not_count(monkeypatch, cog):
    calls = {"increment": 0, "add_xp": 0}
    monkeypatch.setattr(db, "increment_daily_correct", AsyncMock(side_effect=lambda uid: calls.__setitem__("increment", calls["increment"] + 1) or 0))
    monkeypatch.setattr(db, "add_xp", AsyncMock(side_effect=lambda uid, xp: calls.__setitem__("add_xp", calls["add_xp"] + 1)))

    session = make_session(mode="daily", correct=0)
    msg = SimpleNamespace(content="A")  # wrong (correct is B)

    await cog._process_answer(msg, session, 123)

    assert calls["increment"] == 0
    assert calls["add_xp"] == 0
    assert session["correct"] == 0
    assert session["answered"] == 1
    assert any("Wrong" in m for m in session["channel"].messages)


@pytest.mark.asyncio
async def test_daily_correct_answer_counts_once(monkeypatch, cog):
    calls = {"increment": 0, "add_xp": 0}
    monkeypatch.setattr(db, "increment_daily_correct", AsyncMock(side_effect=lambda uid: calls.__setitem__("increment", calls["increment"] + 1) or 1))
    monkeypatch.setattr(db, "add_xp", AsyncMock(side_effect=lambda uid, xp: calls.__setitem__("add_xp", calls["add_xp"] + xp)))

    session = make_session(mode="daily", correct=0)
    msg = SimpleNamespace(content="B")  # correct

    await cog._process_answer(msg, session, 123)

    assert calls["increment"] == 1
    assert calls["add_xp"] == 20
    assert session["correct"] == 1


@pytest.mark.asyncio
async def test_quiz_correct_answer_gives_5_xp_no_daily_increment(monkeypatch, cog):
    calls = {"increment": 0, "add_xp": 0}
    monkeypatch.setattr(db, "increment_daily_correct", AsyncMock(side_effect=lambda uid: calls.__setitem__("increment", calls["increment"] + 1) or 0))
    monkeypatch.setattr(db, "add_xp", AsyncMock(side_effect=lambda uid, xp: calls.__setitem__("add_xp", calls["add_xp"] + xp)))

    session = make_session(mode="study", correct=0)
    msg = SimpleNamespace(content="B")

    await cog._process_answer(msg, session, 123)

    assert calls["increment"] == 0
    assert calls["add_xp"] == 5
    assert session["correct"] == 0


@pytest.mark.asyncio
async def test_daily_completion_at_10_correct(monkeypatch, cog):
    monkeypatch.setattr(db, "increment_daily_correct", AsyncMock(side_effect=lambda uid: 10))
    monkeypatch.setattr(db, "add_xp", AsyncMock())
    monkeypatch.setattr(db, "unlock_achievement", AsyncMock(return_value=False))

    end_session = AsyncMock()
    cog.end_session = end_session

    session = make_session(mode="daily", correct=9)
    msg = SimpleNamespace(content="B")

    await cog._process_answer(msg, session, 123)

    assert session["correct"] == 10
    end_session.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_command_prefix_message_ignored(monkeypatch, cog):
    monkeypatch.setattr(db, "add_xp", AsyncMock())
    session = make_session(mode="study")
    msg = SimpleNamespace(content="!othercommand")

    await cog._process_answer(msg, session, 123)

    assert session["answered"] == 0
    assert not session["channel"].messages


@pytest.mark.asyncio
async def test_stop_ends_session(monkeypatch, cog):
    end_session = AsyncMock()
    cog.end_session = end_session
    session = make_session(mode="study")

    await cog._process_answer(SimpleNamespace(content="!stop"), session, 123)
    end_session.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_open_question_checked(monkeypatch, cog):
    monkeypatch.setattr(db, "add_xp", AsyncMock())
    session = make_session(
        mode="study",
        question={"type": "open", "question": "What is H2O?", "correct": "water"},
    )
    msg = SimpleNamespace(content="water")
    await cog._process_answer(msg, session, 123)
    assert session["answered"] == 1
    assert any("Correct" in m for m in session["channel"].messages)