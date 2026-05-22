"""
ResumeAI Bot — Telegram Bot powered by Google Gemini (Free API)
Co-founders: You + Claude
"""

import sys
import os

# Ensure the project root is always on the path (fixes Railway deployment)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from utils.gemini import generate_resume, generate_cover_letter
from utils.docx_maker import generate_docx
from utils.database import Database
from utils.rate_limiter import RateLimiter
from config import (
    TELEGRAM_BOT_TOKEN,
    FREE_DAILY_LIMIT,
    PRO_MONTHLY_PRICE,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
(
    ASKING_JOB,
    ASKING_EXPERIENCE,
    ASKING_SKILLS,
    ASKING_EDUCATION,
    CHOOSING_OUTPUT,
) = range(5)

# ── Shared resources (initialised in main) ───────────────────────────────────
db: Database = None
limiter: RateLimiter = None


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Create Resume", callback_data="start_resume"),
         InlineKeyboardButton("✉️ Cover Letter", callback_data="start_cover")],
        [InlineKeyboardButton("⭐ Upgrade to Pro", callback_data="upgrade"),
         InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ])


def output_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Resume Only", callback_data="out_resume"),
         InlineKeyboardButton("✉️ Cover Letter Only", callback_data="out_cover")],
        [InlineKeyboardButton("📦 Both", callback_data="out_both")],
        [InlineKeyboardButton("🔄 Start Over", callback_data="restart")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])


async def check_limit(user_id: int) -> tuple[bool, int]:
    """Returns (can_proceed, remaining_count)."""
    user = db.get_user(user_id)
    if user and user.get("is_pro"):
        return True, 999
    count = limiter.get_count(user_id)
    remaining = max(0, FREE_DAILY_LIMIT - count)
    return remaining > 0, remaining


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.upsert_user(user.id, user.first_name, user.username)

    # Handle referral
    args = context.args
    if args and args[0].startswith("ref_"):
        referrer_id = args[0][4:]
        db.record_referral(referrer_id, user.id)
        referral_bonus = db.check_referral_bonus(referrer_id)
        if referral_bonus:
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 Someone joined using your link! You've earned *7 days Pro free!*",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    welcome = (
        f"👋 Welcome, *{user.first_name}*!\n\n"
        f"I'm *ResumeAI* — your personal career assistant powered by Google Gemini AI.\n\n"
        f"I'll help you create a *professional resume* and *cover letter* in under 2 minutes. "
        f"Completely free to start!\n\n"
        f"🆓 Free plan: *{FREE_DAILY_LIMIT} resumes/day*\n"
        f"⭐ Pro plan: *Unlimited* + ATS scoring + LinkedIn tips\n\n"
        f"What would you like to do today?"
    )
    await update.message.reply_text(
        welcome, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *ResumeAI Help*\n\n"
        "*/start* — Main menu\n"
        "*/resume* — Create a new resume\n"
        "*/cover* — Create a cover letter\n"
        "*/stats* — Your usage stats\n"
        "*/upgrade* — Upgrade to Pro\n"
        "*/refer* — Get your referral link\n"
        "*/help* — Show this message\n\n"
        "💡 *Tips:*\n"
        "• Be specific about your job title and company\n"
        "• List your top 3–5 achievements, not just duties\n"
        "• Mention the tech stack or tools you use\n"
    )
    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    count = limiter.get_count(user_id)
    total = db.get_total_resumes(user_id)
    referrals = db.get_referral_count(user_id)
    is_pro = user.get("is_pro", False) if user else False

    plan = "⭐ Pro" if is_pro else f"🆓 Free ({FREE_DAILY_LIMIT - count} left today)"
    text = (
        f"📊 *Your Stats*\n\n"
        f"Plan: {plan}\n"
        f"Resumes created (total): *{total}*\n"
        f"Friends referred: *{referrals}*\n\n"
        f"{'✅ Unlimited resumes active!' if is_pro else f'Refer 3 friends → get 7 days Pro free!'}"
    )
    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    referrals = db.get_referral_count(user_id)
    needed = max(0, 3 - referrals)

    text = (
        f"🔗 *Your Referral Link*\n\n"
        f"`{link}`\n\n"
        f"Share this with friends who are job hunting!\n\n"
        f"✅ Friends referred: *{referrals}/3*\n"
        f"{'🎉 You qualify for 7 days Pro free! Use /upgrade to claim.' if referrals >= 3 else f'Refer {needed} more friend(s) → 7 days Pro FREE!'}"
    )
    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referrals = db.get_referral_count(user_id)
    user = db.get_user(user_id)

    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    if user and user.get("is_pro"):
        await send(
            "⭐ You're already on Pro! Enjoy unlimited resumes.",
            reply_markup=back_keyboard()
        )
        return

    referral_text = ""
    if referrals >= 3:
        referral_text = "\n\n🎁 *You have 3 referrals — claim 7 days Pro free!*\nContact @YourSupportHandle"

    text = (
        f"⭐ *Upgrade to ResumeAI Pro*\n\n"
        f"*₹399/month* — cancel anytime\n\n"
        f"✅ Unlimited resumes & cover letters\n"
        f"✅ ATS compatibility score\n"
        f"✅ LinkedIn profile tips\n"
        f"✅ 5 premium templates\n"
        f"✅ Priority AI generation\n"
        f"{referral_text}\n\n"
        f"💳 To subscribe, contact @YourSupportHandle or pay via UPI:\n"
        f"`your-upi@bank`\n\n"
        f"Send payment screenshot to activate instantly."
    )
    await send(text, parse_mode="Markdown", reply_markup=back_keyboard())


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION — RESUME FLOW
# ═══════════════════════════════════════════════════════════════════════════════

