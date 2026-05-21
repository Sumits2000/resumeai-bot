# 🤖 ResumeAI Bot — Setup Guide

## What you need (takes 10 minutes)

- Python 3.11+
- A Telegram account
- A Google account (for free Gemini API)

---

## Step 1 — Get your Telegram Bot Token (2 min)

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Choose a name: `ResumeAI`
4. Choose a username: `resumeai_yourname_bot`
5. Copy the token it gives you (looks like `123456:ABCdef...`)

---

## Step 2 — Get your FREE Gemini API Key (2 min)

1. Go to → **https://aistudio.google.com/apikey**
2. Sign in with Google
3. Click **"Create API Key"**
4. Copy the key (free — no credit card needed)

---

## Step 3 — Setup the bot (5 min)

```bash
# 1. Enter the folder
cd resumeai_bot

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# OR: venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env

# 5. Edit .env and paste your keys
nano .env   # or open in any text editor
```

Your `.env` should look like:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Step 4 — Run the bot

```bash
python bot.py
```

You'll see:
```
🚀 ResumeAI Bot is running...
```

Open Telegram → search your bot → send `/start` 🎉

---

## Deploy 24/7 for FREE (Railway)

1. Go to **https://railway.app** → sign up free
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Push your code to GitHub first, then connect it
4. Add environment variables in Railway dashboard
5. Done — your bot runs 24/7 without your computer being on

---

## Bot Commands

| Command | What it does |
|---------|-------------|
| `/start` | Main menu |
| `/resume` | Start resume creation |
| `/cover` | Start cover letter creation |
| `/stats` | See your usage |
| `/refer` | Get your referral link |
| `/upgrade` | See Pro plan |
| `/cancel` | Cancel current flow |
| `/help` | Show help |

---

## Monetisation Setup

1. **Edit `config.py`** to set your UPI ID and support handle
2. **Activate Pro manually** when someone pays:

```python
# Run this in Python to give a user Pro access
from utils.database import Database
db = Database()
db.activate_pro(USER_TELEGRAM_ID, days=30)
```

---

## File Structure

```
resumeai_bot/
├── bot.py              ← Main bot logic
├── config.py           ← Settings
├── requirements.txt    ← Dependencies
├── .env.example        ← Template for your keys
├── .env                ← Your real keys (never share!)
├── data/
│   └── resumeai.db     ← SQLite database (auto-created)
└── utils/
    ├── gemini.py       ← AI generation (Gemini free API)
    ├── database.py     ← User & referral management
    └── rate_limiter.py ← Daily free limit tracking
```

---

## Free Tier Limits (Gemini)

- **1,500 requests/day** — enough for early growth
- Resets at midnight Pacific Time
- No credit card needed
- Upgrade to paid Gemini when you have 50+ daily active users

---

Built with ❤️ by ResumeAI team
