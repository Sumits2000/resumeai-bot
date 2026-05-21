"""
Configuration — all settings in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Required keys ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY: str     = os.getenv("GEMINI_API_KEY", "")

# ── Business settings ─────────────────────────────────────────────────────────
FREE_DAILY_LIMIT: int  = 2      # free resumes per user per day
PRO_MONTHLY_PRICE: int = 399    # ₹ per month

# ── Gemini model (free tier) ──────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-2.5-flash-preview-05-20"

# ── Validation ────────────────────────────────────────────────────────────────
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set. Add it to Railway Variables.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set. Add it to Railway Variables.")
