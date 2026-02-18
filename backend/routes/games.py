"""
Game session routes.

Serves:  /api/v1/games/...
"""

from fastapi import APIRouter, HTTPException
from models import (
    GameStartRequest, GameStartResponse,
    GameStateResponse, ActionRequest, ActionResponse,
    GameResultResponse,
)
from store.agent_store import agent_store
from scenarios.templates import ScenarioManager
from game_session import session_manager

router = APIRouter(tags=["Games"])


@router.post("/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """
    Start a new game session.

    Your agent will be placed into the scenario world.
    System AI agents respond dynamically after your actions.
    """
    if not agent_store.agent_exists(request.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    if not ScenarioManager.template_exists(request.scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    session = session_manager.create_session(request.scenario_id, request.agent_id)
    session_manager.start_session(session.game_id)

    return GameStartResponse(
        game_id=session.game_id,
        scenario_id=session.scenario_id,
        agent_id=session.agent_id,
        turn=session.turn,
        state=session.get_state()['state'].to_dict(),
    )


@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get the current state of a game session."""
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
        events=state_dict['state'].events[-10:],
        world_properties=state_dict['scenario_info'],
    )


@router.post("/{game_id}/action", response_model=ActionResponse)
async def submit_action(game_id: str, request: ActionRequest):
    """
    Submit an action for your agent.

    System AI agents will respond automatically after your action.
    """
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    params = dict(request.params or {})
    if getattr(request, 'prompt_summary', None):
        params['prompt_summary'] = request.prompt_summary

    success, message, state_update = session.process_action(request.action, params)

    return ActionResponse(
        success=success,
        message=message,
        state_update=state_update,
        turn=session.turn,
    )


@router.post("/{game_id}/end")
async def end_game(game_id: str):
    """End a game session and return the final result."""
    session = session_manager.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    session_manager.end_session(game_id)
    result = session.get_result()
    agent_store.update_game_stats(session.agent_id, result['success'])
    return result


@router.get("/{game_id}/result", response_model=GameResultResponse)
async def get_game_result(game_id: str):
    """Get the result and feedback for a completed game session."""
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
        completed_at=session.completed_at,
    )
