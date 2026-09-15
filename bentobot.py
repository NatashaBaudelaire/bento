import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import database.database as db

load_dotenv()

REQUIRED_ENV = {
    "DISCORD_TOKEN": "Token of the Discord bot",
    "DATABASE_URL": "PostgreSQL connection URL",
    "GEMINI_API_KEY": "Google Gemini API key",
}

missing = [var for var, desc in REQUIRED_ENV.items() if not os.getenv(var)]
if missing:
    print("❌ Missing required environment variables:")
    for var in missing:
        print(f"   - {var}: {REQUIRED_ENV[var]}")
    sys.exit(1)

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot connected as {bot.user}")

    try:
        await db.get_pool()
        await db.seed_achievements()
        print("🌐 Database connected successfully!")
    except Exception as e:
        print(f"❌ ERROR connecting to database: {e}")

EXTENSIONS = [
    "cogs.basic",
    "cogs.study",
    "cogs.profile",
    "cogs.training",
    "cogs.ranking",
    "cogs.history",
]

async def load_extensions():
    for extension in EXTENSIONS:
        try:
            await bot.load_extension(extension)
            print(f"  [OK] Loaded extension: {extension}")
        except Exception as e:
            print(f"  [ERROR] Failed to load {extension}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")
