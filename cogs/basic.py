import discord
from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 **Pong!** ({latency}ms)")

    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(
            title="📘 Bento Command List",
            description="Master your subjects with AI-powered quizzes and tracking.",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="⚙️ General",
            value="`!ping` — Check bot latency\n`!help` — Show this guide",
            inline=False,
        )

        embed.add_field(
            name="📚 Configuration",
            value="`!study <subject> <content>` — Set your current topic\n"
                  "*Example: !study Biology Mitosis*",
            inline=False,
        )

        embed.add_field(
            name="🎮 Training Modes",
            value="`!quiz` — Start an infinite practice session (Private Thread)\n"
                  "`!daily` — Complete 10 questions for **Bonus XP**\n"
                  "`!stop` — End your current session",
            inline=False,
        )

        embed.add_field(
            name="👤 Personal Stats",
            value="`!profile` — View level, accuracy, and current focus\n"
                  "`!xp` — Quick check of your total XP\n"
                  "`!history` — Review your past answers",
            inline=False,
        )

        embed.add_field(
            name="🏆 Competitive",
            value="`!rank` — Global XP Leaderboard\n"
                  "`!rankday` — Top students for today\n"
                  "`!top10` — Elite Top 10",
            inline=False,
        )

        embed.add_field(
            name="🔗 Slash Commands",
            value="`/study` `/profile` `/xp` `/rank` `/history`",
            inline=False,
        )

        embed.set_footer(text="Type a command to get started!")
        await ctx.send(embed=embed)


async def setup(bot):
    bot.remove_command("help")
    await bot.add_cog(Basic(bot))