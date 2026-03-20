import discord
from discord.ext import commands

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This dictionary stores temporary session settings.
        # format: {user_id: {"subject": str, "content": str}}.
        self.preferences = {}  

    @commands.command(
        name="study", 
        help="Set your study topic. Usage: !study <subject> <content>"
    )
    async def study(self, ctx, subject: str, *, content: str):
        # This command allows users to set their current study topic and content. The bot will save these preferences in memory, which can then be accessed by the Training Cog when generating questions. It also provides user feedback with an embedded message confirming the settings and guiding them to the next steps.
        user_id = ctx.author.id

        # Saving the user's study preferences in memory.
        self.preferences[user_id] = {
            "subject": subject,
            "content": content
        }

        # User-facing feedback.
        embed = discord.Embed(
            title="📚 Study Topic Set!",
            description=(
                f"Subject: **{subject}**\n"
                f"Content: **{content}**\n\n"
                "**Choose your training mode:**\n"
                "➡️ `!quiz` — Unlimited practice questions\n"
                "➡️ `!daily` — Complete your 10 daily questions"
            ),
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

        # Developer Debugging.
        print(f"[DEBUG] Study preferences saved for {ctx.author} ({user_id})")
        print(f"Topic: {subject} | Details: {content}")

    # Public method for other Cogs (like Training) to access these settings.
    def get_preference(self, user_id):
        return self.preferences.get(user_id)


async def setup(bot):
    await bot.add_cog(Study(bot))