async def resume_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — works for /resume command and inline button."""
    query = update.callback_query
    if query:
        await query.answer()
        send = query.message.reply_text
    else:
        send = update.message.reply_text

    user_id = update.effective_user.id
    can_proceed, remaining = await check_limit(user_id)

    if not can_proceed:
        await send(
            f"⚠️ You've used all *{FREE_DAILY_LIMIT}* free resumes for today.\n\n"
            f"Come back tomorrow or upgrade to Pro for unlimited access!\n\n"
            f"Use /upgrade to go Pro ⭐",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Upgrade to Pro", callback_data="upgrade")],
                [InlineKeyboardButton("🔗 Refer Friends (Free Pro)", callback_data="refer")],
            ])
        )
        return ConversationHandler.END

    context.user_data.clear()
    await send(
        f"📄 *Let's build your resume!*\n\n"
        f"*Step 1/4* — What job are you applying for?\n\n"
        f"_Example: Software Engineer at a fintech startup, Marketing Manager at FMCG company_",
        parse_mode="Markdown",
    )
    return ASKING_JOB


async def got_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Got it! Targeting: *{context.user_data['job']}*\n\n"
        f"*Step 2/4* — Tell me about your work experience.\n\n"
        f"_Share your top 2–3 achievements or responsibilities. Example:_\n"
        f"_'3 years as a backend developer, built REST APIs serving 1M users, reduced latency by 40%'_",
        parse_mode="Markdown",
    )
    return ASKING_EXPERIENCE


async def got_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text.strip()
    await update.message.reply_text(
        f"💪 Great experience!\n\n"
        f"*Step 3/4* — What are your top skills?\n\n"
        f"_List tools, technologies, or soft skills. Example:_\n"
        f"_'Python, Django, PostgreSQL, AWS, team leadership, agile'_",
        parse_mode="Markdown",
    )
    return ASKING_SKILLS


async def got_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["skills"] = update.message.text.strip()
    await update.message.reply_text(
        f"🎓 *Step 4/4* — What's your educational background?\n\n"
        f"_Example: 'B.Tech Computer Science, IIT Delhi, 2022'_\n"
        f"_Or just: 'BBA from Delhi University, 2021'_",
        parse_mode="Markdown",
    )
    return ASKING_EDUCATION


async def got_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["education"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ All set! What would you like me to generate?",
        reply_markup=output_keyboard(),
    )
    return CHOOSING_OUTPUT


async def generate_output(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data  # out_resume | out_cover | out_both

    user_id = update.effective_user.id
    user_data = context.user_data

    thinking_msg = await query.message.reply_text("⏳ Generating your content with AI... please wait!")

    results = []   # list of (title, text, doc_type)
    error = None

    try:
        if choice in ("out_resume", "out_both"):
            resume_text = await generate_resume(
                job=user_data.get("job", ""),
                experience=user_data.get("experience", ""),
                skills=user_data.get("skills", ""),
                education=user_data.get("education", ""),
            )
            results.append(("📄 *YOUR RESUME*", resume_text, "resume"))

        if choice in ("out_cover", "out_both"):
            cover_text = await generate_cover_letter(
                job=user_data.get("job", ""),
                experience=user_data.get("experience", ""),
                skills=user_data.get("skills", ""),
            )
            results.append(("✉️ *COVER LETTER*", cover_text, "cover"))

    except Exception as e:
        logger.error(f"Generation error for user {user_id}: {e}")
        error = str(e)

    await thinking_msg.delete()

    if error:
        await query.message.reply_text(
            "❌ Something went wrong while generating. Please try again in a moment.\n\n"
            f"Error: `{error}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )
        return ConversationHandler.END

    # Record usage
    limiter.increment(user_id)
    db.increment_resume_count(user_id)

    import io as _io

    # Send each result — full text in chunks + Word file
    for title, text_content, doc_type in results:
        # 1. Send header separately (Markdown safe)
        await query.message.reply_text(title, parse_mode="Markdown")

        # 2. Send full plain text in chunks — no Markdown to avoid parse failures
        for chunk in split_message(text_content, 3800):
            await query.message.reply_text(chunk)

        # 3. Generate and send .docx
        docx_msg = await query.message.reply_text("📎 Creating your Word file...")
        try:
            docx_bytes = await generate_docx(text_content, doc_type)
            fname = "Resume.docx" if doc_type == "resume" else "Cover_Letter.docx"
            await query.message.reply_document(
                document=_io.BytesIO(docx_bytes),
                filename=fname,
                caption=f"✅ Your {fname} is ready! Open in Word or Google Docs to edit and save as PDF.",
            )
            await docx_msg.delete()
        except Exception as e:
            err_detail = str(e)
            logger.error(f"DOCX error for user {user_id}: {err_detail}", exc_info=True)
            await docx_msg.edit_text(
                f"⚠️ Word file error: {err_detail[:300]}\n\nYour text above is complete — paste into Word or Google Docs!"
            )
    # Referral nudge
    _, remaining = await check_limit(user_id)
    bot_username = (await context.bot.get_me()).username

    nudge = (
        f"\n\n🔗 Know someone job-hunting? Share your referral link — get *7 days Pro free* after 3 referrals!\n"
        f"`https://t.me/{bot_username}?start=ref_{user_id}`"
    )

    await query.message.reply_text(
        f"✅ Done! {'You have *' + str(remaining) + '* free generation(s) left today.' if remaining < FREE_DAILY_LIMIT else '🌟 Unlimited generations active!'}{nudge}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Cancelled. Back to main menu!", reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK QUERY HANDLER (buttons outside conversation)
# ═══════════════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    send = query.message.reply_text   # always use query.message for buttons

    if data == "main_menu":
        await send("🏠 Main Menu", reply_markup=main_menu_keyboard())
    elif data == "upgrade":
        await upgrade_command(update, context)
    elif data == "stats":
        await stats_command(update, context)
    elif data == "refer":
        await refer_command(update, context)
    elif data == "help":
        await help_command(update, context)
    elif data == "restart":
        await send("🔄 Let\'s start fresh!", reply_markup=main_menu_keyboard())
    elif data in ("start_resume", "start_cover"):
        context.user_data.clear()
        await resume_start(update, context)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def split_message(text: str, limit: int = 4000) -> list[str]:
    """Split long messages at newline boundaries."""
    if len(text) <= limit:
        return [text]
    chunks, current = [], []
    current_len = 0
    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > limit:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    global db, limiter
    db = Database()
    limiter = RateLimiter()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for the resume/cover letter flow
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("resume", resume_start),
            CommandHandler("cover", resume_start),
            CallbackQueryHandler(resume_start, pattern="^start_(resume|cover)$"),
        ],
        states={
            ASKING_JOB:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_job)],
            ASKING_EXPERIENCE:[MessageHandler(filters.TEXT & ~filters.COMMAND, got_experience)],
            ASKING_SKILLS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_skills)],
            ASKING_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_education)],
            CHOOSING_OUTPUT:  [CallbackQueryHandler(generate_output, pattern="^out_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("refer", refer_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))
    app.add_handler(conv)
    # Generic button handler (for menus outside the conversation)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 ResumeAI Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
