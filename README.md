<h1 align="center">
  Bento Bot
</h1>

## Objective

The main goal of this project was to develop a gamified chatbot for Discord, designed to encourage discipline, motivation, and consistency in studying through **quizzes, XP, levels, rankings, and focus tools**. The bot was built using **Node.js** with **Discord.js** (or Python with discord.py), integrated with a **PostgreSQL** database to persist user data, answer history, and daily XP control — with optional deployment via **Docker Compose**.

***

## Contents

1. [Project Overview](#project-overview)
2. [Objective](#objective)
3. [Technologies Used](#technologies-used)
4. [Installation and Execution](#installation-and-execution)
5. [Command List](#command-list)
6. [Key Concepts Applied](#key-concepts-applied)
7. [Improvements to Implement](#improvements-to-implement)
8. [Contact](#contact)

***

## Project Overview

Bento Bot transforms study routines into a light and engaging experience using game mechanics. Players answer daily quizzes, earn XP for correct answers, level up, compete on a global ranking, and track their answer history — all inside Discord, with a daily XP cap to encourage consistency over grinding.

***

## Technologies Used

- **Node.js** or **Python**
- **Discord.js** or **discord.py**
- **PostgreSQL**
- **Docker & Docker Compose** (optional, recommended)
- **Git & GitHub**
- **VS Code**

***

## Key Features

- Daily quizzes with category-based questions
- XP and leveling system with global ranking
- Daily XP limit: only the first 10 correct answers per day grant XP
- Answer history tracking per user
- Focus Rooms for dedicated study sessions
- Full user profile with XP, level, and progress display
- Persistent data via PostgreSQL with structured DDL and seed files
- Containerised deployment with Docker Compose

***

## Improvements to Implement

- Global ranking with weekly leagues and seasons
- Rare collectible achievements
- Mobile app integration
- Expanded question bank with more categories

***

## Installation and Execution

### 1. Clone the repository

```bash
git clone https://github.com/natashabaudelaire/bentobot
cd bentobot
```

### 2. Requirements

- Node.js 16+ (or Python 3.10+)
- PostgreSQL
- Git
- VS Code
- A Discord account and a bot created in the [Discord Developer Portal](https://discord.com/developers/applications)

### 3. Configure the bot on Discord

1. Go to the Discord Developer Portal and click **New Application**
2. Name it **BentoBot**, then go to **Bot → Add Bot** and copy the TOKEN
3. In **OAuth2 → URL Generator**, select scopes: `bot` and permissions: Send Messages, Read Messages, Embed Links, Manage Messages
4. Generate the link and add the bot to your server

> ⚠️ Never publish your TOKEN on GitHub

### 4. Create the `.env` file

```env
DISCORD_TOKEN=YOUR_TOKEN_HERE

DB_HOST=localhost
DB_PORT=5432
DB_USER=bentobot_user
DB_PASSWORD=secure_password
DB_NAME=bentobot
```

> ⚠️ Do not upload this file to GitHub

### 5. Configure the database

```sql
CREATE DATABASE bentobot;
CREATE USER bentobot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bentobot TO bentobot_user;
```

```bash
psql -U postgres -d bentobot -f db/init.sql
psql -U bentobot_user -d bentobot -f db/seed.sql
```

### 6. Install dependencies and run

**Node.js**
```bash
npm install
npm start
```

**Python**
```bash
pip install -r requirements.txt
python bot.py
```

### 7. Docker Compose (Recommended)

```bash
docker compose up --build -d
docker compose logs -f bot
```

***

## Command List

| Command | Description |
|---------|-------------|
| `!ping` | Test bot response |
| `!help` | Show command list |
| `!study <subject> <content>` | Register what you want to study |
| `!quiz` | Start an infinite quiz in a private thread |
| `!diary` | Answer the daily 10 questions (high XP) |
| `!stop` | End the current quiz session |
| `!profile` | Show full profile with XP and level |
| `!xp` | Show total XP |
| `!ranking` | Show global ranking |
| `!history` | Show recent answer history |

***

## Key Concepts Applied

- Gamification applied to study habits
- RESTful bot architecture with command handlers
- PostgreSQL relational schema with foreign keys and constraints
- Daily XP cap controlled via `daily_counters` table
- Environment variable management with `.env`
- Containerised infrastructure with Docker Compose
- Persistent answer history and user progression

***

## Contact

For questions, suggestions, or feedback, please open an issue on the repository or contact directly via GitHub.
