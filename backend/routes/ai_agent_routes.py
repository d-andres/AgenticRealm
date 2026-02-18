"""
AI Agent Management Routes

Endpoints for:
- Registering/unregistering AI agents
- Checking agent status
- Monitoring agent health
- Triggering agent actions
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

from ai_agents.interfaces import AgentRole
from ai_agents.agent_pool import get_agent_pool
from ai_agents.openai_agents import OpenAIScenarioGeneratorAgent, OpenAINPCAdminAgent
from ai_agents.anthropic_agents import AnthropicScenarioGeneratorAgent, AnthropicNPCAdminAgent

router = APIRouter(prefix="/api/v1/ai-agents", tags=["AI Agents"])


# Request/Response Models

class AgentRegistrationRequest(BaseModel):
    """Request to register an AI agent"""
    agent_name: str
    agent_role: str  # "scenario_generator", "npc_admin", etc.
    agent_type: str  # "gpt", "claude", "custom", etc.
    config: dict  # Provider-specific config (api_key, model, etc.)


class AgentStatusResponse(BaseModel):
    """Status of a registered agent"""
    agent_name: str
    agent_role: str
    is_connected: bool
    request_count: int = 0


class AgentListResponse(BaseModel):
    """List of all registered agents"""
    agents: List[AgentStatusResponse]
    total_agents: int


# Endpoints

@router.post("/register")
async def register_agent(request: AgentRegistrationRequest):
    """
    Register an AI agent to connect to the system.
    
    The agent will try to connect immediately and remain connected
    to handle requests.
    
    Example (OpenAI):
    ```json
    {
        "agent_name": "openai-scenario-gen",
        "agent_role": "scenario_generator",
        "agent_type": "openai",
        "config": {
            "api_key": "sk-...",
            "model": "gpt-4o"
        }
    }
    ```

    Example (Anthropic):
    ```json
    {
        "agent_name": "claude-npc-admin",
        "agent_role": "npc_admin",
        "agent_type": "anthropic",
        "config": {
            "api_key": "sk-ant-...",
            "model": "claude-sonnet-4-5"
        }
    }
    ```
    """
    try:
        pool = await get_agent_pool()

        agent_type = request.agent_type.lower()
        # Support legacy 'gpt' alias for openai
        if agent_type == "gpt":
            agent_type = "openai"

        # Factory: map (provider, role) → agent class
        _AGENT_FACTORIES = {
            ("openai", "scenario_generator"): (
                OpenAIScenarioGeneratorAgent, {"model": "gpt-4o"}
            ),
            ("openai", "npc_admin"): (
                OpenAINPCAdminAgent, {"model": "gpt-4o"}
            ),
            ("anthropic", "scenario_generator"): (
                AnthropicScenarioGeneratorAgent, {"model": "claude-sonnet-4-5"}
            ),
            ("anthropic", "npc_admin"): (
                AnthropicNPCAdminAgent, {"model": "claude-sonnet-4-5"}
            ),
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
        
        # Register with pool
        success = await pool.register_agent(agent)
        
        if not success:
            raise Exception("Failed to connect agent")
        
        return {
            "success": True,
            "agent_name": request.agent_name,
            "agent_role": request.agent_role,
            "message": f"Agent {request.agent_name} registered and connected"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unregister/{agent_name}")
async def unregister_agent(agent_name: str):
    """
    Unregister and disconnect an AI agent.
    """
    try:
        pool = await get_agent_pool()
        success = await pool.unregister_agent(agent_name)
        
        if not success:
            raise Exception(f"Agent not found: {agent_name}")
        
        return {
            "success": True,
            "agent_name": agent_name,
            "message": f"Agent {agent_name} unregistered and disconnected"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
async def list_agents() -> AgentListResponse:
    """
    Get list of all registered and connected AI agents.
    """
    try:
        pool = await get_agent_pool()
        agent_list = pool.get_all_agents()
        
        agents = []
        for role, agent_objs in agent_list:
            for agent in agent_objs:
                agents.append(AgentStatusResponse(
                    agent_name=agent.agent_name,
                    agent_role=role.value,
                    is_connected=agent.is_connected
                ))
        
        return AgentListResponse(
            agents=agents,
            total_agents=len(agents)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{agent_name}")
async def get_agent_status(agent_name: str) -> AgentStatusResponse:
    """
    Get status of a specific agent.
    """
    try:
        pool = await get_agent_pool()
        
        # Search for agent
        for role, agents in pool.agents.items():
            for agent in agents:
                if agent.agent_name == agent_name:
                    return AgentStatusResponse(
                        agent_name=agent.agent_name,
                        agent_role=role.value,
                        is_connected=agent.is_connected
                    )
        
        raise Exception(f"Agent not found: {agent_name}")
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/request/{agent_role}/{action}")
async def request_agent(
    agent_role: str,
    action: str,
    context: Optional[dict] = None,
    priority: str = "normal"
):
    """
    Send a request to an agent with the given role.
    
    If multiple agents have this role, uses round-robin load balancing.
    
    Example:
    ```
    POST /api/v1/ai-agents/request/npc_admin/npc_decision
    {
        "context": {
            "npc_id": "npc_001",
            "npc_data": {"name": "Captain Dorn", "job": "guard", ...},
            "situation": "Player approaches to buy items"
        }
    }
    ```
    """
    try:
        if context is None:
            context = {}
        
        pool = await get_agent_pool()
        
        # Convert role string to enum
        role_enum = AgentRole[agent_role.upper()]
        
        # Send request to agent
        response = await pool.request(
            role=role_enum,
            action=action,
            context=context,
            priority=priority
        )
        
        if response is None:
            raise Exception(f"No agents available for role {agent_role}")
        
        return {
            "success": response.success,
            "request_id": response.request_id,
            "action": response.action,
            "result": response.result,
            "reasoning": response.reasoning
        }
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown agent role: {agent_role}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_pool_health():
    """
    Check health of agent pool and connected agents.
    """
    try:
        pool = await get_agent_pool()
        agent_list = pool.get_all_agents()
        
        connected = 0
        disconnected = 0
        
        for role, agents in agent_list:
            for agent in agents:
                if agent.is_connected:
                    connected += 1
                else:
                    disconnected += 1
        
        return {
            "pool_status": "healthy" if connected > 0 else "no agents",
            "total_agents": connected + disconnected,
            "connected_agents": connected,
            "disconnected_agents": disconnected,
            "agents_by_role": {
                role.value: len(agents) for role, agents in agent_list
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
