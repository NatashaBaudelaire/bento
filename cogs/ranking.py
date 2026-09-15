import discord
from discord.ext import commands
import database.database as db


class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _resolve_name(self, user_id):
        user = self.bot.get_user(user_id)
        if user:
            return user.name
        try:
            user = await self.bot.fetch_user(user_id)
            return user.name
        except discord.NotFound:
            return f"User {user_id}"

    @commands.command(name="rank")
    async def rank(self, ctx):
        rows = await db.get_global_ranking(limit=20)

        if not rows:
            return await ctx.send("📄 No one has earned any XP yet.")

        embed = discord.Embed(
            title="🏆 GLOBAL RANKING (TOP 20)",
            color=discord.Color.gold(),
        )

        medals = ["🥇", "🥈", "🥉"]
        description = ""
        for pos, row in enumerate(rows, 1):
            name = await self._resolve_name(row["user_id"])
            prefix = medals[pos - 1] if pos <= 3 else f"**#{pos}**"
            description += f"{prefix} {name} — `{row['total_xp']} XP`\n"

        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="rankday")
    async def rankday(self, ctx):
        rows = await db.get_daily_ranking(limit=20)

        if not rows:
            return await ctx.send("📅 No one has answered daily questions today.")

        embed = discord.Embed(
            title="📅 DAILY RANKING — Top Performers Today",
            color=discord.Color.blue(),
        )

        medals = ["🥇", "🥈", "🥉"]
        description = ""
        for pos, row in enumerate(rows, 1):
            name = await self._resolve_name(row["user_id"])
            prefix = medals[pos - 1] if pos <= 3 else f"**#{pos}**"
            description += (
                f"{prefix} {name} — `{row['daily_xp']} XP` "
                f"({row['answers_today']} correct)\n"
            )

        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="top10")
    async def top10(self, ctx):
        rows = await db.get_global_ranking(limit=10)

        if not rows:
            return await ctx.send("🏅 There are no top players yet.")

        embed = discord.Embed(title="🥇 ELITE TOP 10", color=discord.Color.gold())

        medals = ["🥇", "🥈", "🥉"]
        description = ""
        for pos, row in enumerate(rows, 1):
            name = await self._resolve_name(row["user_id"])
            prefix = medals[pos - 1] if pos <= 3 else f"✨ **#{pos}**"
            description += f"{prefix} {name} — `{row['total_xp']} XP`\n"

        embed.description = description
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ranking(bot))
