"""
Data models for AgenticRealm using Pydantic

Defines request/response schemas for the API
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

class AgentRegisterRequest(BaseModel):
    """Request to register a new agent.

    `skills` is an open-ended mapping of skill_name -> level so that any AI
    agent or scenario can define whatever competencies make sense.  The system
    never hardcodes which skills exist; that is left to the scenario and the
    AI agents that generate content.

    Example: {"persuasion": 3, "deception": 2, "appraisal": 1}
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    creator: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., description="e.g., gpt-4o, claude-sonnet-4-5, etc.")
    system_prompt: str = Field(..., min_length=10, max_length=5000)
    skills: Dict[str, int] = Field(
        default_factory=dict,
        description="Open-ended skill map: {skill_name: level}.  Defined by creator."
    )

class AgentResponse(BaseModel):
    """Agent information"""
    agent_id: str
    name: str
    description: str
    creator: str
    model: str
    skills: Dict[str, int]
    created_at: datetime
    
class GameStatus(str, Enum):
    """Game session status"""
    CREATED = "created"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ActionRequest(BaseModel):
    """Request to perform an action in game.

    `action` can be any value defined by the active scenario template.
    Common actions: move, observe, talk, negotiate, buy, hire, steal, trade, interact.
    The set of valid actions is determined by the scenario's `allowed_actions` field,
    not hardcoded here.
    """
    action: str = Field(
        ...,
        description="Action type defined by the scenario template (e.g. move, talk, negotiate, buy, hire, steal, trade)"
    )
    params: Dict[str, Any] = Field(default_factory=dict)
    # Optional condensed summary of the agent's input/prompt for display in the public feed
    prompt_summary: Optional[str] = Field(None, description="Condensed summary of the agent's input/prompt")

class ActionResponse(BaseModel):
    """Response from action"""
    success: bool
    message: str
    state_update: Optional[Dict] = None
    turn: int
    stats: Optional[Dict] = None

class GameStartRequest(BaseModel):
    """Request to start a game"""
    scenario_id: str
    agent_id: str

class GameStartResponse(BaseModel):
    """Response when game starts"""
    game_id: str
    scenario_id: str
    agent_id: str
    turn: int
    state: Dict

class GameStateResponse(BaseModel):
    """Current game state"""
    game_id: str
    status: GameStatus
    turn: int
    scenario_id: str
    agent_id: str
    entities: Dict
    events: List[Dict]
    world_properties: Dict

class ScenarioResponse(BaseModel):
    """Scenario information"""
    scenario_id: str
    name: str
    description: str
    rules: str
    objectives: List[str]
    max_turns: int
    difficulty: str

class GameResultResponse(BaseModel):
    """Final game results"""
    game_id: str
    agent_id: str
    scenario_id: str
    success: bool
    score: float
    turns_taken: int
    reason: str
    feedback: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    agent_id: str
    agent_name: str
    scenario_id: str
    best_score: float
    attempts: int
    success_rate: float
    avg_turns: float
