"""
Judge - Environment & Physics Logic

Handles:
- Environment rules and physics
- Trap mechanics
- Collision detection
- Win/lose conditions
- Interaction validation
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class Trap:
    """Trap definition"""
    id: str
    x: float
    y: float
    radius: float  # Detection radius
    damage: int
    active: bool = True

class Judge:
    """
    Enforces world rules and environment mechanics
    
    Acts as the impartial arbiter of what is and isn't allowed
    in the game world. Validates actions against physics and rules.
    """
    
    def __init__(self):
        self.traps: Dict[str, Trap] = {}
        self.gravity = 9.8
        self.friction = 0.1
        
    def validate_movement(self, from_pos: Tuple[float, float], to_pos: Tuple[float, float], 
                         world_bounds: Dict[str, float]) -> Tuple[bool, str]:
        """
        Validate if movement is allowed
        
        Args:
            from_pos: Starting position (x, y)
            to_pos: Target position (x, y)
            world_bounds: World size limits
            
        Returns:
            (is_valid, reason)
        """
        x, y = to_pos
        
        # Check world bounds
        if x < 0 or x > world_bounds.get("width", 800):
            return False, "Out of bounds (x)"
        if y < 0 or y > world_bounds.get("height", 600):
            return False, "Out of bounds (y)"
            
        return True, "Valid movement"
        
    def check_collisions(self, entity_id: str, pos: Tuple[float, float], 
                        radius: float, all_entities: Dict[str, Any]) -> list:
        """
        Check for collisions with other entities and traps
        
        Returns:
            List of collision events
        """
        collisions = []
        x, y = pos
        
        # Check trap collisions
        for trap in self.traps.values():
            distance = ((x - trap.x)**2 + (y - trap.y)**2)**0.5
            if distance < (radius + trap.radius):
                collisions.append({
                    "type": "trap",
                    "trap_id": trap.id,
                    "damage": trap.damage
                })
                
        return collisions
        
    def add_trap(self, trap: Trap):
        """Add a trap to the world"""
        self.traps[trap.id] = trap
        print(f"[Judge] Added trap: {trap.id} at ({trap.x}, {trap.y})")
        
    def remove_trap(self, trap_id: str):
        """Remove a trap from the world"""
        if trap_id in self.traps:
            del self.traps[trap_id]
            print(f"[Judge] Removed trap: {trap_id}")
            
    def check_win_condition(self, agent_id: str, game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if an agent has won
        
        Returns:
            (has_won, reason)
        """
        # TODO: Define win conditions based on scenario
        return False, "Game in progress"
        
    def check_lose_condition(self, agent_id: str, game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if an agent has lost
        
        Returns:
            (has_lost, reason)
        """
        # TODO: Define lose conditions
        return False, "Game in progress"
