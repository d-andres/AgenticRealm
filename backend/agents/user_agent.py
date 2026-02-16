"""
User Agent - Player AI Logic

Handles the AI logic for user-designed agents.
Processes user-defined behaviors, decision-making, and interactions.
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseAgentLogic(ABC):
    """Base class for agent decision logic"""
    
    @abstractmethod
    def decide_action(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a decision based on the current perception
        
        Args:
            perception: Current game state information visible to agent
            
        Returns:
            Action to perform
        """
        pass

class UserAgent:
    """
    Represents a user-designed AI agent
    
    Contains the user's custom logic for decision-making.
    Can be powered by LLM, script-based, or ML model.
    """
    
    def __init__(self, agent_id: str, logic: BaseAgentLogic):
        self.agent_id = agent_id
        self.logic = logic
        self.action_history: List[Dict[str, Any]] = []
        self.perception_history: List[Dict[str, Any]] = []
        
    async def perceive(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process game state into agent's perception
        
        Filters and formats world state for the agent to process
        """
        perception = {
            "turn": game_state.get("turn", 0),
            "entities": game_state.get("entities", {}),
            "visible_range": 300  # Agent's vision range
        }
        self.perception_history.append(perception)
        return perception
        
    async def act(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide and return an action based on perception
        
        Args:
            perception: Filtered game state
            
        Returns:
            Action to perform
        """
        action = self.logic.decide_action(perception)
        self.action_history.append(action)
        return action
        
    def get_history(self, limit: int = 10) -> Dict[str, List]:
        """Get recent action and perception history"""
        return {
            "actions": self.action_history[-limit:],
            "perceptions": self.perception_history[-limit:]
        }


class LLMAgentLogic(BaseAgentLogic):
    """
    Agent logic powered by an LLM (GPT, Claude, Gemini, etc.)
    
    Sends game perception to LLM and executes returned actions.
    """
    
    def __init__(self, llm_provider: str, model: str, system_prompt: str = ""):
        self.llm_provider = llm_provider  # 'openai', 'anthropic', 'google', etc.
        self.model = model
        self.system_prompt = system_prompt
        
    def decide_action(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query LLM for action decision
        
        TODO: Implement LLM integration
        """
        # Placeholder - will integrate with LLM provider
        return {
            "type": "move",
            "direction": "forward"
        }


class ScriptAgentLogic(BaseAgentLogic):
    """
    Agent logic based on user-written Python scripts
    """
    
    def __init__(self, script_code: str):
        self.script_code = script_code
        self.namespace = {}
        # TODO: Safely execute and validate script
        
    def decide_action(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Execute script logic"""
        # Execute script with perception as input
        return {
            "type": "move",
            "direction": "forward"
        }
