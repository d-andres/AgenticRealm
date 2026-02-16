"""
Data models for AgenticRealm using Pydantic

Defines request/response schemas for the API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class SkillModel(BaseModel):
    """Agent skills"""
    reasoning: int = Field(1, ge=1, le=5)
    observation: int = Field(1, ge=1, le=5)

class AgentRegisterRequest(BaseModel):
    """Request to register a new agent"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    creator: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., description="e.g., gpt-4, claude-3, etc.")
    system_prompt: str = Field(..., min_length=10, max_length=5000)
    skills: SkillModel

class AgentResponse(BaseModel):
    """Agent information"""
    agent_id: str
    name: str
    description: str
    creator: str
    model: str
    skills: SkillModel
    created_at: datetime
    
class GameStatus(str, Enum):
    """Game session status"""
    CREATED = "created"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ActionRequest(BaseModel):
    """Request to perform an action in game"""
    action: str = Field(..., description="Type of action: move, observe, interact")
    params: Dict = Field(default_factory=dict)
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
