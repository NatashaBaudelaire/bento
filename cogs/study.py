import discord
from discord.ext import commands
import database.database as db


class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="study",
        help="Set your study topic. Usage: !study <subject> <content>",
    )
    async def study(self, ctx, subject: str, *, content: str):
        user_id = ctx.author.id

        await db.register_user(user_id)
        await db.save_study_preference(user_id, subject, content)

        embed = discord.Embed(
            title="📚 Study Topic Set!",
            description=(
                f"Subject: **{subject}**\n"
                f"Content: **{content}**\n\n"
                "**Choose your training mode:**\n"
                "➡️ `!quiz` — Unlimited practice questions\n"
                "➡️ `!daily` — Complete your 10 daily questions"
            ),
            color=discord.Color.blue(),
        )

        await ctx.send(embed=embed)

    async def get_preference(self, user_id):
        return await db.get_study_preference(user_id)


async def setup(bot):
    await bot.add_cog(Study(bot))
