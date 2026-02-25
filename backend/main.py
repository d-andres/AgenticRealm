"""
AgenticRealm Backend — REST API entry point.

Thin app setup only: CORS, router registration, and engine lifecycle.
All route logic lives in routes/.  All persistence/storage lives in store/.
All scenario logic lives in scenarios/.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.engine import GameEngine, set_engine
from routes import (
    agents_router,
    games_router,
    scenarios_router,
    feed_router,
    analytics_router,
)
from scenarios.templates import ScenarioManager

load_dotenv()

# ---- FastAPI app ----------------------------------------------------

app = FastAPI(
    title="AgenticRealm API",
    description=(
        "Agentic AI Learning Platform — external agents (player and system) "
        "connect via REST to interact inside procedurally generated scenarios. "
        "System agents (npc_admin, storyteller, game_master, etc.) register "
        "with POST /api/v1/agents/register and poll for NPC tasks just like "
        "player agents."
    ),
    version="0.2.0",
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

# ---- Static frontend (served when built dist is present) -----------

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    # Serve JS/CSS/assets under their natural paths
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str = ""):
        """SPA fallback — return index.html for any non-API path."""
        # Don't intercept API or health routes
        if full_path.startswith(("api/", "health", "docs", "openapi", "redoc")):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        return FileResponse(_FRONTEND_DIST / "index.html")


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
            "feed": "/api/v1/feed",
        },
    }


# ---- Engine lifecycle -----------------------------------------------

engine = GameEngine(tick_rate=float(os.getenv('TICK_RATE', '2.0')))
set_engine(engine)  # register as global singleton for scenarios/instances.py


@app.on_event('startup')
async def startup_event():
    try:
        await engine.start()
        print("[Main] Game engine started.")
    except Exception as e:
        print(f"[Main] Failed to start engine: {e}")


@app.on_event('shutdown')
async def shutdown_event():
    try:
        await engine.stop()
        print("[Main] Game engine stopped.")
    except Exception as e:
        print(f"[Main] Engine stop error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
