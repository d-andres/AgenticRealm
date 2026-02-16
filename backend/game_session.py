"""
Game session management

Handles active game sessions and their state
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import uuid
from core.state import GameState, Entity
from scenarios import ScenarioManager

class GameSession:
    """A game session instance

    Can be attached to an existing scenario GameState (for running scenario instances)
    by passing `existing_state` and `instance_id`. If `existing_state` is None, a
    fresh scenario state is created (legacy behavior).
    """
    
    def __init__(self, game_id: str, scenario_id: str, agent_id: str, existing_state=None, instance_id: str = None):
        self.game_id = game_id
        self.scenario_id = scenario_id
        self.agent_id = agent_id
        self.status = "started"
        self.turn = 0
        # If attaching to an existing scenario instance, reuse its GameState
        self.state = existing_state if existing_state is not None else GameState()
        self.actions_taken = []
        self.created_at = datetime.now()
        self.completed_at = Optional[datetime]
        self.instance_id = instance_id
        
        # Load scenario and only setup static scenario entities if we created the state
        self.scenario = ScenarioManager.get_scenario(scenario_id)
        if self.scenario and existing_state is None:
            self._setup_scenario()
        elif self.scenario and existing_state is not None:
            # Ensure player entity is added to existing state
            if self.agent_id not in self.state.entities:
                player = Entity(
                    id=self.agent_id,
                    type='agent',
                    x=self.scenario.starting_position[0],
                    y=self.scenario.starting_position[1],
                    properties={'health': 100, 'score': 0}
                )
                self.state.add_entity(player)
    
    def _setup_scenario(self):
        """Initialize the scenario environment"""
        # Add player entity
        player = Entity(
            id=self.agent_id,
            type='agent',
            x=self.scenario.starting_position[0],
            y=self.scenario.starting_position[1],
            properties={'health': 100, 'score': 0}
        )
        self.state.add_entity(player)
        
        # Add traps
        for trap in self.scenario.traps:
            trap_entity = Entity(
                id=trap['id'],
                type='trap',
                x=trap['x'],
                y=trap['y'],
                properties={'damage': trap['damage'], 'radius': trap['radius']}
            )
            self.state.add_entity(trap_entity)
    
    def process_action(self, action: str, params: Dict) -> Tuple[bool, str, Dict]:
        """
        Process an agent action
        
        Returns: (success, message, state_update)
        """
        if self.status != "in_progress":
            return False, "Game is not in progress", {}
        
        if self.turn >= self.scenario.max_turns:
            self.status = "completed"
            return False, "Maximum turns reached", {}
        
        try:
            self.turn += 1
            self.actions_taken.append({
                'turn': self.turn,
                'action': action,
                'params': params
            })

            # If caller provided a condensed prompt summary, record it to the global feed
            prompt_summary = params.get('prompt_summary') if isinstance(params, dict) else None
            if prompt_summary:
                try:
                    from feed_store import feed_store
                    feed_store.log({
                        'timestamp': datetime.now().isoformat(),
                        'game_id': self.game_id,
                        'agent_id': self.agent_id,
                        'turn': self.turn,
                        'summary': prompt_summary
                    })
                except Exception:
                    # non-fatal: continue even if feed logging fails
                    pass
            
            if action == 'move':
                success, message, update = self._handle_move(params)
            elif action == 'observe':
                success, message, update = self._handle_observe(params)
            else:
                return False, f"Unknown action: {action}", {}

            # Build compact stats for this action
            agent = self.state.entities.get(self.agent_id)
            stats = {
                'actions_taken': len(self.actions_taken),
                'health': agent.properties.get('health') if agent else None,
                'score': agent.properties.get('score') if agent else None,
                'turn': self.turn
            }

            # Attach stats to the state update
            if isinstance(update, dict):
                update.setdefault('stats', {}).update(stats)
            else:
                update = {'stats': stats}

            return success, message, update
                
        except Exception as e:
            return False, f"Error processing action: {str(e)}", {}
    
    def _handle_move(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Handle movement action"""
        direction = params.get('direction')
        valid_directions = ['up', 'down', 'left', 'right']
        
        if direction not in valid_directions:
            return False, f"Invalid direction: {direction}", {}
        
        # Get agent current position
        agent = self.state.entities.get(self.agent_id)
        if not agent:
            return False, "Agent not found", {}
        
        old_x, old_y = agent.x, agent.y
        
        # Calculate new position (move 10 units)
        move_distance = 10
        new_x, new_y = old_x, old_y
        
        if direction == 'up':
            new_y -= move_distance
        elif direction == 'down':
            new_y += move_distance
        elif direction == 'left':
            new_x -= move_distance
        elif direction == 'right':
            new_x += move_distance
        
        # Check bounds
        if new_x < 0 or new_x > self.scenario.world_width or \
           new_y < 0 or new_y > self.scenario.world_height:
            return False, "Out of bounds", {}
        
        # Check for trap collisions
        for trap_id, trap in self.state.entities.items():
            if trap.type != 'trap':
                continue
            
            distance = ((new_x - trap.x)**2 + (new_y - trap.y)**2)**0.5
            if distance < trap.properties['radius']:
                # Hit a trap
                agent.properties['health'] -= trap.properties['damage']
                self.state.log_event('trap_hit', {'trap_id': trap_id, 'damage': trap.properties['damage']})
                
                if agent.properties['health'] <= 0:
                    self.status = "failed"
                    return False, "Trap hit! Game over.", {}
                
                return False, f"Hit a trap! Health: {agent.properties['health']}", {}
        
        # Check for exit
        distance_to_exit = ((new_x - self.scenario.exit_position[0])**2 + 
                           (new_y - self.scenario.exit_position[1])**2)**0.5
        
        if distance_to_exit < 20:
            agent.x = new_x
            agent.y = new_y
            self.status = "completed"
            self.completed_at = datetime.now()
            score = 100 - (self.turn * 0.5)  # Score based on efficiency
            agent.properties['score'] = max(0, score)
            return True, "Exit reached! Success!", {}
        
        # Valid move
        agent.x = new_x
        agent.y = new_y
        
        return True, f"Moved {direction}", {
            'position': {'x': agent.x, 'y': agent.y},
            'turn': self.turn
        }
    
    def _handle_observe(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Handle observation action"""
        # Agent can observe nearby entities
        agent = self.state.entities.get(self.agent_id)
        if not agent:
            return False, "Agent not found", {}
        
        observation_radius = 100
        nearby = []
        
        for entity_id, entity in self.state.entities.items():
            if entity_id == self.agent_id:
                continue
            
            distance = ((entity.x - agent.x)**2 + (entity.y - agent.y)**2)**0.5
            if distance < observation_radius:
                nearby.append({
                    'id': entity_id,
                    'type': entity.type,
                    'distance': distance,
                    'position': {'x': entity.x, 'y': entity.y}
                })
        
        return True, f"Observed {len(nearby)} entities", {
            'entities': nearby,
            'turn': self.turn
        }
    
    def get_state(self) -> Dict:
        """Get current game state"""
        return {
            'game_id': self.game_id,
            'scenario_id': self.scenario_id,
            'agent_id': self.agent_id,
            'status': self.status,
            'turn': self.turn,
            'max_turns': self.scenario.max_turns,
            'state': self.state.to_dict(),
            'scenario_info': {
                'name': self.scenario.name,
                'world_width': self.scenario.world_width,
                'world_height': self.scenario.world_height,
                'exit_position': self.scenario.exit_position
            }
        }
    
    def get_result(self) -> Dict:
        """Get game result"""
        agent = self.state.entities.get(self.agent_id)
        success = self.status == "completed"
        score = agent.properties.get('score', 0) if agent else 0
        
        return {
            'game_id': self.game_id,
            'scenario_id': self.scenario_id,
            'agent_id': self.agent_id,
            'success': success,
            'turn': self.turn,
            'score': score,
            'reason': 'Successfully completed scenario' if success else 'Failed to complete',
            'feedback': self._generate_feedback(success, score),
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def _generate_feedback(self, success: bool, score: float) -> str:
        """Generate feedback for the agent"""
        if success:
            if score > 80:
                return "Excellent! Your agent solved this efficiently."
            elif score > 60:
                return "Good! Your agent completed the scenario."
            else:
                return "Your agent completed, but there might be room for optimization."
        else:
            if self.status == "failed":
                return "Your agent hit a trap. Consider improving observation or planning."
            elif self.turn >= self.scenario.max_turns:
                return "Ran out of turns. Your agent needs better decision-making."
            else:
                return "Your agent was unable to complete the scenario."

class GameSessionManager:
    """Manages active game sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
    
    def create_session(self, scenario_id: str, agent_id: str, existing_state=None, instance_id: str = None) -> GameSession:
        """Create a new game session. If `existing_state` is provided the session will
        attach to that state (used when joining a running scenario instance)."""
        game_id = str(uuid.uuid4())
        session = GameSession(game_id, scenario_id, agent_id, existing_state=existing_state, instance_id=instance_id)
        self.sessions[game_id] = session
        print(f"[GameSessionManager] Created session {game_id}")
        return session
    
    def get_session(self, game_id: str) -> Optional[GameSession]:
        """Get a session by ID"""
        return self.sessions.get(game_id)
    
    def start_session(self, game_id: str) -> bool:
        """Start a session"""
        session = self.sessions.get(game_id)
        if session:
            session.status = "in_progress"
            return True
        return False
    
    def end_session(self, game_id: str) -> bool:
        """End a session"""
        session = self.sessions.get(game_id)
        if session:
            session.status = "completed"
            session.completed_at = datetime.now()
            return True
        return False

# Global session manager
session_manager = GameSessionManager()
