import os
import json
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

# ==================================================
#  CONNECTION POOL
# ==================================================
async def get_pool():
    global _pool

    if _pool:
        try:
            async with _pool.acquire() as conn:
                await conn.execute("SELECT 1;")
            return _pool
        except Exception:
            print("⚠️ Pool disconnected — recreating...")

    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        max_size=10,
        command_timeout=30
    )

    print("🌐 Connection pool created!")
    return _pool


# ==================================================
#  USER MANAGEMENT
# ==================================================
async def register_user(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING;
        """, user_id)


async def get_xp(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT total_xp
            FROM users
            WHERE user_id=$1
        """, user_id)


async def add_xp(user_id, xp):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET total_xp = total_xp + $1
            WHERE user_id=$2
        """, xp, user_id)


# ==================================================
#  DAILY PROGRESS
# ==================================================
async def get_daily_answers(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT answers_today
            FROM daily_xp
            WHERE user_id=$1
              AND date_day = CURRENT_DATE
        """, user_id)

        return row["answers_today"] if row else 0


async def increment_daily_answer(user_id):
    # This function increments the count of daily answers for the user. It uses an UPSERT to either create a new record for today or update the existing one.
    pool = await get_pool()
    async with pool.acquire() as conn:
        # This SQL inserts a new row for today or updates the existing one.
        row = await conn.fetchrow("""
            INSERT INTO daily_xp (user_id, date_day, answers_today)
            VALUES ($1, CURRENT_DATE, 1)
            ON CONFLICT (user_id, date_day) 
            DO UPDATE SET answers_today = daily_xp.answers_today + 1
            RETURNING answers_today;
        """, user_id)
        
        return row["answers_today"]


# ==================================================
#  ANSWER HISTORY
# ==================================================
async def register_answer(
    user_id, question_text, q_type, alternatives,
    user_answer, correct_answer, is_correct, xp_gained, is_daily_10
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO answer_history
            (user_id, question_text, type, alternatives,
             user_answer, correct_answer, is_correct,
             xp_gained, is_daily_10)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        """,
            user_id,
            question_text,
            q_type,
            json.dumps(alternatives) if alternatives else None,
            user_answer,
            correct_answer,
            is_correct,
            xp_gained,
            is_daily_10
        )


# ==================================================
#  USER PROFILE DATA
# ==================================================
async def get_profile_data(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:

        # Fetch basic User Info
        row_user = await conn.fetchrow("""
            SELECT total_xp
            FROM users
            WHERE user_id = $1
        """, user_id)

        if not row_user:
            return None

        xp = row_user["total_xp"]

        # Fetch Stats (Total, Correct, Wrong).
        row_hist = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) AS correct,
                SUM(CASE WHEN is_correct = FALSE THEN 1 ELSE 0 END) AS wrong
            FROM answer_history
            WHERE user_id = $1
        """, user_id)

        total = row_hist["total"] or 0
        correct = row_hist["correct"] or 0
        wrong = row_hist["wrong"] or 0

        # Fetch Daily Progress.
        row_daily = await conn.fetchrow("""
            SELECT answers_today
            FROM daily_xp
            WHERE user_id = $1
              AND date_day = CURRENT_DATE
        """, user_id)

        answers_today = row_daily["answers_today"] if row_daily else 0

        return {
            "xp": xp,
            "total_answers": total,
            "correct": correct,
            "wrong": wrong,
            "answers_today": answers_today
        }