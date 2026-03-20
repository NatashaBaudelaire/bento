import discord
from discord.ext import commands
import database.database as db
import math

class History(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="history", help="Check your past answers. Usage: !history <page>")
    async def history(self, ctx, page: int = 1):
        # This command allows users to review their past quiz answers, showing the question, their answer, the correct answer, and whether they were correct or not. It supports pagination for easy navigation through the history.
        user_id = ctx.author.id
        pool = await db.get_pool()

        # Count total entries for the user to handle pagination.
        total = await pool.fetchval("""
            SELECT COUNT(*) FROM answer_history
            WHERE user_id = $1
        """, user_id)

        if total == 0:
            return await ctx.send("📄 You haven't answered any questions yet. Start with `!quiz`!")

        per_page = 5
        total_pages = math.ceil(total / per_page)

        if page < 1 or page > total_pages:
            return await ctx.send(f"⚠️ Invalid page! There are only **{total_pages}** pages available.")

        # Calculate SQL offset.
        offset = (page - 1) * per_page

        # Fetching records (Matching the column names in our database.py).
        rows = await pool.fetch("""
            SELECT question_text, user_answer, correct_answer, is_correct, answered_at
            FROM answer_history
            WHERE user_id = $1
            ORDER BY answered_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, per_page, offset)

        # Build the response string.
        header = f"📄 **Your Study History — Page {page}/{total_pages}**\n"
        header += "------------------------------------------\n\n"
        
        content = ""
        for i, row in enumerate(rows, start=offset + 1):
            status = "✅" if row["is_correct"] else "❌"
            
            # Formatting the date for a cleaner look.
            date_str = row["answered_at"].strftime("%Y-%m-%d %H:%M")
            
            content += (
                f"**{i}. {row['question_text']}**\n"
                f"   ➤ Your answer: `{row['user_answer']}` {status}\n"
                f"   ➤ Correct answer: `{row['correct_answer']}`\n"
                f"   *Answered on: {date_str}*\n\n"
            )

        # Using an embed if the text isn't too long, otherwise send as plain text.
        if len(header + content) < 4000:
            embed = discord.Embed(
                title=f"Study History for {ctx.author.display_name}",
                description=content,
                color=discord.Color.dark_grey()
            )
            embed.set_footer(text=f"Page {page} of {total_pages} • Use !history <page> to navigate")
            await ctx.send(embed=embed)
        else:
            await ctx.send(header + content)

async def setup(bot):
    await bot.add_cog(History(bot))