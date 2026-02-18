"""
AgenticRealm Backend - REST API for Agentic AI Learning Platform

API-first architecture where external agents interact with built-in AI agents
in game scenarios to learn about prompt engineering and agentic workflows.
"""

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

from models import (
    AgentRegisterRequest, AgentResponse, GameStartRequest, GameStartResponse,
    GameStateResponse, ActionRequest, ActionResponse, ScenarioResponse,
    GameResultResponse
)
from agents_store import agent_store
from scenarios import ScenarioManager
from game_session import session_manager
from scenario_instances import scenario_instance_manager
from core.engine import GameEngine
import os
from feed_store import feed_store
from ai_agents.agent_pool import get_agent_pool, shutdown_agent_pool
from routes.ai_agent_routes import router as ai_agent_router

# Admin token for management endpoints (simple initial protection)
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'dev-token')

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="AgenticRealm API",
    description="API for Agentic AI Learning Platform - External agents interact with system AI agents",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AI AGENT ROUTES ====================
# Include routes for AI agent management and request routing
app.include_router(ai_agent_router, prefix="/api/v1/ai-agents", tags=["AI Agents"])

# ==================== HEALTH & INFO ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_registered": len(agent_store.agents),
        "active_games": len(session_manager.sessions),
        "scenarios_available": len(ScenarioManager.SCENARIOS)
    }

@app.get("/api/v1/info")
async def get_info():
    """Get API information"""
    return {
        "name": "AgenticRealm",
        "version": "0.1.0",
        "description": "Agentic AI Learning Platform - Train agents to interact with system AI agents",
        "endpoints": {
            "agents": "/api/v1/agents",
            "scenarios": "/api/v1/scenarios",
            "games": "/api/v1/games"
        }
    }

# ==================== AGENT ENDPOINTS ====================

@app.post("/api/v1/agents/register", response_model=AgentResponse)
async def register_agent(request: AgentRegisterRequest):
    """Register a new user agent"""
    try:
        agent = agent_store.register({
            'name': request.name,
            'description': request.description,
            'creator': request.creator,
            'model': request.model,
            'system_prompt': request.system_prompt,
            'skills': request.skills.dict()
        })
        
        return AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            creator=agent.creator,
            model=agent.model,
            skills=request.skills,
            created_at=agent.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent information"""
    agent = agent_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        description=agent.description,
        creator=agent.creator,
        model=agent.model,
        skills={'reasoning': agent.skills['reasoning'], 'observation': agent.skills['observation']},
        created_at=agent.created_at
    )

@app.get("/api/v1/agents")
async def list_agents():
    """List all registered user agents"""
    agents = agent_store.get_all_agents()
    return {
        'agents': [agent.to_dict() for agent in agents],
        'total': len(agents)
    }

# ==================== FEED ENDPOINTS ====================


@app.get("/api/v1/feed")
async def get_feed(limit: int = Query(25, ge=1, le=200)):
    """Return recent condensed prompt summaries for presentation"""
    return {
        'entries': feed_store.get_recent(limit),
        'count': len(feed_store.entries)
    }

# ==================== ENGINE STARTUP ====================

# Create and start the global engine which runs continuously so the world is always active
engine = GameEngine(tick_rate=float(os.getenv('TICK_RATE', '1.0')))


@app.on_event('startup')
async def startup_event():
    # Initialize agent pool (ready to accept AI agent registrations)
    print("[Main] Initializing AI agent pool...")
    agent_pool = await get_agent_pool()
    print(f"[Main] Agent pool ready. Pool ID: {id(agent_pool)}")
    
    # Start the continuous simulation loop
    try:
        await engine.start()
    except Exception as e:
        print(f"[Main] Failed to start engine: {e}")


@app.on_event('shutdown')
async def shutdown_event():
    # Shutdown agent pool (disconnect all registered agents)
    print("[Main] Shutting down agent pool...")
    try:
        await shutdown_agent_pool()
        print("[Main] Agent pool shutdown complete")
    except Exception as e:
        print(f"[Main] Failed to shutdown agent pool: {e}")
    
    # Stop the simulation engine
    try:
        await engine.stop()
    except Exception as e:
        print(f"[Main] Failed to stop engine: {e}")

# ==================== SCENARIO ENDPOINTS ====================

@app.get("/api/v1/scenarios", response_model=List[ScenarioResponse])
async def list_scenarios():
    """List all available scenarios with system AI agents"""
    scenarios = ScenarioManager.get_all_scenarios()
    return [
        ScenarioResponse(
            scenario_id=s.scenario_id,
            name=s.name,
            description=s.description,
            rules=s.rules,
            objectives=s.objectives,
            max_turns=s.max_turns,
            difficulty=s.difficulty
        ) for s in scenarios
    ]

@app.get("/api/v1/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str):
    """Get scenario details including system AI agent info"""
    scenario = ScenarioManager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return ScenarioResponse(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        description=scenario.description,
        rules=scenario.rules,
        objectives=scenario.objectives,
        max_turns=scenario.max_turns,
        difficulty=scenario.difficulty
    )


@app.post("/api/v1/scenarios/{scenario_id}/instances")
async def start_scenario_instance(scenario_id: str):
    """Start a persistent scenario instance (always-on world)"""
    scenario = ScenarioManager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    instance = scenario_instance_manager.create_instance(scenario_id)
    return {
        'instance_id': instance.instance_id,
        'scenario_id': scenario_id,
        'created_at': instance.created_at.isoformat()
    }


@app.get("/api/v1/scenarios/instances")
async def list_scenario_instances():
    insts = scenario_instance_manager.list_instances()
    return [{'instance_id': i.instance_id, 'scenario_id': i.scenario_id, 'players': i.players, 'created_at': i.created_at.isoformat()} for i in insts]


@app.get("/api/v1/scenarios/instances/{instance_id}")
async def get_scenario_instance(instance_id: str):
    inst = scenario_instance_manager.get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    return {
        'instance_id': inst.instance_id,
        'scenario_id': inst.scenario_id,
        'players': inst.players,
        'created_at': inst.created_at.isoformat(),
        'active': getattr(inst, 'active', True),
        'state': inst.state.to_dict()
    }


@app.post("/api/v1/scenarios/instances/{instance_id}/stop")
async def stop_scenario_instance(instance_id: str, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ok = scenario_instance_manager.stop_instance(instance_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Instance not found")

    return {'instance_id': instance_id, 'stopped': True}


@app.delete("/api/v1/scenarios/instances/{instance_id}")
async def delete_scenario_instance(instance_id: str, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ok = scenario_instance_manager.delete_instance(instance_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Instance not found")

    return {'instance_id': instance_id, 'deleted': True}


@app.post("/api/v1/scenarios/instances/{instance_id}/join")
async def join_scenario_instance(instance_id: str, agent_id: str = Query(...)):
    """Join a running scenario instance as an agent.

    The agent will be added into the running world's state and a session created
    for it to take actions. The scenario continues running for others.
    """
    instance = scenario_instance_manager.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Validate agent exists
    if not agent_store.agent_exists(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    # Add player entity to the instance
    instance.add_player_entity(agent_id)

    # Create a session attached to this instance state
    session = session_manager.create_session(instance.scenario_id, agent_id, existing_state=instance.state, instance_id=instance.instance_id)
    session_manager.start_session(session.game_id)

    return {
        'game_id': session.game_id,
        'instance_id': instance.instance_id,
        'scenario_id': instance.scenario_id,
        'agent_id': agent_id
    }

# ==================== GAME ENDPOINTS ====================

@app.post("/api/v1/games/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """
    Start a new game session.
    
    Your agent will be matched with a system AI agent in the scenario.
    """
    # Validate agent exists
    if not agent_store.agent_exists(request.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate scenario exists
    if not ScenarioManager.scenario_exists(request.scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Create game session
    # The session will automatically include system AI agents
    session = session_manager.create_session(request.scenario_id, request.agent_id)
    
    # Start the session
    session_manager.start_session(session.game_id)
    
    return GameStartResponse(
        game_id=session.game_id,
        scenario_id=session.scenario_id,
        agent_id=session.agent_id,
        turn=session.turn,
        state=session.get_state()['state'].to_dict()
    )

@app.get("/api/v1/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get current game state"""
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    
    state_dict = session.get_state()
    
    return GameStateResponse(
        game_id=session.game_id,
        scenario_id=session.scenario_id,
        agent_id=session.agent_id,
        status=session.status,
        turn=session.turn,
        entities=state_dict['state'].entities,
        events=state_dict['state'].events[-10:],  # Last 10 events
        world_properties=state_dict['scenario_info']
    )

