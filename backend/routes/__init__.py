"""
Routes package — all API route handlers.

Each module exposes a FastAPI `router` that main.py includes with its prefix.
"""

from routes.agents import router as agents_router
from routes.games import router as games_router
from routes.scenarios import router as scenarios_router
from routes.feed import router as feed_router
from routes.analytics import router as analytics_router
from routes.ai_agents import router as ai_agents_router

__all__ = [
    'agents_router',
    'games_router',
    'scenarios_router',
    'feed_router',
    'analytics_router',
    'ai_agents_router',
]
