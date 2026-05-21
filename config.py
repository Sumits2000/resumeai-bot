"""
Configuration — edit these values before running the bot.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY: str     = os.getenv("GEMINI_API_KEY", "")

# ── Business settings ─────────────────────────────────────────────────────────
FREE_DAILY_LIMIT: int   = 2        # Free resumes per user per day
PRO_MONTHLY_PRICE: int  = 399      # ₹ per month

# ── Gemini model ──────────────────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-2.5-flash-preview-05-20"   # Free-tier model

# ── Validation ────────────────────────────────────────────────────────────────
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
