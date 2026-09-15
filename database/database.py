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
            _pool = None

    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        max_size=10,
        command_timeout=30,
    )
    return _pool


# ==================================================
#  XP PROGRESSION
# ==================================================
def calculate_level(total_xp):
    """Calculate level from total XP using a progressive curve.

    Formula: level = floor(sqrt(total_xp / 50)) + 1
    Each level requires more XP than the previous one.
    """
    import math
    return int(math.sqrt(total_xp / 50)) + 1


def calculate_xp_for_level(level):
    """Return the total XP needed to reach a given level."""
    return 50 * (level - 1) ** 2


def get_level_progress(total_xp):
    """Return (level, xp_in_level, xp_needed) for display."""
    level = calculate_level(total_xp)
    xp_for_current = calculate_xp_for_level(level)
    xp_for_next = calculate_xp_for_level(level + 1)
    xp_in_level = total_xp - xp_for_current
    xp_needed = xp_for_next - xp_for_current
    return level, xp_in_level, xp_needed


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
        result = await conn.fetchval("""
            SELECT total_xp FROM users WHERE user_id = $1
        """, user_id)
        return result if result is not None else 0


async def add_xp(user_id, xp):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, total_xp)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET total_xp = users.total_xp + $2;
        """, user_id, xp)


# ==================================================
#  STUDY PREFERENCES
# ==================================================
async def save_study_preference(user_id, subject, content):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO study_preferences (user_id, subject, content, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET subject = $2, content = $3, updated_at = NOW();
        """, user_id, subject, content)


async def get_study_preference(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT subject, content FROM study_preferences WHERE user_id = $1
        """, user_id)
        if row:
            return {"subject": row["subject"], "content": row["content"]}
        return None


# ==================================================
#  DAILY PROGRESS
# ==================================================
async def get_daily_answers(user_id):
    """Return number of correct daily answers for today."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT answers_today
            FROM daily_xp
            WHERE user_id = $1 AND date_day = CURRENT_DATE
        """, user_id)
        return row["answers_today"] if row else 0


async def increment_daily_correct(user_id):
    """Increment the correct answers counter for today. Only call on correct answer."""
    pool = await get_pool()
    async with pool.acquire() as conn:
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
            is_daily_10,
        )


async def get_history(user_id, limit=5, offset=0):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT question_text, user_answer, correct_answer, is_correct, answered_at
            FROM answer_history
            WHERE user_id = $1
            ORDER BY answered_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)


async def get_history_count(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM answer_history WHERE user_id = $1
        """, user_id)


# ==================================================
#  USER PROFILE DATA
# ==================================================
async def get_profile_data(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row_user = await conn.fetchrow("""
            SELECT total_xp FROM users WHERE user_id = $1
        """, user_id)

        xp = row_user["total_xp"] if row_user else 0

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

        row_daily = await conn.fetchrow("""
            SELECT answers_today
            FROM daily_xp
            WHERE user_id = $1 AND date_day = CURRENT_DATE
        """, user_id)

        answers_today = row_daily["answers_today"] if row_daily else 0

        return {
            "xp": xp,
            "total_answers": total,
            "correct": correct,
            "wrong": wrong,
            "answers_today": answers_today,
        }


# ==================================================
#  RANKING
# ==================================================
async def get_global_ranking(limit=20):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT user_id, total_xp
            FROM users
            WHERE total_xp > 0
            ORDER BY total_xp DESC
            LIMIT $1
        """, limit)


async def get_daily_ranking(limit=20):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT d.user_id, d.answers_today, COALESCE(SUM(ah.xp_gained), 0) AS daily_xp
            FROM daily_xp d
            LEFT JOIN answer_history ah
                ON ah.user_id = d.user_id
                AND ah.answered_at::date = d.date_day
                AND ah.is_daily_10 = TRUE
            WHERE d.date_day = CURRENT_DATE
            GROUP BY d.user_id, d.answers_today
            ORDER BY daily_xp DESC, d.answers_today DESC
            LIMIT $1
        """, limit)


# ==================================================
#  ACHIEVEMENTS
# ==================================================
async def get_all_achievements():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, key, name, description, icon FROM achievements")
        return {row["key"]: dict(row) for row in rows}


async def get_achievement_by_key(key):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, key, name, description, icon FROM achievements WHERE key = $1",
            key,
        )
        return dict(row) if row else None


