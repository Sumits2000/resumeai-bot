"""
Lightweight SQLite database for user management.
No external DB needed — perfect for launch phase.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "resumeai.db"


class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id       INTEGER PRIMARY KEY,
                    first_name    TEXT,
                    username      TEXT,
                    is_pro        INTEGER DEFAULT 0,
                    pro_expires   TEXT,
                    total_resumes INTEGER DEFAULT 0,
                    joined_at     TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS referrals (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id   INTEGER,
                    referred_id   INTEGER,
                    created_at    TEXT DEFAULT (datetime('now')),
                    UNIQUE(referred_id)
                );
            """)
        logger.info(f"Database ready at {DB_PATH}")

    # ── Users ─────────────────────────────────────────────────────────────────

    def upsert_user(self, user_id: int, first_name: str, username: str | None):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, first_name, username)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    username   = excluded.username
                """,
                (user_id, first_name, username),
            )

    def get_user(self, user_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        user = dict(row)
        # Check if pro has expired
        if user["is_pro"] and user["pro_expires"]:
            if datetime.fromisoformat(user["pro_expires"]) < datetime.now():
                self._expire_pro(user_id)
                user["is_pro"] = 0
        return user

    def _expire_pro(self, user_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET is_pro = 0, pro_expires = NULL WHERE user_id = ?",
                (user_id,),
            )

    def activate_pro(self, user_id: int, days: int = 30):
        expires = (datetime.now() + timedelta(days=days)).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET is_pro = 1, pro_expires = ? WHERE user_id = ?",
                (expires, user_id),
            )
        logger.info(f"Pro activated for user {user_id} until {expires}")

    def increment_resume_count(self, user_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET total_resumes = total_resumes + 1 WHERE user_id = ?",
                (user_id,),
            )

    def get_total_resumes(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT total_resumes FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row["total_resumes"] if row else 0

    # ── Referrals ─────────────────────────────────────────────────────────────

    def record_referral(self, referrer_id: str, referred_id: int):
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                    (int(referrer_id), referred_id),
                )
        except Exception as e:
            logger.warning(f"Referral recording failed: {e}")

    def get_referral_count(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = ?", (user_id,)
            ).fetchone()
        return row["cnt"] if row else 0

    def check_referral_bonus(self, referrer_id: str) -> bool:
        """Returns True if this referral pushes user to exactly 3 (bonus threshold)."""
        count = self.get_referral_count(int(referrer_id))
        if count == 3:
            self.activate_pro(int(referrer_id), days=7)
            return True
        return False

    # ── Admin helpers ─────────────────────────────────────────────────────────

    def get_total_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"] if row else 0

    def get_pro_users(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM users WHERE is_pro = 1"
            ).fetchone()
        return row["cnt"] if row else 0
