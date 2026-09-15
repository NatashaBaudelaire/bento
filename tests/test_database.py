"""Tests for the database access layer (with mocked pool)."""
import sys
import os
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

import database.database as db  # noqa: E402


class _Acquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        return False


class _FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


@pytest.fixture
def fake_conn(monkeypatch):
    """Mock the pool with a disposable connection mock."""
    conn = AsyncMock()
    pool = _FakePool(conn)
    monkeypatch.setattr(db, "get_pool", AsyncMock(return_value=pool))
    return conn


# ---------- get_xp ----------

@pytest.mark.asyncio
async def test_get_xp_returns_zero_for_missing_user(fake_conn):
    fake_conn.fetchval = AsyncMock(return_value=None)
    assert await db.get_xp(999999) == 0


@pytest.mark.asyncio
async def test_get_xp_returns_existing_value(fake_conn):
    fake_conn.fetchval = AsyncMock(return_value=250)
    assert await db.get_xp(123) == 250


# ---------- profile data ----------

@pytest.mark.asyncio
async def test_profile_data_for_new_user_returns_zeros(fake_conn):
    fake_conn.fetchrow = AsyncMock(side_effect=[None, {"total": 0, "correct": None, "wrong": None}, None])
    data = await db.get_profile_data(999)
    assert data["xp"] == 0
    assert data["total_answers"] == 0
    assert data["correct"] == 0
    assert data["wrong"] == 0
    assert data["answers_today"] == 0


@pytest.mark.asyncio
async def test_profile_data_existing_user(fake_conn):
    fake_conn.fetchrow = AsyncMock(
        side_effect=[
            {"total_xp": 120},
            {"total": 10, "correct": 7, "wrong": 3},
            {"answers_today": 4},
        ]
    )
    data = await db.get_profile_data(123)
    assert data == {"xp": 120, "total_answers": 10, "correct": 7, "wrong": 3, "answers_today": 4}


# ---------- daily ----------

@pytest.mark.asyncio
async def test_get_daily_answers_zero_when_no_row(fake_conn):
    fake_conn.fetchrow = AsyncMock(return_value=None)
    assert await db.get_daily_answers(123) == 0


# ---------- ranking ----------

@pytest.mark.asyncio
async def test_global_ranking_empty(fake_conn):
    fake_conn.fetch = AsyncMock(return_value=[])
    assert await db.get_global_ranking(limit=20) == []


# ---------- achievements ----------

@pytest.mark.asyncio
async def test_unlock_achievement_new_and_duplicate(fake_conn):
    fake_conn.fetchrow = AsyncMock(return_value={"id": 1})
    fake_conn.execute = AsyncMock(return_value="INSERT 0 1")
    assert await db.unlock_achievement(123, "first_quiz") is True

    fake_conn.execute = AsyncMock(return_value="INSERT 0 0")
    assert await db.unlock_achievement(123, "first_quiz") is False


# ---------- missions ----------

@pytest.mark.asyncio
async def test_update_mission_progress_returns_only_completed(fake_conn):
    fake_conn.fetch = AsyncMock(
        return_value=[
            {"id": 1, "name": "Answer 5 Questions", "reward_xp": 25, "completed": True}
        ]
    )
    missions = await db.update_mission_progress(123, "Answer 5 Questions", 1)
    assert len(missions) == 1
    assert missions[0]["completed"] is True