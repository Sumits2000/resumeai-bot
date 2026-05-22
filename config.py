"""
Configuration — all settings in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Required keys ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY: str     = os.getenv("GEMINI_API_KEY", "")

# ── Your details (EDIT THESE) ─────────────────────────────────────────────────
ADMIN_IDS: list[int]   = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]
UPI_ID: str            = os.getenv("UPI_ID", "yourname@upi")
SUPPORT_USERNAME: str  = os.getenv("SUPPORT_USERNAME", "YourTelegramUsername")

# ── Subscription plans ────────────────────────────────────────────────────────
PLANS = {
    "weekly": {
        "label":   "⚡ Weekly",
        "price":   59,
        "days":    7,
        "desc":    "Perfect for active job seekers",
        "emoji":   "⚡",
    },
    "monthly": {
        "label":   "⭐ Monthly",
        "price":   199,
        "days":    30,
        "desc":    "Best value — most popular",
        "emoji":   "⭐",
        "popular": True,
    },
    "quarterly": {
        "label":   "👑 3 Months",
        "price":   399,
        "days":    90,
        "desc":    "Save ₹198 vs monthly",
        "emoji":   "👑",
    },
}

# ── Free tier ─────────────────────────────────────────────────────────────────
FREE_DAILY_LIMIT: int = 2

# ── Gemini model ──────────────────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-2.5-flash"

# ── Validation ────────────────────────────────────────────────────────────────
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set.")
