"""
AI Agent Interfaces - Contract definitions for AI agents

All AI agents connected to AgenticRealm must implement the AIAgent interface.
This ensures consistency and allows plug-and-play AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentRole(Enum):
    """Types of AI agents in the system"""
    SCENARIO_GENERATOR = "scenario_generator"      # Generates scenarios
    NPC_ADMIN = "npc_admin"                        # Manages NPCs
    GAME_MASTER = "game_master"                    # Orchestrates gameplay
    JUDGE = "judge"                                # Evaluates outcomes
    STORYTELLER = "storyteller"                    # Generates narrative/feedback
    CUSTOM = "custom"                              # User-defined agent


@dataclass
class AIAgentRequest:
    """Request from system to AI agent"""
    agent_role: AgentRole
    action: str  # e.g., "generate_scenario", "respond_to_player", "evaluate_outcome"
    context: Dict[str, Any]  # Event-specific data
    request_id: str = ""  # Unique request ID for tracking
    priority: str = "normal"  # normal, high, critical


@dataclass
class AIAgentResponse:
    """Response from AI agent back to system"""
    request_id: str
    agent_role: AgentRole
    success: bool
    action: str  # echoes request action
    result: Dict[str, Any]  # agent's decision/generation
    reasoning: str = ""  # why the agent made this decision
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIAgent(ABC):
    """
    Abstract base class for AI agents.
    
    An AI agent is connected to AgenticRealm and listens for events.
    When an event matching its role occurs, it processes and responds.
    
    Example:
        class MyNPCAdminAgent(AIAgent):
            async def connect(self):
                # Connect to AgenticRealm, register as NPC_ADMIN
                pass
            
            async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
                if request.action == "npc_decision":
                    npc_id = request.context["npc_id"]
                    player_action = request.context["player_action"]
                    # Use LLM to decide NPC response
                    decision = await self.llm.generate(...)
                    return AIAgentResponse(
                        request_id=request.request_id,
                        agent_role=AgentRole.NPC_ADMIN,
                        success=True,
                        action="npc_decision",
                        result=decision
                    )
    """
    
    def __init__(self, agent_name: str, role: AgentRole):
        """
        Args:
            agent_name: Unique name for this agent instance
            role: What type of agent this is
        """
        self.agent_name = agent_name
        self.role = role
        self.is_connected = False
        self.request_queue: List[AIAgentRequest] = []
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to AgenticRealm server.
        
        Returns:
            True if connection successful, False otherwise
            
        Implementation should:
        1. Establish connection to AgenticRealm API/WebSocket
        2. Register as this agent role
        3. Start listening for requests
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from AgenticRealm.
        
        Returns:
            True if disconnect successful
        """
        pass
    
    @abstractmethod
    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        """
        Process a request from AgenticRealm.
        
        This is where the AI agent makes decisions using its LLM.
        
        Args:
            request: The request from the system
            
        Returns:
            Response with the agent's decision
            
        Implementation should:
        1. Extract context from request
        2. Call your LLM/AI provider with appropriate prompt
        3. Parse LLM response
        4. Return structured response
        """
        pass
    
    async def listen(self):
        """
        Start listening for requests from AgenticRealm.
        
        This runs continuously while agent is connected.
        When system sends request, handle_request is called.
        """
        if not self.is_connected:
            if not await self.connect():
                raise Exception(f"Failed to connect agent {self.agent_name}")
        
        # This would be implemented by the connection mechanism
        # (WebSocket, polling, etc.)
        pass


class ScenarioGeneratorAgentInterface(AIAgent):
    """
    Interface for AI agents that generate scenarios.
    
    Implements: generate_scenario, generate_stores, generate_npcs, generate_items
    """
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentRole.SCENARIO_GENERATOR)
    
    @abstractmethod
    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        """
        Handle scenario generation requests.
        
        Supported actions:
        - "generate_scenario": Create full scenario instance
        - "generate_stores": Create stores for scenario
        - "generate_npcs": Create NPCs for scenario
        - "generate_items": Create items and inventory
        - "generate_target_item": Select the objective item
        - "generate_story": Create narrative/environmental text
        """
        pass


class NPCAdminAgentInterface(AIAgent):
    """
    Interface for AI agents that manage NPCs.
    
    Implements: npc_decision, npc_perception, npc_interaction
    
    This agent stays connected and responds whenever:
    - A player interacts with an NPC
    - An NPC needs to make a decision
    - An NPC needs to perceive the world
    """
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentRole.NPC_ADMIN)
    
    @abstractmethod
    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        """
        Handle NPC-related requests.
        
        Supported actions:
        - "npc_decision": NPC needs to decide action/response
        - "npc_perception": NPC perceives world state
        - "npc_interaction": Player interacts with NPC
        - "npc_mood_update": Update NPC emotional state
        - "npc_relationship": Manage NPC relationship with player
        """
        pass


class GameMasterAgentInterface(AIAgent):
    """
    Interface for AI agents that orchestrate gameplay.
    
    Implements: evaluate_action, resolve_conflict, generate_feedback
    """
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentRole.GAME_MASTER)
    
    @abstractmethod
    async def handle_request(self, request: AIAgentRequest) -> AIAgentResponse:
        """
        Handle game orchestration requests.
        
        Supported actions:
        - "evaluate_action": Determine if action is valid
        - "resolve_conflict": Handle conflicts between agents
        - "generate_feedback": Create feedback for player
        """
        pass
