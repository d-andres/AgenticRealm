"""
Game State - World State Management

Maintains the authoritative state of the game world including:
- Entity positions and properties
- Environment state
- Turn counter and game progress
- Event log
"""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class Entity:
    """Base entity in the game world"""
    id: str
    type: str  # 'agent', 'npc', 'obstacle', etc.
    x: float
    y: float
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

class GameState:
    """
    Authoritative game state
    
    Maintains:
    - World entities (agents, NPCs, obstacles)
    - Environment properties
    - Event history
    - Turn information
    """
    
    def __init__(self):
        self.turn = 0
        self.entities: Dict[str, Entity] = {}
        self.events: List[Dict[str, Any]] = []
        self.properties: Dict[str, Any] = {
            "world_width": 800,
            "world_height": 600,
            "created_at": datetime.now().isoformat()
        }
        
    def add_entity(self, entity: Entity):
        """Add an entity to the world"""
        self.entities[entity.id] = entity
        self.log_event("entity_added", {"entity_id": entity.id, "type": entity.type})
        
    def remove_entity(self, entity_id: str):
        """Remove an entity from the world"""
        if entity_id in self.entities:
            del self.entities[entity_id]
            self.log_event("entity_removed", {"entity_id": entity_id})
            
    def update_entity(self, entity_id: str, updates: Dict[str, Any]):
        """Update an entity's properties"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    entity.properties[key] = value
            self.log_event("entity_updated", {"entity_id": entity_id, "updates": updates})
            
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event to the event history"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "turn": self.turn,
            "type": event_type,
            "data": data
        }
        self.events.append(event)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for transmission"""
        return {
            "turn": self.turn,
            "entities": {
                entity_id: {
                    "id": entity.id,
                    "type": entity.type,
                    "x": entity.x,
                    "y": entity.y,
                    "properties": entity.properties
                }
                for entity_id, entity in self.entities.items()
            },
            "properties": self.properties,
            "recent_events": self.events[-10:]  # Last 10 events
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Reconstruct a GameState from a dict (used for persistence)."""
        gs = cls()
        gs.turn = data.get('turn', 0)
        gs.properties = data.get('properties', gs.properties)
        gs.events = data.get('events', data.get('recent_events', []))

        entities = data.get('entities', {})
        gs.entities = {}
        for eid, ed in entities.items():
            ent = Entity(
                id=ed.get('id', eid),
                type=ed.get('type', 'unknown'),
                x=ed.get('x', 0),
                y=ed.get('y', 0),
                properties=ed.get('properties', {})
            )
            gs.entities[ent.id] = ent

        return gs
