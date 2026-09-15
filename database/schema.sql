-- Bento Database Schema
-- PostgreSQL

-- ==================================================
--  USERS
-- ==================================================
CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    total_xp    INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==================================================
--  STUDY PREFERENCES
-- ==================================================
CREATE TABLE IF NOT EXISTS study_preferences (
    user_id     BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    subject     TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL DEFAULT '',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==================================================
--  DAILY XP TRACKING
-- ==================================================
CREATE TABLE IF NOT EXISTS daily_xp (
    user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date_day       DATE NOT NULL DEFAULT CURRENT_DATE,
    answers_today  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, date_day)
);

-- ==================================================
--  ANSWER HISTORY
-- ==================================================
CREATE TABLE IF NOT EXISTS answer_history (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_text   TEXT NOT NULL,
    type            TEXT NOT NULL,
    alternatives    JSONB,
    user_answer     TEXT NOT NULL,
    correct_answer  TEXT NOT NULL,
    is_correct      BOOLEAN NOT NULL DEFAULT FALSE,
    xp_gained       INTEGER NOT NULL DEFAULT 0,
    is_daily_10     BOOLEAN NOT NULL DEFAULT FALSE,
    answered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==================================================
--  ACHIEVEMENTS DEFINITIONS
-- ==================================================
CREATE TABLE IF NOT EXISTS achievements (
    id          SERIAL PRIMARY KEY,
    key         TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    icon        TEXT NOT NULL DEFAULT '🏅'
);

-- ==================================================
--  USER ACHIEVEMENTS
-- ==================================================
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id        BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id)
);

-- ==================================================
--  DAILY MISSIONS
-- ==================================================
CREATE TABLE IF NOT EXISTS missions (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date_day    DATE NOT NULL DEFAULT CURRENT_DATE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    objective   INTEGER NOT NULL,
    progress    INTEGER NOT NULL DEFAULT 0,
    reward_xp   INTEGER NOT NULL DEFAULT 0,
    completed   BOOLEAN NOT NULL DEFAULT FALSE,
    claimed     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, date_day, name)
);

-- ==================================================
--  INDEXES
-- ==================================================
CREATE INDEX IF NOT EXISTS idx_answer_history_answered_at ON answer_history(answered_at DESC);
CREATE INDEX IF NOT EXISTS idx_answer_history_user_date ON answer_history(user_id, answered_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_xp_date ON daily_xp(date_day);
CREATE INDEX IF NOT EXISTS idx_users_total_xp ON users(total_xp DESC);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_missions_user_date ON missions(user_id, date_day);
