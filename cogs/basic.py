import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Ping command with Latency.
    @commands.command(name="ping")
    async def ping(self, ctx):
        # Calculate latency in milliseconds.
        latency = round(self.bot.latency * 1000) # Convert to milliseconds.
        await ctx.send(f"🏓 **Pong!** ({latency}ms)")

    # Enhanced Help command.
    @commands.command(name="help")
    async def help(self, ctx):
        # This command provides a comprehensive guide to all available commands and features of the bot.
        embed = discord.Embed(
            title="📘 Study Bot Command List",
            description="Master your subjects with AI-powered quizzes and tracking.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="⚙️ General",
            value="`!ping` — Check bot latency\n`!help` — Show this guide",
            inline=False
        )

        embed.add_field(
            name="📚 Configuration",
            value="`!study <subject> <content>` — Set your current topic\n"
                  "*Example: !study Biology Mitosis*",
            inline=False
        )

        embed.add_field(
            name="🎮 Training Modes",
            value="`!quiz` — Start an infinite practice session (Private Thread)\n"
                  "`!daily` — Complete 10 questions for **Bonus XP**\n"
                  "`!stop` — End your current session",
            inline=False
        )

        embed.add_field(
            name="👤 Personal Stats",
            value="`!profile` — View level, accuracy, and current focus\n"
                  "`!xp` — Quick check of your total XP\n"
                  "`!history` — Review your past answers",
            inline=False
        )

        embed.add_field(
            name="🏆 Competitive",
            value="`!rank` — Global XP Leaderboard\n"
                  "`!rankday` — Top students for today",
            inline=False
        )

        embed.set_footer(text="Type a command to get started!")
        
        await ctx.send(embed=embed)

# Setup function to add the Cog to the bot.
async def setup(bot):
    # Removing the default help command to use our custom one.
    bot.remove_command("help")
    await bot.add_cog(Basic(bot))