@app.post("/api/v1/games/{game_id}/action", response_model=ActionResponse)
async def submit_action(game_id: str, request: ActionRequest):
    """
    Submit an action for your agent.
    
    System AI agents will respond automatically after your action.
    """
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # If the caller provided a top-level prompt_summary, attach it to params for logging
    params = dict(request.params or {})
    if getattr(request, 'prompt_summary', None):
        params['prompt_summary'] = request.prompt_summary

    success, message, state_update = session.process_action(request.action, params)
    
    return ActionResponse(
        success=success,
        message=message,
        state_update=state_update,
        turn=session.turn
    )

@app.post("/api/v1/games/{game_id}/end")
async def end_game(game_id: str):
    """End a game session"""
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    
    session_manager.end_session(game_id)
    
    # Update agent stats
    result = session.get_result()
    agent_store.update_game_stats(session.agent_id, result['success'])
    
    return result

@app.get("/api/v1/games/{game_id}/result", response_model=GameResultResponse)
async def get_game_result(game_id: str):
    """Get game result and feedback"""
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    
    result = session.get_result()
    
    return GameResultResponse(
        game_id=result['game_id'],
        agent_id=result['agent_id'],
        scenario_id=result['scenario_id'],
        success=result['success'],
        score=result['score'],
        turns_taken=result['turn'],
        reason=result['reason'],
        feedback=result['feedback'],
        created_at=session.created_at,
        completed_at=session.completed_at
    )

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/v1/leaderboards/{scenario_id}")
async def get_leaderboard(scenario_id: str, limit: int = Query(10, ge=1, le=100)):
    """Get leaderboard for a scenario"""
    return {
        'scenario_id': scenario_id,
        'entries': [],
        'note': 'Database integration planned'
    }

@app.get("/api/v1/analytics/agent/{agent_id}")
async def get_agent_analytics(agent_id: str):
    """Get agent performance statistics"""
    agent = agent_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success_rate = (agent.games_won / agent.games_played * 100) if agent.games_played > 0 else 0
    
    return {
        'agent_id': agent.agent_id,
        'agent_name': agent.name,
        'games_played': agent.games_played,
        'games_won': agent.games_won,
        'success_rate': success_rate
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
