"""
Game Engine - The Orchestrator

Manages the main simulation loop, handles agent interactions,
coordinates state updates, and manages turn progression.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
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
    
    def __init__(self, tick_rate: float = 1.0):
        self.running = False
        self.turn = 0
        self.agents: Dict[str, Any] = {}
        self.tick_rate = tick_rate  # Seconds per tick
        self.loop_task: Optional[asyncio.Task] = None
        self.state_callback: Optional[Callable] = None
        
    def set_state_callback(self, callback: Callable):
        """Set callback to broadcast state updates"""
        self.state_callback = callback
        
    async def start(self):
        """Start the game engine loop"""
        if self.running:
            return
            
        self.running = True
        print("[Engine] Starting game engine loop...")
        self.loop_task = asyncio.create_task(self._run_loop())
        
    async def stop(self):
        """Stop the game engine loop"""
        self.running = False
        if self.loop_task:
            await self.loop_task
        print("[Engine] Stopped game engine")
        
    async def _run_loop(self):
        """Internal game loop"""
        try:
            while self.running:
                await asyncio.sleep(self.tick_rate)
                await self.tick()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Engine] Error in game loop: {e}")
        
    async def tick(self):
        """
        Execute one game loop iteration
        
        Called at regular intervals determined by tick_rate
        """
        self.turn += 1
        
        # Process actions for all agents
        for agent_id, agent in list(self.agents.items()):
            try:
                await self.process_agent_turn(agent_id, agent)
            except Exception as e:
                print(f"[Engine] Error processing agent {agent_id}: {e}")
        
        # Broadcast updated state to clients
        if self.state_callback:
            await self.state_callback()
            
        print(f"[Engine] Tick {self.turn} - {len(self.agents)} agents")
        
    async def process_agent_turn(self, agent_id: str, agent):
        """
        Process one agent's turn
        
        Args:
            agent_id: Agent identifier
            agent: Agent instance
        """
        # Get agent's current perception
        from .state import GameState
        
        # For now, agents just idle
        # This will be replaced with LLM decision-making
        action = {
            'type': 'idle',
            'agent_id': agent_id
        }
        
        await self.process_action(agent_id, action)
        
    async def process_action(self, agent_id: str, action: Dict[str, Any]):
        """
        Process an action from an agent
        
        Args:
            agent_id: The ID of the agent performing the action
            action: The action data like {'type': 'move', 'direction': 'forward'}
        """
        if agent_id not in self.agents:
            return
            
        print(f"[Engine] {agent_id} action: {action['type']}")
        
        # Action processing will be implemented in a future update
        # - Validate movement
        # - Check collisions
        # - Update entity position
        
    def register_agent(self, agent_id: str, agent):
        """Register an agent with the engine"""
        self.agents[agent_id] = agent
        print(f"[Engine] Registered agent: {agent_id}")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the engine"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"[Engine] Unregistered agent: {agent_id}")
