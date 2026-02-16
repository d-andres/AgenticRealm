"""
Agent Registrar - Skill Gate & Character Creation

Handles:
- Agent registration and validation
- Character creation
- Skill assessment and gating
- Permission management
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Agent:
    """Agent character"""
    id: str
    name: str
    skills: Dict[str, int]  # skill_name -> level
    inventory: list = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

class AgentRegistrar:
    """
    Manages agent registration, character creation, and skill validation
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.required_skills = {
            "reasoning": 1,
            "observation": 1
        }
        
    def register_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Agent]:
        """
        Register a new agent
        
        Args:
            agent_id: Unique agent identifier
            agent_data: {
                "name": str,
                "skills": {"skill_name": level, ...}
            }
            
        Returns:
            Agent instance if successful, None otherwise
        """
        # Validate required skills
        if not self.validate_skills(agent_data.get("skills", {})):
            print(f"[Registrar] Agent {agent_id} failed skill validation")
            return None
            
        agent = Agent(
            id=agent_id,
            name=agent_data.get("name", f"Agent_{agent_id}"),
            skills=agent_data.get("skills", {})
        )
        
        self.agents[agent_id] = agent
        print(f"[Registrar] Registered agent: {agent.name} ({agent_id})")
        return agent
        
    def validate_skills(self, skills: Dict[str, int]) -> bool:
        """Validate that agent has required skills"""
        for skill, min_level in self.required_skills.items():
            if skills.get(skill, 0) < min_level:
                return False
        return True
        
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
        
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"[Registrar] Unregistered agent: {agent_id}")
            return True
        return False
