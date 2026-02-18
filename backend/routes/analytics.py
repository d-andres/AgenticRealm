"""
Analytics and leaderboard routes.

Serves:  /api/v1/leaderboards/...
         /api/v1/analytics/...
"""

from fastapi import APIRouter, HTTPException, Query
from store.agent_store import agent_store

router = APIRouter(tags=["Analytics"])


@router.get("/leaderboards/{scenario_id}")
async def get_leaderboard(scenario_id: str, limit: int = Query(10, ge=1, le=100)):
    """Get the leaderboard for a specific scenario."""
    return {
        'scenario_id': scenario_id,
        'entries': [],
        'note': 'Database integration planned',
    }


@router.get("/analytics/agent/{agent_id}")
async def get_agent_analytics(agent_id: str):
    """Get performance statistics for a specific agent."""
    agent = agent_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    success_rate = (agent.games_won / agent.games_played * 100) if agent.games_played > 0 else 0
    return {
        'agent_id': agent.agent_id,
        'agent_name': agent.name,
        'games_played': agent.games_played,
        'games_won': agent.games_won,
        'success_rate': success_rate,
    }
