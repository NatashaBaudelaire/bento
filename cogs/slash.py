import discord
from discord.ext import commands
import database.database as db


class SlashCommands(commands.Cog):
    """Slash-command wrappers for the main bot features."""

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="study", description="Set your study topic")
    @discord.app_commands.describe(subject="Subject to study", content="What content to focus on")
    async def slash_study(self, interaction: discord.Interaction, subject: str, content: str):
        user_id = interaction.user.id
        await db.register_user(user_id)
        await db.save_study_preference(user_id, subject, content)

        embed = discord.Embed(
            title="📚 Study Topic Set!",
            description=f"Subject: **{subject}**\nContent: **{content}**\n\n"
                        "➡️ Use `!quiz` for practice or `!daily` for the daily challenge.",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="profile", description="View your study stats and progress")
    async def slash_profile(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        await db.register_user(user_id)
        data = await db.get_profile_data(user_id)

        if not data:
            await interaction.response.send_message("⚠️ Could not load profile data.")
            return

        level, xp_in_level, xp_needed = db.get_level_progress(data["xp"])
        accuracy = (data["correct"] / data["total_answers"] * 100) if data["total_answers"] > 0 else 0

        embed = discord.Embed(
            title=f"👤 {interaction.user.display_name}'s Student Profile",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🏅 Level", value=f"**{level}**", inline=True)
        embed.add_field(name="⭐ Level XP", value=f"**{xp_in_level}/{xp_needed}**", inline=True)
        embed.add_field(name="🎯 Accuracy", value=f"**{accuracy:.1f}%**", inline=True)
        embed.add_field(name="✨ Total XP", value=f"**{data['xp']}**", inline=True)
        embed.add_field(name="✅ Correct", value=str(data["correct"]), inline=True)
        embed.add_field(name="❌ Wrong", value=str(data["wrong"]), inline=True)
        embed.add_field(name="📅 Daily", value=f"**{data['answers_today']}/10**", inline=True)

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="xp", description="Check your total XP")
    async def slash_xp(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        await db.register_user(user_id)
        total_xp = await db.get_xp(user_id)
        await interaction.response.send_message(
            f"✨ {interaction.user.mention}, your total accumulated XP is **{total_xp}**!"
        )

    @discord.app_commands.command(name="rank", description="Global XP leaderboard (top 20)")
    async def slash_rank(self, interaction: discord.Interaction):
        rows = await db.get_global_ranking(limit=20)
        embed = discord.Embed(title="🏆 GLOBAL RANKING (TOP 20)", color=discord.Color.gold())
        if not rows:
            embed.description = "No one has earned any XP yet."
        else:
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for pos, row in enumerate(rows, 1):
                name = self.bot.get_user(row["user_id"])
                label = name.name if name else f"User {row['user_id']}"
                prefix = medals[pos - 1] if pos <= 3 else f"**#{pos}**"
                lines.append(f"{prefix} {label} — `{row['total_xp']} XP`")
            embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="history", description="Review your past answers")
    @discord.app_commands.describe(page="Page number")
    async def slash_history(self, interaction: discord.Interaction, page: int = 1):
        user_id = interaction.user.id
        total = await db.get_history_count(user_id)

        if total == 0:
            await interaction.response.send_message(
                "📄 You haven't answered any questions yet. Use `/study` first!"
            )
            return

        import math
        per_page = 5
        total_pages = math.ceil(total / per_page)
        if page < 1 or page > total_pages:
            await interaction.response.send_message(
                f"⚠️ Invalid page! There are only **{total_pages}** pages available."
            )
            return

        rows = await db.get_history(user_id, limit=per_page, offset=(page - 1) * per_page)
        content = ""
        for i, row in enumerate(rows, start=(page - 1) * per_page + 1):
            status = "✅" if row["is_correct"] else "❌"
            date_str = row["answered_at"].strftime("%Y-%m-%d %H:%M")
            content += (
                f"**{i}. {row['question_text'][:100]}**\n"
                f"   ➤ Your answer: `{row['user_answer']}` {status}\n"
                f"   ➤ Correct: `{row['correct_answer']}`\n"
                f"   *{date_str}*\n\n"
            )

        embed = discord.Embed(
            title=f"Study History for {interaction.user.display_name}",
            description=content[:4000],
            color=discord.Color.dark_grey(),
        )
        embed.set_footer(text=f"Page {page} of {total_pages}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    cog = SlashCommands(bot)
    await bot.add_cog(cog)