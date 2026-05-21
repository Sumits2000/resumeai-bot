"""
In-memory daily rate limiter.
Resets counts at midnight automatically.
"""
import logging
from datetime import date
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Tracks how many times each user_id has generated today.
    Automatically resets at the start of a new calendar day.
    """

    def __init__(self):
        self._counts: dict[int, int] = defaultdict(int)
        self._date: date = date.today()

    def _maybe_reset(self):
        today = date.today()
        if today != self._date:
            logger.info(f"Daily reset — clearing {len(self._counts)} user counters.")
            self._counts.clear()
            self._date = today

    def get_count(self, user_id: int) -> int:
        self._maybe_reset()
        return self._counts[user_id]

    def increment(self, user_id: int):
        self._maybe_reset()
        self._counts[user_id] += 1
        logger.debug(f"User {user_id} count → {self._counts[user_id]}")
