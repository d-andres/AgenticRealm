"""
Agent registration and lookup routes.

Serves:  /api/v1/agents/...

All agents — player and system — register and connect through these endpoints.
Set the ``role`` field to declare what the agent does:
  player             — participates in the world scenario
  npc_admin          — manages NPC behaviour; polls /npc-tasks on active instances
  scenario_generator — generates world content at instance creation time
  storyteller        — provides narrative commentary via /memory writes
  game_master        — high-level world orchestration
"""

from fastapi import APIRouter, HTTPException
from models import AgentRegisterRequest, AgentResponse

from store.agent_store import agent_store

router = APIRouter(tags=["Agents"])


@router.post("/register", response_model=AgentResponse)
async def register_agent(request: AgentRegisterRequest):
    """
    Register an agent (player or system).  System agents should set ``role``
    to one of: npc_admin, scenario_generator, storyteller, game_master.
    After registering, system agents join an instance and begin their own
    polling loop — they are not managed by the backend.
    """
    try:
        agent = agent_store.register({
            'name': request.name,
            'description': request.description,
            'creator': request.creator,
            'model': request.model,
            'system_prompt': request.system_prompt,
            'role': request.role,
            'skills': request.skills,
        })
        return AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            creator=agent.creator,
            model=agent.model,
            role=agent.role,
            is_system_agent=agent.is_system_agent,
            skills=agent.skills,
            created_at=agent.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="List all registered agents")
async def list_agents():
    """List all registered agents (player and system)."""
    agents = agent_store.get_all_agents()
    return {'agents': [a.to_dict() for a in agents], 'total': len(agents)}


@router.get("/by-role/{role}", summary="List agents by role")
async def list_agents_by_role(role: str):
    """Return all agents registered with a specific role (e.g. npc_admin, player)."""
    agents = agent_store.get_by_role(role)
    return {'role': role, 'agents': [a.to_dict() for a in agents], 'total': len(agents)}


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
        role=agent.role,
        is_system_agent=agent.is_system_agent,
        skills=agent.skills,
        created_at=agent.created_at,
    )
