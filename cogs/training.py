import discord
from discord.ext import commands
import asyncio
from services.gemini import generate_gemini_question
import database.database as db

# This cog handles the training sessions, including the unlimited quiz mode and the daily challenge.
class Training(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}  

    # Helper to get study preferences.
    def get_pref(self, user_id):
        study = self.bot.get_cog("Study")
        if study:
            return study.get_preference(user_id)
        return None

    # Helper to create private thread and set permissions.
    async def create_private_thread(self, ctx, name, user):
        thread = await ctx.channel.create_thread(
            name=name,
            type=discord.ChannelType.public_thread
        )

        overwrite = discord.PermissionOverwrite(send_messages=False)

        for member in ctx.channel.members:
            if member.id not in (user.id, ctx.guild.me.id):
                try:
                    await thread.set_permissions(member, overwrite=overwrite)
                except:
                    pass

        return thread

    # Helper to send a question to the user.
    async def send_question(self, user_id):
        if user_id not in self.sessions:
            return

        session = self.sessions[user_id]
        channel = session["channel"]

        await channel.send("⌛ Generating question...")

        try:
            # Note: Ensure the function name matches your translated services/gemini.py.
            question = await asyncio.wait_for(
                generate_gemini_question(session["subject"], session["content"]),
                timeout=25
            )
        except Exception as e:
            print(f"[GEMINI ERROR]: {e}")
            await channel.send("❌ Error generating question. Session ended.")
            await self.end_session(user_id)
            return

        if not question or "question" not in question:
            await channel.send("❌ AI returned an invalid question.")
            await self.end_session(user_id)
            return

        session["last"] = question
        await channel.send(f"🧠 **{question['question']}**")

        if question["type"] == "multiple":
            alt = question["alternatives"]
            options = "\n".join([f"**{l})** {alt[l]}" for l in "ABCDE"])
            await channel.send(options)

    # Helper to end a session
    async def end_session(self, user_id):
        if user_id not in self.sessions:
            return
        channel = self.sessions[user_id]["channel"]
        try:
            await channel.send("🛑 Session ended.")
            await channel.edit(archived=True)
        except:
            pass
        if user_id in self.sessions:
            del self.sessions[user_id]

    # Unlimited Quiz Command
    @commands.command(name="quiz")
    async def quiz(self, ctx):
        user = ctx.author
        user_id = user.id

        pref = self.get_pref(user_id)
        if not pref:
            return await ctx.send("⚠️ Use `!study <subject> <content>` first to set your topics.")
        
        if user_id in self.sessions:
            return await ctx.send("⚠️ You already have an active session. Use `!stop` inside your thread.")

        thread = await self.create_private_thread(ctx, f"quiz-{user.name}", user)
        await thread.send(f"🎮 {user.mention}, your quiz has started!\nUse **!stop** to end the session.")

        self.sessions[user_id] = {
            "mode": "study",
            "channel": thread,
            "answered": 0,
            "last": None,
            "subject": pref["subject"],
            "content": pref["content"]
        }

        await self.send_question(user_id)

    # Daily Challenge Command
    @commands.command(name="daily")
    async def daily(self, ctx):
        user = ctx.author
        user_id = user.id

        pref = self.get_pref(user_id)
        if not pref:
            return await ctx.send("⚠️ Use `!study <subject> <content>` first.")
            
        if user_id in self.sessions:
            return await ctx.send("⚠️ You already have an active session. Use `!stop`.")

        done = await db.get_daily_answers(user_id)
        if done >= 10:
            return await ctx.send("🔥 You already completed your **10 daily questions** today!")

        thread = await self.create_private_thread(ctx, f"daily-{user.name}", user)
        await thread.send(f"📅 {user.mention}, starting your **daily challenge**!\n"
                          f"Progress: **{done}/10**.\nUse **!stop** to end.")

        self.sessions[user_id] = {
            "mode": "daily",
            "channel": thread,
            "answered": done,
            "last": None,
            "subject": pref["subject"],
            "content": pref["content"]
        }

        await self.send_question(user_id)

    # Message listener to handle quiz answers.
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        user_id = msg.author.id
        session = self.sessions.get(user_id)

        # Ensure the message is in the user's active quiz thread.
        if not session or msg.channel.id != session["channel"].id:
            return

        content = msg.content.lower().strip()

        # Stop command.
        if content == "!stop":
            await self.end_session(user_id)
            return

        question = session["last"]
        if not question:
            return

        # Normalize answer check.
        correct = str(question["correct"]).strip().lower()
        if question["type"] == "multiple":
            # Just take the first character (the letter).
            correct = correct[0]

        is_correct = (content == correct)

        # Calculate XP: 20 for daily, 5 for normal quiz.
        xp = 0
        if is_correct:
            xp = 20 if session["mode"] == "daily" else 5
            await db.add_xp(user_id, xp)
            await session["channel"].send(f"✅ **Correct!** (+{xp} XP)")
        else:
            await session["channel"].send(f"❌ **Wrong!** Correct answer: **{correct.upper()}**")

        # Update daily progress in DB.
        if session["mode"] == "daily":
            await db.increment_daily_answer(user_id)

        session["answered"] += 1

        # Check for Daily Challenge completion.
        if session["mode"] == "daily" and session["answered"] >= 10:
            await session["channel"].send("🏆 **Congratulations!** You've completed your daily 10. See you tomorrow!")
            await self.end_session(user_id)
        else:
            # Brief pause for the user to read the feedback.
            await asyncio.sleep(1.5)
            await self.send_question(user_id)

async def setup(bot):
    await bot.add_cog(Training(bot))