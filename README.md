<h1 align="center">
  Bento Bot
</h1>

## Objective

The main goal of this project is a gamified chatbot for Discord designed to encourage discipline, motivation, and consistency in studying through quizzes, XP, levels, rankings, and focus tools. The bot is built with **Python** using **discord.py**, integrated with a **PostgreSQL** database to persist user data, study preferences, answer history, and daily XP control.

***

## Contents

1. [Project Overview](#project-overview)
2. [Technologies Used](#technologies-used)
3. [Installation and Execution](#installation-and-execution)
4. [Command List](#command-list)
5. [Project Structure](#project-structure)
6. [Gamification System](#gamification-system)
7. [Limitations](#limitations)
8. [Contact](#contact)

***

## Project Overview

Bento Bot transforms study routines into a light and engaging experience using game mechanics. Players set a study topic, answer AI-generated questions, earn XP for correct answers, level up, compete on global and daily rankings, unlock achievements, complete missions, and track their answer history — all inside Discord.

***

## Technologies Used

- **Python 3.10+**
- **discord.py** (prefix and slash commands)
- **PostgreSQL** with **asyncpg**
- **Google Gemini API** (question generation)
- **Git & GitHub**
- **pytest** (testing)

***

## Key Features

- Daily quizzes with AI-generated questions based on the user's chosen subject
- XP and leveling system with progressive difficulty
- Global and daily rankings
- Daily challenge: first 10 **correct** answers per day grant bonus XP
- Answer history tracking per user with pagination
- Persistent study preferences
- Achievement system (auto-unlocked)
- Daily missions with XP rewards
- Focus threads for dedicated study sessions
- Persistent data via PostgreSQL with structured DDL

***

## Installation and Execution

### 1. Clone the repository

```bash
git clone https://github.com/natashabaudelaire/bentobot
cd bentobot
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
```

### 3. Configure the bot on Discord

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**
2. Name it **BentoBot**, then go to **Bot → Add Bot** and copy the TOKEN
3. In **OAuth2 → URL Generator**, select scopes: `bot` and `applications.commands`; permissions: Send Messages, Read Messages, Embed Links, Manage Messages, Create Public Threads
4. Generate the link and add the bot to your server

> ⚠️ Never publish your TOKEN on GitHub

### 4. Create the `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```env
DISCORD_TOKEN=YOUR_TOKEN_HERE
DATABASE_URL=postgresql://bentobot_user:secure_password@localhost:5432/bentobot
GEMINI_API_KEY=YOUR_GEMINI_KEY_HERE
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
```

> ⚠️ Do not upload this file to GitHub

### 5. Configure the database

```bash
# Start PostgreSQL and create the database and user
psql -U postgres
```

```sql
CREATE DATABASE bentobot;
CREATE USER bentobot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bentobot TO bentobot_user;
```

Apply the schema:

```bash
psql -U bentobot_user -d bentobot -f database/schema.sql
```

### 6. Run the bot

```bash
python bentobot.py
```

### 7. Run the tests

```bash
pytest
```

***

## Command List

### Prefix commands

| Command | Description |
|---------|-------------|
| `!ping` | Test bot response |
| `!help` | Show command list |
| `!study <subject> <content>` | Set your current study topic (persisted) |
| `!quiz` | Start an unlimited practice session in a thread |
| `!daily` | Complete 10 correct questions for **Bonus XP** |
| `!stop` | End your current session (inside the thread) |
| `!profile` | Show full profile with level, XP, and accuracy |
| `!xp` | Show total XP |
| `!rank` | Global XP leaderboard (top 20) |
| `!rankday` | Daily performance leaderboard (top 20) |
| `!top10` | Elite leaderboard (top 10) |
| `!history <page>` | Review your past answers with pagination |

### Slash commands

| Command | Description |
|---------|-------------|
| `/study <subject> <content>` | Set your current study topic |
| `/profile` | Show your full profile |
| `/xp` | Show total XP |
| `/rank` | Global XP leaderboard |
| `/history <page>` | Review your past answers |

***

## Project Structure

```
bentobot.py              # Entry point: env validation, bot setup, cog loading
requirements.txt         # Python dependencies
.env.example             # Environment variable template (no secrets)
database/
  schema.sql             # Full PostgreSQL DDL
  database.py            # Data access layer (all queries/transactions)
  __init__.py
services/
  gemini.py              # Gemini API client + JSON normalization
  gamification.py        # Pure gamification logic (level, XP, achievements)
cogs/
  basic.py               # !ping, !help
  study.py               # !study + persisted preferences
  profile.py             # !profile, !xp
  training.py            # !quiz, !daily, !stop, sessions, achievements, missions
  ranking.py             # !rank, !rankday, !top10
  history.py             # !history
  slash.py               # Slash command wrappers
tests/
  test_*.py              # pytest suite
```

***

## Gamification System

### XP & Levels

- Quiz mode: **+5 XP** per correct answer
- Daily mode: **+20 XP** per correct answer (max 10 per day)
- Level formula: `level = floor(sqrt(total_xp / 50)) + 1`
- Early levels are fast; higher levels require progressively more XP

### Achievements

Achievements are stored in the database and unlocked automatically when criteria are met. They are sent as a Discord message the moment they are earned. Current set:

| Key | Name | Criteria |
|-----|------|----------|
| `first_quiz` | First Steps | Answer 1 question |
| `correct_10` | Sharp Mind | 10 correct answers |
| `correct_50` | Scholar | 50 correct answers |
| `xp_100` | Century Club | 100 total XP |
| `xp_500` | XP Master | 500 total XP |
| `xp_1000` | XP Legend | 1000 total XP |
| `level_5` | Leveling Up | Reach level 5 |
| `level_10` | Veteran | Reach level 10 |
| `first_daily` | Daily Warrior | Complete the daily 10 |
| `streak_3` | Consistent | 3 daily challenges in a row |

### Daily Missions

Five daily missions are generated per user per day: answer 5 questions, get 3 correct, complete the daily, earn 50 XP, and start a study session. Completing a mission grants bonus XP automatically.

### Daily XP Control

The `daily_xp` table tracks how many **correct** answers a user has given today. Only correct answers count towards the 10-question daily limit, so the daily cannot be "completed" with wrong answers.

***

## Limitations

- Threads are created as public threads with per-member permission overrides (private threads require Boost Level 2). If permission setting fails, other members may still see the thread.
- Slash commands currently cover the read-only commands (`/study`, `/profile`, `/xp`, `/rank`, `/history`). Full migration of `/quiz` and `/daily` to slash is a future step.

***

## Contact

For questions, suggestions, or feedback, please open an issue on the repository or contact directly via GitHub.