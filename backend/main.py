"""
AgenticRealm Backend — REST API entry point.

Thin app setup only: CORS, router registration, and engine lifecycle.
All route logic lives in routes/.  All persistence/storage lives in store/.
All scenario logic lives in scenarios/.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.engine import GameEngine
from ai_agents.agent_pool import get_agent_pool, shutdown_agent_pool
from routes import (
    agents_router,
    games_router,
    scenarios_router,
    feed_router,
    analytics_router,
    ai_agents_router,
)
from scenarios.templates import ScenarioManager

load_dotenv()

# ---- FastAPI app ----------------------------------------------------

app = FastAPI(
    title="AgenticRealm API",
    description=(
        "Agentic AI Learning Platform: external user agents interact with "
        "system AI agents (OpenAI/Anthropic) inside procedurally generated scenarios."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Router registration --------------------------------------------

app.include_router(agents_router,    prefix="/api/v1/agents")
app.include_router(games_router,     prefix="/api/v1/games")
app.include_router(scenarios_router, prefix="/api/v1/scenarios")
app.include_router(feed_router,      prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(ai_agents_router, prefix="/api/v1/ai-agents")

# ---- Health & info --------------------------------------------------

from game_session import session_manager
from store.agent_store import agent_store


@app.get("/health", tags=["Health"])
async def health_check():
    """Quick health probe."""
    return {
        "status": "healthy",
        "agents_registered": len(agent_store.agents),
        "active_games": len(session_manager.sessions),
        "scenarios_available": len(ScenarioManager.TEMPLATES),
    }


@app.get("/api/v1/info", tags=["Health"])
async def get_info():
    """API metadata."""
    return {
        "name": "AgenticRealm",
        "version": "0.1.0",
        "description": "Agentic AI Learning Platform — train agents to interact with system AI agents",
        "endpoints": {
            "agents": "/api/v1/agents",
            "scenarios": "/api/v1/scenarios",
            "games": "/api/v1/games",
            "ai_agents": "/api/v1/ai-agents",
            "feed": "/api/v1/feed",
        },
    }


# ---- Engine lifecycle -----------------------------------------------

engine = GameEngine(tick_rate=float(os.getenv('TICK_RATE', '1.0')))


@app.on_event('startup')
async def startup_event():
    print("[Main] Initializing AI agent pool...")
    pool = await get_agent_pool()
    print(f"[Main] Agent pool ready (id={id(pool)})")
    try:
        await engine.start()
    except Exception as e:
        print(f"[Main] Failed to start engine: {e}")


@app.on_event('shutdown')
async def shutdown_event():
    print("[Main] Shutting down AI agent pool...")
    try:
        await shutdown_agent_pool()
        print("[Main] Agent pool shutdown complete")
    except Exception as e:
        print(f"[Main] Agent pool shutdown error: {e}")
    try:
        await engine.stop()
    except Exception as e:
        print(f"[Main] Engine stop error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
