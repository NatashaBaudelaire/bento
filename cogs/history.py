import math
import discord
from discord.ext import commands
import database.database as db


class History(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="history", help="Check your past answers. Usage: !history <page>")
    async def history(self, ctx, page: int = 1):
        user_id = ctx.author.id

        total = await db.get_history_count(user_id)

        if total == 0:
            return await ctx.send("📄 You haven't answered any questions yet. Start with `!quiz`!")

        per_page = 5
        total_pages = math.ceil(total / per_page)

        if page < 1 or page > total_pages:
            return await ctx.send(f"⚠️ Invalid page! There are only **{total_pages}** pages available.")

        offset = (page - 1) * per_page
        rows = await db.get_history(user_id, limit=per_page, offset=offset)

        content = ""
        for i, row in enumerate(rows, start=offset + 1):
            status = "✅" if row["is_correct"] else "❌"
            date_str = row["answered_at"].strftime("%Y-%m-%d %H:%M")
            content += (
                f"**{i}. {row['question_text'][:100]}**\n"
                f"   ➤ Your answer: `{row['user_answer']}` {status}\n"
                f"   ➤ Correct answer: `{row['correct_answer']}`\n"
                f"   *Answered on: {date_str}*\n\n"
            )

        if len(content) < 4000:
            embed = discord.Embed(
                title=f"Study History for {ctx.author.display_name}",
                description=content,
                color=discord.Color.dark_grey(),
            )
            embed.set_footer(text=f"Page {page} of {total_pages} • Use !history <page> to navigate")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"📄 **Your Study History — Page {page}/{total_pages}**\n\n{content}")


async def setup(bot):
    await bot.add_cog(History(bot))
