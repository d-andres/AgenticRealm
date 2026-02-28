"""
Scenario template and instance management routes.

Serves:  /api/v1/scenarios/...

Route ordering is intentional: literal paths (/instances/...) are defined
before parameterised paths (/{scenario_id}) so FastAPI resolves them correctly.
"""

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from models import ScenarioResponse, ActionRequest, ActionResponse
from store.agent_store import agent_store
from store.task_queue import npc_task_queue
from store.memory_store import memory_store
from scenarios.templates import ScenarioManager
from scenarios.instances import scenario_instance_manager
from scenarios.generator import generate_world_entities
from game_session import session_manager
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
            short_description=getattr(s, 'short_description', ''),
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


@router.get("/instances/{instance_id}/npc-tasks", summary="Poll pending NPC decision tasks (npc_admin agents)")
async def get_npc_tasks(instance_id: str, limit: int = Query(20, ge=1, le=100)):
    """
    Return up to ``limit`` pending NPC decision tasks for this instance.

    Intended for external **npc_admin** agents that run their own reasoning
    loop.  Each task represents an NPC that needs a decision (reaction to a
    player action, or autonomous idle behaviour).  After reasoning, resolve
    each task via ``POST /instances/{id}/npc-tasks/{task_id}/resolve``.

    Tasks not resolved within their TTL are automatically expired by the
    engine on the next tick.
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    tasks = npc_task_queue.get_pending(instance_id, limit=limit)
    return {
        "instance_id": instance_id,
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


class NpcTaskResolution(BaseModel):
    """NPC update submitted by an external agent when resolving a task."""
    agent_id: str
    # Any subset of the fields below; all are optional.
    # trust_delta     (float) — added to NPC current trust, clamped [0,1]
    # health_delta    (float) — added to NPC current health, clamped [0,max]
    # mood            (str)   — replaces current mood
    # last_ai_message (str)   — dialogue line for next player observe
    # patrol_target   (str)   — entity_id the NPC is moving toward
    resolution: Dict[str, Any]


@router.post("/instances/{instance_id}/npc-tasks/{task_id}/resolve",
             summary="Submit an NPC decision (npc_admin agents)")
async def resolve_npc_task(
    instance_id: str,
    task_id: str,
    body: NpcTaskResolution,
):
    """
    Submit the agent's decision for a pending NPC task.

    The ``resolution`` dict may contain any combination of:
    - ``trust_delta`` (float) — change in NPC trust toward player
    - ``health_delta`` (float) — change in NPC health
    - ``mood`` (str) — new NPC mood label
    - ``last_ai_message`` (str) — NPC dialogue stored for next ``observe``
    - ``patrol_target`` (str) — entity ID the NPC should move toward

    The engine's next tick will drain resolved tasks and apply updates to
    the live world state.  Memory entries written here are immediately
    available to all other agents via ``GET /instances/{id}/memory``.
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    task = npc_task_queue.resolve(
        instance_id=instance_id,
        task_id=task_id,
        resolution=body.resolution,
        resolved_by=body.agent_id,
    )
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found or already resolved/expired.",
        )

    # Persist NPC context to shared memory so other agents have history.
    mem = memory_store.get_or_create(instance_id)
    npc_name = task.context.get("npc_name", task.npc_id)
    mem.write(
        key=f"npc:{task.npc_id}:context",
        value={
            "task_type": task.task_type,
            "resolution": body.resolution,
            "world_turn": task.context.get("world_turn"),
        },
        agent_id=body.agent_id,
    )

    return {"task_id": task_id, "status": "resolved", "npc_id": task.npc_id}


