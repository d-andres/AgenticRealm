"""
AI Agent management routes.

Serves:  /api/v1/ai-agents/...

These endpoints manage the LLM-backed system agents (OpenAI, Anthropic) that
power NPC behaviour and scenario generation.  This is separate from user agent
registration (/api/v1/agents) which is for the external player agents.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

from ai_agents.interfaces import AgentRole
from ai_agents.agent_pool import get_agent_pool
from ai_agents.openai_agents import OpenAIScenarioGeneratorAgent, OpenAINPCAdminAgent
from ai_agents.anthropic_agents import AnthropicScenarioGeneratorAgent, AnthropicNPCAdminAgent

# No prefix here — main.py provides the /api/v1/ai-agents prefix via include_router
router = APIRouter(tags=["AI Agents"])


# ---- Request / Response models ----------------------------------------

class AgentRegistrationRequest(BaseModel):
    """Request to register a system AI agent."""
    agent_name: str
    agent_role: str   # "scenario_generator" | "npc_admin"
    agent_type: str   # "openai" | "anthropic"  (legacy: "gpt" → "openai")
    config: dict      # Provider-specific: {"api_key": "...", "model": "..."}


class AgentStatusResponse(BaseModel):
    """Status snapshot of a registered system AI agent."""
    agent_name: str
    agent_role: str
    is_connected: bool
    request_count: int = 0


class AgentListResponse(BaseModel):
    agents: List[AgentStatusResponse]
    total_agents: int


# ---- Endpoints --------------------------------------------------------

@router.post("/register")
async def register_ai_agent(request: AgentRegistrationRequest):
    """
    Register and connect a system AI agent (OpenAI or Anthropic).

    Example — OpenAI scenario generator:
    ```json
    {
        "agent_name": "openai-scenario-gen",
        "agent_role": "scenario_generator",
        "agent_type": "openai",
        "config": {"api_key": "sk-...", "model": "gpt-4o"}
    }
    ```

    Example — Anthropic NPC admin:
    ```json
    {
        "agent_name": "claude-npc-admin",
        "agent_role": "npc_admin",
        "agent_type": "anthropic",
        "config": {"api_key": "sk-ant-...", "model": "claude-sonnet-4-5"}
    }
    ```
    """
    try:
        pool = await get_agent_pool()

        agent_type = request.agent_type.lower()
        if agent_type == "gpt":   # legacy alias
            agent_type = "openai"

        _AGENT_FACTORIES = {
            ("openai",    "scenario_generator"): (OpenAIScenarioGeneratorAgent,    {"model": "gpt-4o"}),
            ("openai",    "npc_admin"):           (OpenAINPCAdminAgent,             {"model": "gpt-4o"}),
            ("anthropic", "scenario_generator"): (AnthropicScenarioGeneratorAgent, {"model": "claude-sonnet-4-5"}),
            ("anthropic", "npc_admin"):           (AnthropicNPCAdminAgent,          {"model": "claude-sonnet-4-5"}),
        }

        key = (agent_type, request.agent_role)
        if key not in _AGENT_FACTORIES:
            raise ValueError(
                f"Unsupported combination: agent_type='{agent_type}', "
                f"agent_role='{request.agent_role}'. "
                f"Valid types: openai, anthropic. "
                f"Valid roles: scenario_generator, npc_admin."
            )

        agent_cls, defaults = _AGENT_FACTORIES[key]
        agent = agent_cls(
            agent_name=request.agent_name,
            api_key=request.config.get("api_key"),
            model=request.config.get("model", defaults["model"]),
        )

        if not await pool.register_agent(agent):
            raise Exception("Failed to connect agent")

        return {
            "success": True,
            "agent_name": request.agent_name,
            "agent_role": request.agent_role,
            "message": f"Agent {request.agent_name} registered and connected",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unregister/{agent_name}")
async def unregister_ai_agent(agent_name: str):
    """Unregister and disconnect a system AI agent."""
    try:
        pool = await get_agent_pool()
        if not await pool.unregister_agent(agent_name):
            raise Exception(f"Agent not found: {agent_name}")
        return {
            "success": True,
            "agent_name": agent_name,
            "message": f"Agent {agent_name} unregistered and disconnected",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=AgentListResponse)
async def list_ai_agents():
    """Get all registered system AI agents and their connection status."""
    try:
        pool = await get_agent_pool()
        agent_list = pool.get_all_agents()
        agents = [
            AgentStatusResponse(
                agent_name=agent.agent_name,
                agent_role=role.value,
                is_connected=agent.is_connected,
            )
            for role, agent_objs in agent_list
            for agent in agent_objs
        ]
        return AgentListResponse(agents=agents, total_agents=len(agents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{agent_name}", response_model=AgentStatusResponse)
async def get_ai_agent_status(agent_name: str):
    """Get status of a specific system AI agent."""
    try:
        pool = await get_agent_pool()
        for role, agents in pool.agents.items():
            for agent in agents:
                if agent.agent_name == agent_name:
                    return AgentStatusResponse(
                        agent_name=agent.agent_name,
                        agent_role=role.value,
                        is_connected=agent.is_connected,
                    )
        raise Exception(f"Agent not found: {agent_name}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/request/{agent_role}/{action}")
async def request_ai_agent(
    agent_role: str,
    action: str,
    context: Optional[dict] = None,
    priority: str = "normal",
):
    """
    Send a request to a system agent by role.  Uses round-robin load balancing
    when multiple agents share the same role.

    Example:
    ```
    POST /api/v1/ai-agents/request/npc_admin/npc_decision
    {"context": {"npc_id": "npc_001", "situation": "Player approaches"}}
    ```
    """
    try:
        pool = await get_agent_pool()
        role_enum = AgentRole[agent_role.upper()]
        response = await pool.request(
            role=role_enum,
            action=action,
            context=context or {},
            priority=priority,
        )
        if response is None:
            raise Exception(f"No agents available for role '{agent_role}'")
        return {
            "success": response.success,
            "request_id": response.request_id,
            "action": response.action,
            "result": response.result,
            "reasoning": response.reasoning,
        }
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown agent role: {agent_role}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_agent_pool_health():
    """Health check for the system AI agent pool."""
    try:
        pool = await get_agent_pool()
        agent_list = pool.get_all_agents()
        connected = sum(1 for _, agents in agent_list for a in agents if a.is_connected)
        total = sum(len(agents) for _, agents in agent_list)
        return {
            "pool_status": "healthy" if connected > 0 else "no agents",
            "total_agents": total,
            "connected_agents": connected,
            "disconnected_agents": total - connected,
            "agents_by_role": {role.value: len(agents) for role, agents in agent_list},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
