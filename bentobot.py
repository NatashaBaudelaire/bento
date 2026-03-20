import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import database.database as db # Ensure your database module uses English internally too!.

# Load environment variables.
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure intents.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

# Create bot instance.
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: when the bot starts.
@bot.event
async def on_ready():
    print(f"✅ Bot connected as {bot.user}")

    try:
        # Initializing the database pool.
        await db.get_pool()
        print("🌐 Database connected successfully!")
    except Exception as e:
        print(f"❌ ERROR connecting to database: {e}")

# Load Cog modules
async def load_extensions():
    extensions = [
        "cogs.basic",
        "cogs.study",
        "cogs.profile",
        "cogs.progress",
        "cogs.ranking",
        "cogs.history"
    ]

    for extension in extensions:
        # We use the full path to check if it's loaded to avoid conflicts.
        try:
            await bot.load_extension(extension)
            print(f" [OK] Loaded extension: {extension}")
        except Exception as e:
            print(f" [ERROR] Failed to load {extension}: {e}")

# Start the bot.
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")