@router.get("/instances/{instance_id}/memory", summary="Read shared instance memory")
async def get_instance_memory(
    instance_id: str,
    key: Optional[str] = Query(None, description="Exact key to read (returns last 20 entries)"),
    prefix: Optional[str] = Query(None, description="Key prefix to search (returns latest per key)"),
    n: int = Query(20, ge=1, le=200, description="Max entries per key"),
):
    """
    Read shared memory for this instance.

    Agents write context here (player interaction history, NPC notes, narrative
    threads) so other agents can build on it.  Omit both ``key`` and ``prefix``
    to get the latest entry for every key.
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    mem = memory_store.get_or_create(instance_id)
    if key:
        return {"instance_id": instance_id, "key": key, "entries": mem.read(key, n)}
    if prefix:
        return {"instance_id": instance_id, "prefix": prefix, "entries": mem.search(prefix)}
    return {"instance_id": instance_id, "memory": mem.read_all_latest()}


class MemoryWriteRequest(BaseModel):
    """Request to write a shared memory entry."""
    agent_id: str
    key: str
    value: Any
    ttl_turns: Optional[int] = None


@router.post("/instances/{instance_id}/memory", summary="Write a shared memory entry")
async def write_instance_memory(instance_id: str, body: MemoryWriteRequest):
    """
    Write a context entry to the shared instance memory.

    Use structured key namespaces so agents can find each other's context:
    - ``player:{agent_id}:interactions``   — player action history
    - ``player:{agent_id}:relationship``   — per-NPC trust summaries
    - ``npc:{npc_id}:context``             — NPC admin's running notes
    - ``npc:{npc_id}:dialogue_history``    — recent NPC dialogue
    - ``world:narrative``                  — storyteller's narrative thread
    - ``world:facts``                      — established world facts
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    mem = memory_store.get_or_create(instance_id)
    entry = mem.write(
        key=body.key,
        value=body.value,
        agent_id=body.agent_id,
        ttl_turns=body.ttl_turns,
    )
    return {"instance_id": instance_id, "key": body.key, "written_at": entry.timestamp}


@router.get("/instances/{instance_id}/events", summary="Get recent world events for an instance")
async def get_instance_events(instance_id: str, limit: int = Query(80, ge=1, le=500)):
    """
    Return the most recent world events for a running scenario instance.
    Events are returned newest-first and include all player actions, NPC
    reactions, hazard hits, item purchases, etc.  Use this to power a
    live activity log on a host / spectator screen.
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    events = list(reversed(inst.state.events[-limit:]))
    return {'instance_id': instance_id, 'events': events, 'total': len(inst.state.events)}


@router.get("/instances/{instance_id}/players", summary="Get players currently in an instance")
async def get_instance_players(instance_id: str):
    """
    Return all agents that have joined this instance along with their
    live session stats (turn count, health, gold, score, status).
    """
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    from store.agent_store import agent_store
    players = []
    for aid in inst.players:
        agent   = agent_store.get_agent(aid)
        session = session_manager.get_session_by_instance_agent(instance_id, aid)
        entity  = inst.state.entities.get(aid)
        props   = entity.properties if entity else {}
        players.append({
            'agent_id': aid,
            'name':     agent.name if agent else aid,
            'creator':  agent.creator if agent else '',
            'status':   session.status if session else 'unknown',
            'turn':     session.turn   if session else 0,
            'health':   props.get('health'),
            'gold':     props.get('gold'),
            'score':    props.get('score'),
        })
    return {'instance_id': instance_id, 'players': players}


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
    # Persist gold, inventory, and NPC trust changes after every player action.
    try:
        import store.db as db
        db.save_instance_dict(instance.to_dict())
    except Exception:
        pass
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
        short_description=getattr(scenario, 'short_description', ''),
        description=scenario.description,
        rules=scenario.rules,
        objectives=scenario.objectives,
        max_turns=scenario.max_turns,
        difficulty=scenario.difficulty,
    )


@router.post("/{scenario_id}/instances", summary="Create a new scenario instance")
async def start_scenario_instance(
    scenario_id: str,
    background_tasks: BackgroundTasks,
    tick_rate: Optional[float] = Query(None, ge=0.5, le=30.0, description="Engine tick interval in seconds (0.5–30). Updates the global engine rate."),
):
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

    # Apply requested tick rate to the running engine before generation starts.
    from core.engine import get_engine
    if tick_rate is not None:
        get_engine().tick_rate = tick_rate

    instance = scenario_instance_manager.create_instance(scenario_id)

    async def _generate():
        await generate_world_entities(instance)

    background_tasks.add_task(_generate)

    return {
        'instance_id': instance.instance_id,
        'scenario_id': scenario_id,
        'status': instance.status,
        'tick_rate': get_engine().tick_rate,
        'message': 'World generation started. Poll status until active.',
        'created_at': instance.created_at.isoformat(),
    }
