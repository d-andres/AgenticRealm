"""
Simple in-memory feed store for condensed agent prompt summaries and events.

Used by `GameSession` to log prompt summaries for presentation and by API to
serve a public feed for the presentation screen.
"""
from typing import List, Dict

class FeedStore:
    def __init__(self):
        self.entries: List[Dict] = []

    def log(self, entry: Dict):
        # Keep a bounded list (most recent 200 entries)
        self.entries.append(entry)
        if len(self.entries) > 200:
            self.entries.pop(0)

    def get_recent(self, limit: int = 50):
        return list(self.entries[-limit:])[::-1]


# Global singleton
feed_store = FeedStore()
