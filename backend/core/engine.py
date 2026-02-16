"""
Game Engine - The Orchestrator

Manages the main simulation loop, handles agent interactions,
coordinates state updates, and manages turn progression.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

class GameEngine:
    """
    Main orchestrator for the Agentic AI simulation.
    
    Manages:
    - Simulation loop
    - Agent actions and interactions
    - State transitions
    - Turn management
    """
    
    def __init__(self):
        self.running = False
        self.turn = 0
        self.agents = {}
        self.tick_rate = 1.0  # Seconds per tick
        
    async def start(self):
        """Start the game engine loop"""
        self.running = True
        print("[Engine] Starting game engine...")
        
    async def stop(self):
        """Stop the game engine loop"""
        self.running = False
        print("[Engine] Stopping game engine...")
        
    async def process_action(self, agent_id: str, action: Dict[str, Any]):
        """
        Process an action from an agent
        
        Args:
            agent_id: The ID of the agent performing the action
            action: The action data
        """
        print(f"[Engine] Processing action from {agent_id}: {action}")
        
    async def tick(self):
        """
        Execute one game loop iteration
        
        Called at regular intervals determined by tick_rate
        """
        self.turn += 1
        print(f"[Engine] Tick {self.turn} - {datetime.now()}")
        
    def register_agent(self, agent_id: str, agent):
        """Register an agent with the engine"""
        self.agents[agent_id] = agent
        print(f"[Engine] Registered agent: {agent_id}")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the engine"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"[Engine] Unregistered agent: {agent_id}")
