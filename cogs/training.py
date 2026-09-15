import asyncio
import discord
from discord.ext import commands
from services.gemini import generate_gemini_question
import database.database as db


class Training(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}
        self._locks = {}

    # ==================================================
    #  HELPERS
    # ==================================================
    async def get_pref(self, user_id):
        return await db.get_study_preference(user_id)

    async def create_private_thread(self, ctx, name, user):
        try:
            thread = await ctx.channel.create_thread(
                name=name,
                type=discord.ChannelType.public_thread,
                auto_archive_duration=60,
            )
        except discord.Forbidden:
            await ctx.send("⚠️ I don't have permission to create threads here.")
            return None
        except Exception:
            await ctx.send("⚠️ Could not create the study thread.")
            return None

        overwrite = discord.PermissionOverwrite(send_messages=False)

        for member in ctx.channel.members:
            if member.id not in (user.id, ctx.guild.me.id):
                try:
                    await thread.set_permissions(member, overwrite=overwrite)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

        return thread

    async def send_question(self, user_id):
        session = self.sessions.get(user_id)
        if not session:
            return

        channel = session["channel"]

        try:
            await channel.send("⌛ Generating question...")
            question = await asyncio.wait_for(
                generate_gemini_question(session["subject"], session["content"]),
                timeout=25,
            )
        except Exception as e:
            print(f"[GEMINI ERROR]: {e}")
            try:
                await channel.send("❌ Error generating question. Session ended.")
            except discord.HTTPException:
                pass
            await self.end_session(user_id)
            return

        if not question or "question" not in question:
            try:
                await channel.send("❌ AI returned an invalid question. Session ended.")
            except discord.HTTPException:
                pass
            await self.end_session(user_id)
            return

        session["last"] = question
        try:
            await channel.send(f"🧠 **{question['question']}**")

            if question.get("type") == "multiple":
                alt = question.get("alternatives") or {}
                options = "\n".join(f"**{letter})** {alt[letter]}" for letter in sorted(alt))
                await channel.send(options)
        except discord.HTTPException as e:
            print(f"[TRAINING ERROR] Failed to send question: {e}")
            await self.end_session(user_id)

    async def end_session(self, user_id):
        session = self.sessions.pop(user_id, None)
        self._locks.pop(user_id, None)
        if not session:
            return

        channel = session["channel"]
        try:
            await channel.send("🛑 Session ended.")
            await channel.edit(archived=True)
        except discord.HTTPException:
            pass

    # ==================================================
    #  ACHIEVEMENTS
    # ==================================================
    @staticmethod
    def _consecutive_days(dates):
        from datetime import timedelta

        if not dates:
            return 0

        count = 1
        for i in range(1, len(dates)):
            if dates[i - 1] - dates[i] == timedelta(days=1):
                count += 1
            else:
                break
        return count

    async def check_achievements(self, user_id):
        data = await db.get_profile_data(user_id)
        if not data:
            return

        xp = data["xp"]
        correct = data["correct"]
        total = data["total_answers"]
        level, _, _ = db.get_level_progress(xp)

        daily_dates = await db.get_daily_completion_dates(user_id, daily_goal=10)
        streak = self._consecutive_days(daily_dates)

        criteria = {
            "first_quiz": total >= 1,
            "correct_10": correct >= 10,
            "correct_50": correct >= 50,
            "xp_100": xp >= 100,
            "xp_500": xp >= 500,
            "xp_1000": xp >= 1000,
            "level_5": level >= 5,
            "level_10": level >= 10,
            "streak_3": streak >= 3,
        }

        for key, met in criteria.items():
            if met and await db.unlock_achievement(user_id, key):
                achievement = await db.get_achievement_by_key(key)
                if achievement:
                    try:
                        await self.bot.get_cog("Training").send_achievement_feedback(
                            user_id, achievement
                        )
                    except Exception:
                        pass

    async def send_achievement_feedback(self, user_id, achievement):
        session = self.sessions.get(user_id)
        if not session:
            return
        try:
            await session["channel"].send(
                f"🏅 **Achievement unlocked: {achievement['name']}**\n"
                f"{achievement['icon']} {achievement['description']}"
            )
        except discord.HTTPException:
            pass

    # ==================================================
    #  MISSIONS
    # ==================================================
    async def handle_mission_hooks(self, user_id, correct, xp, mode, missions_extra=None):
        completed_gained = []

        if missions_extra:
            for name in missions_extra:
                completed_gained.extend(await db.update_mission_progress(user_id, name, 1))

        completed_gained.extend(await db.update_mission_progress(user_id, "Answer 5 Questions", 1))

        if correct:
            completed_gained.extend(await db.update_mission_progress(user_id, "Get 3 Correct", 1))

        if xp > 0:
            completed_gained.extend(await db.add_xp_to_missions(user_id, xp))

        if correct and mode == "daily" and xp > 0:
            completed_gained.extend(await db.update_mission_progress(user_id, "Complete Daily", 1))

        seen = {}
        for m in completed_gained:
            seen[m["id"]] = m

        session = self.sessions.get(user_id)
        for mission in seen.values():
            if mission["completed"] and mission["reward_xp"] > 0:
                await db.add_xp(user_id, mission["reward_xp"])
                if session:
                    try:
                        await session["channel"].send(
                            f"🎯 **Mission complete: {mission['name']}** (+{mission['reward_xp']} XP bonus!)"
                        )
                    except discord.HTTPException:
                        pass

    # ==================================================
    #  COMMANDS
    # ==================================================
    @commands.command(name="quiz")
    async def quiz(self, ctx):
        user = ctx.author
        user_id = user.id

        pref = await self.get_pref(user_id)
        if not pref or not pref.get("subject"):
            return await ctx.send("⚠️ Use `!study <subject> <content>` first to set your topic.")

        if user_id in self.sessions:
            return await ctx.send("⚠️ You already have an active session. Use `!stop` inside your thread.")

        thread = await self.create_private_thread(ctx, f"quiz-{user.name}", user)
        if not thread:
            return

        await db.register_user(user_id)
        await db.generate_daily_missions(user_id)

        try:
            await thread.send(
                f"🎮 {user.mention}, your quiz has started!\nUse **!stop** to end the session."
            )
        except discord.HTTPException:
            return

        self.sessions[user_id] = {
            "mode": "study",
            "channel": thread,
            "answered": 0,
            "correct": 0,
            "last": None,
            "subject": pref["subject"],
            "content": pref["content"],
        }

        await self.handle_mission_hooks(user_id, False, 0, "study", missions_extra=["Study Session"])
        await self.send_question(user_id)

    @commands.command(name="daily")
    async def daily(self, ctx):
        user = ctx.author
        user_id = user.id

        pref = await self.get_pref(user_id)
        if not pref or not pref.get("subject"):
            return await ctx.send("⚠️ Use `!study <subject> <content>` first.")

        if user_id in self.sessions:
            return await ctx.send("⚠️ You already have an active session. Use `!stop`.")

        done = await db.get_daily_answers(user_id)
        if done >= 10:
            return await ctx.send("🔥 You already completed your **10 daily questions** today!")

        thread = await self.create_private_thread(ctx, f"daily-{user.name}", user)
        if not thread:
            return

        await db.register_user(user_id)
        await db.generate_daily_missions(user_id)

        try:
            await thread.send(
                f"📅 {user.mention}, starting your **daily challenge**!\n"
                f"Progress: **{done}/10** correct answers neded.\nUse **!stop** to end."
            )
        except discord.HTTPException:
            return

        self.sessions[user_id] = {
            "mode": "daily",
            "channel": thread,
            "answered": 0,
            "correct": done,
            "last": None,
            "subject": pref["subject"],
            "content": pref["content"],
        }

        await self.send_question(user_id)

    # ==================================================
    #  MESSAGE LISTENER
    # ==================================================
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        user_id = msg.author.id
        session = self.sessions.get(user_id)

        if not session or msg.channel.id != session["channel"].id:
            return

        lock = self._locks.setdefault(user_id, asyncio.Lock())
        if lock.locked():
            return

        async with lock:
            try:
                await self._process_answer(msg, session, user_id)
            except Exception as e:
                print(f"[TRAINING ERROR] {e}")

    async def _process_answer(self, msg, session, user_id):
        content = msg.content.lower().strip()

        if content == "!stop":
            await self.end_session(user_id)
            return

        if content.startswith("!"):
            return

        question = session.get("last")
        if not question:
            return

        mode = session["mode"]
        question_type = question.get("type", "open")
        correct_value = str(question.get("correct", "")).strip().lower()
        content = msg.content.lower().strip()

        if question_type == "multiple":
            valid_letters = {k.lower() for k in (question.get("alternatives") or {})}
            user_answer = content[:1]
            correct_letter = correct_value[:1]
            is_correct = user_answer in valid_letters and user_answer == correct_letter
        else:
            user_answer = content
            is_correct = user_answer == correct_value

        xp = 0
        if is_correct:
            xp = 20 if mode == "daily" else 5
            await db.add_xp(user_id, xp)
            if mode == "daily":
                await db.increment_daily_correct(user_id)
                session["correct"] += 1
            await session["channel"].send(f"✅ **Correct!** (+{xp} XP)")
        else:
            await session["channel"].send(
                f"❌ **Wrong!** Correct answer: **{correct_value.upper()}**"
            )

        session["answered"] += 1

        await db.register_answer(
            user_id,
            question["question"],
            question_type,
            question.get("alternatives"),
            user_answer,
            correct_value,
            is_correct,
            xp,
            mode == "daily",
        )

        await self.handle_mission_hooks(user_id, is_correct, xp, mode)
        await self.check_achievements(user_id)

        if mode == "daily" and session["correct"] >= 10:
            try:
                await session["channel"].send(
                    "🏆 **Congratulations!** You've completed your daily 10. See you tomorrow!"
                )
            except discord.HTTPException:
                pass
            await self.check_daily_achievement(user_id)
            await self.end_session(user_id)
            return

        await asyncio.sleep(1.5)
        await self.send_question(user_id)

    async def check_daily_achievement(self, user_id):
        unlocked = await db.unlock_achievement(user_id, "first_daily")
        if unlocked:
            achievement = await db.get_achievement_by_key("first_daily")
            if achievement:
                await self.send_achievement_feedback(user_id, achievement)


async def setup(bot):
    await bot.add_cog(Training(bot))