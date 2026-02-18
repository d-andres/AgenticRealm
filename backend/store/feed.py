"""
Feed store — bounded in-memory log of agent prompt summaries and world events.

Used by GameSession to record observable agent activity, and served via
GET /api/v1/feed for the presentation display screen.
"""

from typing import List, Dict


class FeedStore:
    """Bounded FIFO list of feed entries (max 200)."""

    def __init__(self, max_size: int = 200):
        self.entries: List[Dict] = []
        self.max_size = max_size

    def log(self, entry: Dict):
        self.entries.append(entry)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)

    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Return up to `limit` most recent entries, newest first."""
        return list(self.entries[-limit:])[::-1]


# Global singleton
feed_store = FeedStore()
