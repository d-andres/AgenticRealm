"""
Agent registration and lookup routes.

Serves:  /api/v1/agents/...
"""

from fastapi import APIRouter, HTTPException
from models import AgentRegisterRequest, AgentResponse

from store.agent_store import agent_store

router = APIRouter(tags=["Agents"])


@router.post("/register", response_model=AgentResponse)
async def register_agent(request: AgentRegisterRequest):
    """Register a new user agent."""
    try:
        agent = agent_store.register({
            'name': request.name,
            'description': request.description,
            'creator': request.creator,
            'model': request.model,
            'system_prompt': request.system_prompt,
            'skills': request.skills,
        })
        return AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            creator=agent.creator,
            model=agent.model,
            skills=agent.skills,
            created_at=agent.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="List all registered user agents")
async def list_agents():
    """List all registered user agents."""
    agents = agent_store.get_all_agents()
    return {'agents': [a.to_dict() for a in agents], 'total': len(agents)}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent information."""
    agent = agent_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        description=agent.description,
        creator=agent.creator,
        model=agent.model,
        skills=agent.skills,
        created_at=agent.created_at,
    )
