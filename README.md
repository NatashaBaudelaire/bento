# Bento Bot: Gamified Chatbot for Discord

Bento Bot is a gamified chatbot developed for Discord, designed to encourage discipline, motivation, and consistency in studying through quizzes, XP, levels, rankings, and focus tools.

---

# About the Project

Bento Bot transforms study routines into a light and engaging experience using game mechanics.

Features include:

* Daily quizzes
* XP and leveling system
* Global ranking
* Answer history tracking
* Daily XP limit (first 10 correct answers)
* Category-based questions
* Focus Rooms

---

# Technologies Used

* Node.js or Python
* Discord.js or discord.py
* PostgreSQL
* Docker & Docker Compose (optional, recommended)
* Git & GitHub
* VS Code

---

# Prerequisites

Before starting, install:

* Node.js 16+
* (Optional) Python 3.10+
* PostgreSQL
* Git
* VS Code
* A Discord account
* A bot created in the Discord Developer Portal

---

# Project Structure

* /db/init.sql → DDL do banco
* /db/seed.sql → perguntas iniciais
* bot.js / bot.py → aplicação principal
* docker-compose.yml (opcional, recomendado)
* .env → variáveis sensíveis

---

# Clone the Repository

```bash
git clone https://github.com/nerysecurity/botdiscord
cd botdiscord
```

---

# Create and Configure the Bot on Discord

1. Go to: [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click on New Application
3. Name it: BentoBot
4. Go to Bot → Add Bot
5. Copy the TOKEN
6. In OAuth2 → URL Generator, select:
   * Scopes: bot
   * Permissions: Send Messages, Read Messages, Embed Links, Manage Messages
7. Generate the link and add the bot to your server

⚠️ **Never publish your TOKEN on GitHub**

---

# Configure PostgreSQL Database

## Local Installation

Access psql:

```sql
CREATE DATABASE bentobot;
CREATE USER bentobot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bentobot TO bentobot_user;
```

---

# Create Tables (DDL)

Create the file db/init.sql:
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  discord_id VARCHAR(50) NOT NULL UNIQUE,
  username VARCHAR(100),
  xp INTEGER DEFAULT 0,
  level INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questions (
  id SERIAL PRIMARY KEY,
  category VARCHAR(100),
  question TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT,
  option_d TEXT,
  correct_answer CHAR(1) NOT NULL
);

CREATE TABLE answer_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  question_id INTEGER REFERENCES questions(id),
  is_correct BOOLEAN,
  chosen_answer CHAR(1),
  answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_questions (
  id SERIAL PRIMARY KEY,
  question_id INTEGER REFERENCES questions(id),
  date DATE NOT NULL
);

CREATE TABLE daily_counters (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  date DATE NOT NULL,
  answers_with_xp INTEGER DEFAULT 0,
  UNIQUE (user_id, date)
);
```

Run:

```bash
psql -U postgres -d bentobot -f db/init.sql
```

---

# 🔑 Create the `.env` file

In the root folder:

```
DISCORD_TOKEN=YOUR_TOKEN_HERE

DB_HOST=localhost
DB_PORT=5432
DB_USER=bentobot_user
DB_PASSWORD=secure_password
DB_NAME=bentobot
```

⚠️ **Do not upload this file to GitHub**

---

# Install Dependencies and Run

## Node.js

```bash
npm install
npm start
```

## Python

```bash
pip install -r requirements.txt
python bot.py
```

---

# Run the Bot

## Node.js

```bash
npm start
```

## Python

```bash
python bot.py
```

---

# Docker Compose (Recommended)

Create docker-compose.yml:

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    container_name: bentobot_db
    environment:
      POSTGRES_DB: bentobot
      POSTGRES_USER: bentobot_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"

  bot:
    build: .
    container_name: bentobot_app
    depends_on:
      - db
    env_file:
      - .env
    volumes:
      - .:/app
    command: npm start
    restart: unless-stopped

volumes:
  db_data:
```

Run:

```bash
docker compose up --build -d
docker compose logs -f bot
```

---

# Insert Initial Questions (Seed)

File db/seed.sql:

```sql
INSERT INTO answers (category,question,option_a,option_b,option_c,option_d,correct_answer)
VALUES
('Math','What is 2+2?','3','4','5','6','B'),
('Portuguese','Which is correct?','a','b','c','d','A');
```

Run:

```bash
psql -U bentobot_user -d bentobot -f db/seed.sql
```

---

# Command List

### General

* !ping: Test bot response
* !help: Show command list

### Study

* !study `<subject` `<content>`: Register what the user wants to study

### Quiz & Training

* !quiz: Start infinite quiz in private thread
* !diary: Answer daily 10 questions (high XP)
* !stop: End quiz session

### Profile & XP

* !profile: Show full profile
* !xp: Show total XP

### Ranking

* !ranking: Show global ranking

### History

* !history: Show recent answers

---

# XP Rules (MVP)

* Only the first 10 correct answers per day grant XP
* Additional answers are recorded but do not grant XP
* Controlled via daily_counters table

---

# Bot Commands

| Comando      | Função                    |
| ------------ | --------------------------|
| `!quiz`      | Start a quiz              |
| `!perfil`    | Show XP, level, progress  |
| `!rank`      | Global ranking            |
| `!historico` | User history              |
| `!help`      | Command list              |

---

# Quick Tests After Setup

* Bot appears online on Discord
* `!help` works
* `!perfil` creates user in users table
* `!quiz` records answers
* XP increases only for first 10 correct answers per day
* Useful queries:

```bash
psql -U bentobot_user -d bentobot -c "SELECT * FROM usuarios LIMIT 10;"
psql -U bentobot_user -d bentobot -c "SELECT * FROM historico_respostas LIMIT 10;""
```

---

# MVP Features

* Daily quizzes
* Daily XP limit
* Levels
* Ranking
* Answer history
* Focus Rooms
* Multiple categories

---

# Future Improvements

* Global ranking
* Weekly leagues & seasons
* Rare collectible achievements
* Mobile app integration

---

# Troubleshooting

| Problema              | Solução                           |
| ----------------------| -------------------------------   |
| Bot not connecting    | Check `DISCORD_TOKEN`             |
| DB connection error   | Verify user/password/port         |
| Missing permissions   | Regenerate OAuth2 URL             |
| Port 5432 in use      | Change port in docker-compose     |

---

# Evaluation Checklist

* Bot runs with `npm start` / `python bot.py`
* PostgreSQL is working
* Tables created correctly
* Seed executed
* Daily XP working
* Docker Compose working
* Clear documentation

---

Made with 💙 to help students improve every day.

---

# Contact
For questions, suggestions, or feedback, please open an issue on the repository or contact directly via GitHub.