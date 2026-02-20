"""
Scenario template and instance management routes.

Serves:  /api/v1/scenarios/...

Route ordering is intentional: literal paths (/instances/...) are defined
before parameterised paths (/{scenario_id}) so FastAPI resolves them correctly.
"""

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from typing import List
from models import ScenarioResponse, ActionRequest, ActionResponse
from store.agent_store import agent_store
from scenarios.templates import ScenarioManager
from scenarios.instances import scenario_instance_manager
from scenarios.generator import generate_world_entities
from game_session import session_manager
from ai_agents.agent_pool import get_agent_pool
import os

router = APIRouter(tags=["Scenarios"])

ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'dev-token')


# ---- Scenario templates ------------------------------------------------

@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios():
    """List all available scenario templates."""
    return [
        ScenarioResponse(
            scenario_id=s.scenario_id,
            name=s.name,
            description=s.description,
            rules=s.rules,
            objectives=s.objectives,
            max_turns=s.max_turns,
            difficulty=s.difficulty,
        )
        for s in ScenarioManager.get_all_templates()
    ]


# ---- Instance management (literal paths first) ------------------------

@router.get("/instances", summary="List all running scenario instances")
async def list_scenario_instances():
    """List all running scenario instances."""
    insts = scenario_instance_manager.list_instances()
    return [
        {
            'instance_id': i.instance_id,
            'scenario_id': i.scenario_id,
            'status': getattr(i, 'status', 'active'),
            'players': i.players,
            'created_at': i.created_at.isoformat(),
        }
        for i in insts
    ]


@router.get("/instances/{instance_id}", summary="Get a specific scenario instance")
async def get_scenario_instance(instance_id: str):
    """Get details and full world state for a running scenario instance."""
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return {
        'instance_id': inst.instance_id,
        'scenario_id': inst.scenario_id,
        'status': getattr(inst, 'status', 'active'),
        'players': inst.players,
        'created_at': inst.created_at.isoformat(),
        'active': getattr(inst, 'active', True),
        'state': inst.state.to_dict(),
    }


@router.post("/instances/{instance_id}/stop", summary="Stop a scenario instance (admin)")
async def stop_scenario_instance(instance_id: str, x_admin_token: str = Header(None)):
    """Stop a running scenario instance. Requires admin token."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not scenario_instance_manager.stop_instance(instance_id):
        raise HTTPException(status_code=404, detail="Instance not found")
    return {'instance_id': instance_id, 'stopped': True}


@router.delete("/instances/{instance_id}", summary="Delete a scenario instance (admin)")
async def delete_scenario_instance(instance_id: str, x_admin_token: str = Header(None)):
    """Permanently delete a scenario instance. Requires admin token."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not scenario_instance_manager.delete_instance(instance_id):
        raise HTTPException(status_code=404, detail="Instance not found")
    return {'instance_id': instance_id, 'deleted': True}


@router.post("/instances/{instance_id}/join", summary="Join a running scenario instance")
async def join_scenario_instance(instance_id: str, agent_id: str = Query(...)):
    """
    Join a running scenario instance as an agent.

    The agent is added into the live world state and a dedicated game session is
    created for it.  Other agents in the same instance are unaffected.
    Joining is only allowed once the instance status is ``active``.
    """
    instance = scenario_instance_manager.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if getattr(instance, 'status', 'active') not in ('active',):
        raise HTTPException(
            status_code=409,
            detail=f"Instance is not ready yet (status: {instance.status}). "
                   "Poll GET /instances/{instance_id} until status is 'active'."
        )

    if not agent_store.agent_exists(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    instance.add_player_entity(agent_id)
    session = session_manager.create_session(
        instance.scenario_id,
        agent_id,
        existing_state=instance.state,
        instance_id=instance.instance_id,
    )
    session_manager.start_session(session.game_id)

    return {
        'game_id': session.game_id,
        'instance_id': instance.instance_id,
        'scenario_id': instance.scenario_id,
        'agent_id': agent_id,
    }


@router.post("/instances/{instance_id}/action", response_model=ActionResponse,
             summary="Submit an action in a scenario instance")
async def instance_action(
    instance_id: str,
    request: ActionRequest,
    agent_id: str = Query(..., description="Agent ID that previously joined this instance"),
):
    """
    Submit an action for an agent within a running scenario instance.

    ``agent_id`` must match an agent that has already joined this instance via
    ``POST /instances/{instance_id}/join``.  The action is routed to that
    agent's game session and processed immediately — NPC AI reactions are
    dispatched asynchronously by the engine on the next tick.

    This endpoint is equivalent to ``POST /api/v1/games/{game_id}/action`` but
    addressed by instance + agent rather than game_id, which is more natural
    for agents that track their ``instance_id`` rather than ``game_id``.
    """
    instance = scenario_instance_manager.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if getattr(instance, 'status', 'active') != 'active':
        raise HTTPException(
            status_code=409,
            detail=f"Instance is not active (status: {instance.status}). "
                   "Poll GET /instances/{instance_id} until status is 'active'."
        )

    session = session_manager.get_session_by_instance_agent(instance_id, agent_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="No active session found for this agent in this instance. "
                   "Join the instance first via POST /instances/{instance_id}/join."
        )

    params = dict(request.params or {})
    if request.prompt_summary:
        params['prompt_summary'] = request.prompt_summary

    success, message, state_update = session.process_action(request.action, params)
    return ActionResponse(
        success=success,
        message=message,
        state_update=state_update,
        turn=session.turn,
    )


# ---- Parameterised template paths (must follow all literals) ----------

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario template."""
    scenario = ScenarioManager.get_template(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioResponse(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        description=scenario.description,
        rules=scenario.rules,
        objectives=scenario.objectives,
        max_turns=scenario.max_turns,
        difficulty=scenario.difficulty,
    )


@router.post("/{scenario_id}/instances", summary="Create a new scenario instance")
async def start_scenario_instance(scenario_id: str, background_tasks: BackgroundTasks):
    """
    Spawn a persistent always-on world from a scenario template.

    The instance is created immediately (status ``generating``) and world
    entities are built in the background — either by a connected
    ``scenario_generator`` AI agent, or by the built-in rule-based engine
    if no AI agent is registered.  Poll
    ``GET /api/v1/scenarios/instances/{instance_id}`` until ``status`` is
    ``active`` before sending agents to join.
    """
    if not ScenarioManager.get_template(scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    instance = scenario_instance_manager.create_instance(scenario_id)

    async def _generate():
        pool = await get_agent_pool()
        await generate_world_entities(instance, agent_pool=pool)

    background_tasks.add_task(_generate)

    return {
        'instance_id': instance.instance_id,
        'scenario_id': scenario_id,
        'status': instance.status,
        'message': 'World generation started. Poll status until active.',
        'created_at': instance.created_at.isoformat(),
    }
