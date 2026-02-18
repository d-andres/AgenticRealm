"""
Agent store — in-memory registry for user agents.

Agents registered here represent the external AI agents that interact
with the game world via the REST API.  Not to be confused with:
  - `ai_agents/`  — LLM provider integrations (OpenAI, Anthropic)
  - `scenarios/`  — Generated NPC entities inside the game world
"""

from typing import Dict, Optional, List
from datetime import datetime
import uuid


class Agent:
    """Metadata record for a registered user agent."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        creator: str,
        model: str,
        system_prompt: str,
        skills: Dict,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.creator = creator
        self.model = model
        self.system_prompt = system_prompt
        self.skills = skills
        self.created_at = datetime.now()
        self.games_played = 0
        self.games_won = 0

    def to_dict(self):
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'creator': self.creator,
            'model': self.model,
            'system_prompt': self.system_prompt,
            'skills': self.skills,
            'created_at': self.created_at.isoformat(),
            'games_played': self.games_played,
            'games_won': self.games_won,
        }


class AgentStore:
    """In-memory store for registered user agents."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register(self, agent_data: Dict) -> Agent:
        """Register a new agent and return it."""
        agent_id = str(uuid.uuid4())
        agent = Agent(
            agent_id=agent_id,
            name=agent_data['name'],
            description=agent_data['description'],
            creator=agent_data['creator'],
            model=agent_data['model'],
            system_prompt=agent_data['system_prompt'],
            skills=agent_data['skills'],
        )
        self.agents[agent_id] = agent
        print(f"[AgentStore] Registered agent: {agent.name} ({agent_id})")
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:
        return list(self.agents.values())

    def agent_exists(self, agent_id: str) -> bool:
        return agent_id in self.agents

    def update_game_stats(self, agent_id: str, success: bool):
        """Increment games_played; increment games_won if success."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.games_played += 1
            if success:
                agent.games_won += 1


# Global singleton
agent_store = AgentStore()
