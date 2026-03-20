import discord
from discord.ext import commands
import database.database as db

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Global Ranking Command.
    @commands.command(name="rank")
    async def rank(self, ctx):
        # Displays the Top 20 users with the highest total XP across all time.
        pool = await db.get_pool()

        query = """
            SELECT user_id, total_xp
            FROM users
            ORDER BY total_xp DESC
            LIMIT 20
        """

        rows = await pool.fetch(query)

        if not rows:
            return await ctx.send("📄 No one has earned any XP yet.")

        text = "🏆 **GLOBAL RANKING (TOP 20)**\n"
        text += "------------------------------\n"

        for pos, row in enumerate(rows, 1):
            user_id = row["user_id"]
            user = self.bot.get_user(user_id)
            
            # Fallback if user is not in cache.
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except:
                    name = f"User {user_id}"
            else:
                name = user.name

            text += f"**#{pos}** — {name}: **{row['total_xp']} XP**\n"

        await ctx.send(text)

    # Daily Ranking Command.
    @commands.command(name="rankday")
    async def rankday(self, ctx):
        # Displays the Top 20 users who answered questions today.
        pool = await db.get_pool()

        query = """
            SELECT user_id, answers_today
            FROM daily_xp
            WHERE date_day = CURRENT_DATE
            ORDER BY answers_today DESC
            LIMIT 20
        """

        rows = await pool.fetch(query)

        if not rows:
            return await ctx.send("📅 No one has answered daily questions today.")

        text = "📅 **DAILY RANKING — Most Active Today**\n"
        text += "--------------------------------------\n"

        for pos, row in enumerate(rows, 1):
            user_id = row["user_id"]
            user = self.bot.get_user(user_id)
            
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except:
                    name = f"User {user_id}"
            else:
                name = user.name

            text += f"**#{pos}** — {name}: **{row['answers_today']} answered**\n"

        await ctx.send(text)

    # Top 10 XP Command.
    @commands.command(name="top10")
    async def top10(self, ctx):
        # Displays the Top 10 users with the highest total XP in a more visually appealing format, using an Embed to highlight the elite status of these top performers.
        pool = await db.get_pool()

        query = """
            SELECT user_id, total_xp
            FROM users
            ORDER BY total_xp DESC
            LIMIT 10
        """

        rows = await pool.fetch(query)

        if not rows:
            return await ctx.send("🏅 There are no top players yet.")

        # Using an Embed for the Top 10 for a more "Elite" feel.
        embed = discord.Embed(
            title="🥇 ELITE TOP 10",
            color=discord.Color.gold()
        )

        description = ""
        for pos, row in enumerate(rows, 1):
            user_id = row["user_id"]
            user = self.bot.get_user(user_id)
            name = user.name if user else f"User {user_id}"
            
            medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else "✨"
            description += f"{medal} **#{pos}** {name} — `{row['total_xp']} XP`\n"

        embed.description = description
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ranking(bot))