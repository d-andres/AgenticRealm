"""
AI Agents - External AI models connected to manage different aspects of AgenticRealm.

This module provides the framework for connecting AI agents (OpenAI, Anthropic, etc.)
that actively manage parts of the system:

- ScenarioGeneratorAgent: Generates unique scenarios, placements, rules
- NPCAdminAgent: Manages NPC personas, behaviors, and responses to player interactions
- Custom Agents: Add your own by subclassing AIAgent in interfaces.py

Provider implementations:
- openai_agents.py    → OpenAIScenarioGeneratorAgent, OpenAINPCAdminAgent
- anthropic_agents.py → AnthropicScenarioGeneratorAgent, AnthropicNPCAdminAgent

AI agents stay connected and respond to events in real-time.
"""

from .interfaces import AIAgent, AIAgentRequest, AIAgentResponse
from .agent_pool import AgentPool
from .openai_agents import OpenAIScenarioGeneratorAgent, OpenAINPCAdminAgent
from .anthropic_agents import AnthropicScenarioGeneratorAgent, AnthropicNPCAdminAgent

__all__ = [
    "AIAgent",
    "AIAgentRequest",
    "AIAgentResponse",
    "AgentPool",
    "OpenAIScenarioGeneratorAgent",
    "OpenAINPCAdminAgent",
    "AnthropicScenarioGeneratorAgent",
    "AnthropicNPCAdminAgent",
]
