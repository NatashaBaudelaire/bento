import discord
from discord.ext import commands
import database.database as db

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="profile", help="View your study stats and progress.")
    async def profile(self, ctx, member: discord.Member = None):
        # This command allows users to view their study profile, including their current level, XP, accuracy, and study focus. It also supports viewing other users' profiles by mentioning them.
        user = member or ctx.author
        user_id = user.id

        # Ensure user is in the database.
        await db.register_user(user_id)

        # Fetch profile data from database.
        data = await db.get_profile_data(user_id)

        if not data:
            return await ctx.send("⚠️ Could not load profile data. Try answering a question first!")

        xp = data["xp"]
        correct = data["correct"]
        wrong = data["wrong"]
        total = data["total_answers"]
        daily = data["answers_today"]

        # Fetch current study preferences from Study Cog.
        study_cog = self.bot.get_cog("Study")
        pref = study_cog.get_preference(user_id) if study_cog else None

        if pref:
            study_text = f"**{pref['subject']}** — *{pref['content']}*"
        else:
            study_text = "No topic selected. Use `!study`!"

       # Calculate level and progress to next level.
        level = (xp // 100) + 1
        xp_in_level = xp % 100
        xp_needed = 100

        # Create a visual progress bar (20 blocks long).
        progress_blocks = int((xp_in_level / xp_needed) * 20)
        progress_blocks = max(0, min(20, progress_blocks))
        bar = "🟦" * progress_blocks + "⬜" * (20 - progress_blocks)

        # Calculate Accuracy Percentage.
        accuracy = (correct / total * 100) if total > 0 else 0

        # Build the profile embed.
        embed = discord.Embed(
            title=f"👤 {user.display_name}'s Student Profile",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        # Add fields for level, XP, accuracy, and study focus.
        embed.add_field(name="🏅 Level", value=f"**{level}**", inline=True)
        embed.add_field(name="⭐ Level XP", value=f"**{xp_in_level}/{xp_needed}**", inline=True)
        embed.add_field(name="🎯 Accuracy", value=f"**{accuracy:.1f}%**", inline=True)
        
        embed.add_field(name="📊 Progress to Next Level", value=f"`{bar}`", inline=False)

        embed.add_field(name="✅ Correct", value=str(correct), inline=True)
        embed.add_field(name="❌ Wrong", value=str(wrong), inline=True)
        embed.add_field(name="📝 Total Questions", value=str(total), inline=True)

        embed.add_field(
            name="📅 Daily Challenge",
            value=f"**{daily}/10** questions completed today",
            inline=False
        )

        embed.add_field(
            name="📖 Current Focus",
            value=study_text,
            inline=False
        )

        embed.set_footer(text="Keep studying to climb the leaderboard!")
        await ctx.send(embed=embed)

    @commands.command(name="xp")
    async def xp(self, ctx):
        # This command provides a quick way for users to check their total accumulated XP without needing to view the full profile.
        user_id = ctx.author.id
        await db.register_user(user_id)
        total_xp = await db.get_xp(user_id)
        await ctx.send(f"✨ {ctx.author.mention}, your total accumulated XP is **{total_xp}**!")

async def setup(bot):
    await bot.add_cog(Profile(bot))