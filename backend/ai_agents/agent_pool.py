"""
Agent Pool - Manages connected AI agents.

The agent pool handles registration, discovery, and routing of requests to appropriate agents.
Each AI agent connects and registers, then becomes available for requests.
"""

from typing import Dict, Optional, List
import asyncio
from .interfaces import AIAgent, AIAgentRequest, AIAgentResponse, AgentRole


class AgentPool:
    """
    Manages collection of connected AI agents.
    
    Features:
    - Agent registration and discovery
    - Request routing to appropriate agents
    - Connection health tracking
    - Failover handling
    
    Usage:
        pool = AgentPool()
        
        # Register agents
        await pool.register_agent(scenario_gen_agent)
        await pool.register_agent(npc_admin_agent)
        
        # Route requests
        response = await pool.request(
            role=AgentRole.NPC_ADMIN,
            action="npc_decision",
            context={...}
        )
    """
    
    def __init__(self):
        # agents[role] = [agent1, agent2, ...]
        # Supports multiple agents per role for load balancing
        self.agents: Dict[AgentRole, List[AIAgent]] = {}
        self.current_agent_index: Dict[AgentRole, int] = {}
        self.request_counter = 0
        self.agent_lock = asyncio.Lock()
    
    async def register_agent(self, agent: AIAgent) -> bool:
        """
        Register an AI agent with the pool.
        
        Args:
            agent: The AI agent to register
            
        Returns:
            True if registration successful
        """
        async with self.agent_lock:
            # Initialize agent role in pool if needed
            if agent.role not in self.agents:
                self.agents[agent.role] = []
                self.current_agent_index[agent.role] = 0
            
            # Connect agent
            try:
                connected = await agent.connect()
                if not connected:
                    print(f"Failed to connect agent {agent.agent_name}")
                    return False
                
                # Add to pool
                self.agents[agent.role].append(agent)
                print(f"✓ Registered {agent.role.value} agent: {agent.agent_name}")
                return True
            
            except Exception as e:
                print(f"Error registering agent {agent.agent_name}: {e}")
                return False
    
    async def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an AI agent from the pool.
        
        Args:
            agent_name: Name of agent to unregister
            
        Returns:
            True if unregistration successful
        """
        async with self.agent_lock:
            for role, agents in self.agents.items():
                for i, agent in enumerate(agents):
                    if agent.agent_name == agent_name:
                        try:
                            await agent.disconnect()
                            agents.pop(i)
                            print(f"✓ Unregistered {role.value} agent: {agent_name}")
                            return True
                        except Exception as e:
                            print(f"Error unregistering agent {agent_name}: {e}")
                            return False
        return False
    
    async def request(
        self,
        role: AgentRole,
        action: str,
        context: Dict = None,
        priority: str = "normal"
    ) -> Optional[AIAgentResponse]:
        """
        Send a request to an agent with the given role.
        
        If multiple agents have this role, uses round-robin load balancing.
        
        Args:
            role: Role of agent needed (SCENARIO_GENERATOR, NPC_ADMIN, etc.)
            action: Action for agent to perform
            context: Event context/data
            priority: "normal", "high", or "critical"
            
        Returns:
            AIAgentResponse from the agent, or None if no agent available
        """
        if context is None:
            context = {}
        
        async with self.agent_lock:
            # Check if agents of this role exist
            if role not in self.agents or len(self.agents[role]) == 0:
                print(f"No agents available for role {role.value}")
                return None
            
            # Get next agent using round-robin
            agents = self.agents[role]
            agent_index = self.current_agent_index[role]
            agent = agents[agent_index]
            
            # Advance index for next call
            self.current_agent_index[role] = (agent_index + 1) % len(agents)
        
        # Create request
        self.request_counter += 1
        request = AIAgentRequest(
            agent_role=role,
            action=action,
            context=context,
            request_id=f"req_{self.request_counter}",
            priority=priority
        )
        
        # Send to agent
        try:
            response = await agent.handle_request(request)
            return response
        except Exception as e:
            print(f"Error handling request in agent {agent.agent_name}: {e}")
            return None
    
    async def broadcast(
        self,
        role: AgentRole,
        action: str,
        context: Dict = None
    ) -> List[AIAgentResponse]:
        """
        Send request to ALL agents of a given role.
        
        Useful for updates that need to propagate to all agents.
        
        Args:
            role: Role of agents to request
            action: Action for agents to perform
            context: Event context/data
            
        Returns:
            List of responses from all agents
        """
        if context is None:
            context = {}
        
        async with self.agent_lock:
            if role not in self.agents:
                return []
            agents = self.agents[role].copy()
        
        # Send request to all agents in parallel
        tasks = []
        for agent in agents:
            self.request_counter += 1
            request = AIAgentRequest(
                agent_role=role,
                action=action,
                context=context,
                request_id=f"req_{self.request_counter}",
                priority="normal"
            )
            tasks.append(agent.handle_request(request))
        
        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in responses if isinstance(r, AIAgentResponse)]
    
    def get_agents_by_role(self, role: AgentRole) -> List[AIAgent]:
        """Get all agents with a specific role"""
        return self.agents.get(role, [])
    
    def get_all_agents(self) -> List[tuple]:
        """Get all registered agents as (role, [agent_list]) tuples"""
        return [(role, agents) for role, agents in self.agents.items()]
    
    async def shutdown(self):
        """Disconnect all agents gracefully"""
        async with self.agent_lock:
            for role, agents in self.agents.items():
                for agent in agents:
                    try:
                        await agent.disconnect()
                    except Exception as e:
                        print(f"Error disconnecting agent {agent.agent_name}: {e}")
            self.agents.clear()
            self.current_agent_index.clear()


# Global agent pool instance
_agent_pool: Optional[AgentPool] = None


async def get_agent_pool() -> AgentPool:
    """Get or create the global agent pool"""
    global _agent_pool
    if _agent_pool is None:
        _agent_pool = AgentPool()
    return _agent_pool


async def shutdown_agent_pool():
    """Shutdown the global agent pool"""
    global _agent_pool
    if _agent_pool is not None:
        await _agent_pool.shutdown()
        _agent_pool = None
