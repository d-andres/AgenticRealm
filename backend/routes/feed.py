"""
Event feed routes.

Serves:  /api/v1/feed
"""

from fastapi import APIRouter, Query
from store.feed import feed_store

router = APIRouter(tags=["Feed"])


@router.get("/feed")
async def get_feed(limit: int = Query(25, ge=1, le=200)):
    """Return recent condensed prompt summaries for the presentation display."""
    return {
        'entries': feed_store.get_recent(limit),
        'count': len(feed_store.entries),
    }