async def get_daily_completion_dates(user_id, daily_goal=10, limit=30):
    """Return a list of dates (desc) where the user completed the daily goal."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT date_day
            FROM daily_xp
            WHERE user_id = $1 AND answers_today >= $2
            ORDER BY date_day DESC
            LIMIT $3
        """, user_id, daily_goal, limit)
        return [r["date_day"] for r in rows]


async def get_user_achievements(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT a.key, a.name, a.description, a.icon, ua.unlocked_at
            FROM user_achievements ua
            JOIN achievements a ON a.id = ua.achievement_id
            WHERE ua.user_id = $1
        """, user_id)
        return {row["key"]: dict(row) for row in rows}


async def unlock_achievement(user_id, achievement_key):
    """Unlock an achievement for a user. Returns True if newly unlocked."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM achievements WHERE key = $1
        """, achievement_key)
        if not row:
            return False

        result = await conn.execute("""
            INSERT INTO user_achievements (user_id, achievement_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, achievement_id) DO NOTHING;
        """, user_id, row["id"])
        return result == "INSERT 0 1"


async def seed_achievements():
    """Insert default achievement definitions if they don't exist."""
    pool = await get_pool()
    achievements = [
        ("first_quiz", "First Steps", "Complete your first quiz question", "🎯"),
        ("first_daily", "Daily Warrior", "Complete your first daily challenge", "📅"),
        ("correct_10", "Sharp Mind", "Get 10 correct answers", "🧠"),
        ("correct_50", "Scholar", "Get 50 correct answers", "📚"),
        ("xp_100", "Century Club", "Earn 100 total XP", "⭐"),
        ("xp_500", "XP Master", "Earn 500 total XP", "🏆"),
        ("xp_1000", "XP Legend", "Earn 1000 total XP", "👑"),
        ("streak_3", "Consistent", "Answer 3 daily challenges in a row", "🔥"),
        ("level_5", "Leveling Up", "Reach level 5", "📈"),
        ("level_10", "Veteran", "Reach level 10", "🎖️"),
    ]
    async with pool.acquire() as conn:
        for key, name, desc, icon in achievements:
            await conn.execute("""
                INSERT INTO achievements (key, name, description, icon)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key) DO NOTHING;
            """, key, name, desc, icon)


# ==================================================
#  MISSIONS
# ==================================================
async def get_daily_missions(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT id, name, description, objective, progress, reward_xp, completed, claimed
            FROM missions
            WHERE user_id = $1 AND date_day = CURRENT_DATE
            ORDER BY id
        """, user_id)


async def update_mission_progress(user_id, mission_name, increment=1):
    """Increment mission progress. Returns list of newly completed missions."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            UPDATE missions
            SET progress = LEAST(objective, progress + $3),
                completed = CASE WHEN LEAST(objective, progress + $3) >= objective THEN TRUE ELSE FALSE END
            WHERE user_id = $1 AND date_day = CURRENT_DATE AND name = $2 AND completed = FALSE
            RETURNING id, name, reward_xp, completed
        """, user_id, mission_name, increment)
        return [dict(r) for r in rows]


async def generate_daily_missions(user_id):
    """Generate daily missions for a user if not already created today."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval("""
            SELECT COUNT(*) FROM missions WHERE user_id = $1 AND date_day = CURRENT_DATE
        """, user_id)
        if existing > 0:
            return

        mission_templates = [
            ("Answer 5 Questions", "Answer 5 questions in any mode", 5, 25),
            ("Get 3 Correct", "Get 3 correct answers", 3, 30),
            ("Complete Daily", "Complete the daily challenge (10 questions)", 10, 50),
            ("Earn 50 XP Today", "Earn 50 XP in a single day", 50, 40),
            ("Study Session", "Start a quiz session with !quiz", 1, 10),
        ]
        for name, desc, obj, reward in mission_templates:
            await conn.execute("""
                INSERT INTO missions (user_id, date_day, name, description, objective, reward_xp)
                VALUES ($1, CURRENT_DATE, $2, $3, $4, $5)
                ON CONFLICT (user_id, date_day, name) DO NOTHING;
            """, user_id, name, desc, obj, reward)


async def add_xp_to_missions(user_id, xp_amount):
    """Update missions that track XP earned."""
    return await update_mission_progress(user_id, "Earn 50 XP Today", xp_amount)
