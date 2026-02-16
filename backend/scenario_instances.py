"""
Scenario Instances Manager

Allows hosting always-on scenario instances (running worlds) that agents can join.
Each instance holds a `GameState` and a list of current players.
"""
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from core.state import GameState, Entity
from scenarios import ScenarioManager
import db
import json


class ScenarioInstance:
    def __init__(self, scenario_id: str):
        self.instance_id = str(uuid.uuid4())
        self.scenario_id = scenario_id
        self.scenario = ScenarioManager.get_scenario(scenario_id)
        self.state = GameState()
        self.players: List[str] = []
        self.created_at = datetime.now()
        self.started = False
        self.active = True
        if self.scenario:
            self._setup_world()
        # Persist initial snapshot
        try:
            db.save_instance_dict(self.to_dict())
        except Exception:
            pass

    def _setup_world(self):
        # Add static entities like traps and NPCs based on scenario
        for trap in (self.scenario.traps or []):
            trap_entity = Entity(
                id=trap['id'],
                type='trap',
                x=trap['x'],
                y=trap['y'],
                properties={'damage': trap['damage'], 'radius': trap['radius']}
            )
            self.state.add_entity(trap_entity)

    def add_player_entity(self, agent_id: str):
        # Place player at starting position
        if agent_id in self.state.entities:
            return
        player = Entity(
            id=agent_id,
            type='agent',
            x=self.scenario.starting_position[0],
            y=self.scenario.starting_position[1],
            properties={'health': 100, 'score': 0}
        )
        self.state.add_entity(player)
        self.players.append(agent_id)
        # Persist update
        try:
            db.save_instance_dict(self.to_dict())
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            'instance_id': self.instance_id,
            'scenario_id': self.scenario_id,
            'state': self.state.to_dict(),
            'players': self.players,
            'created_at': self.created_at.isoformat(),
            'active': getattr(self, 'active', True)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        inst = object.__new__(cls)
        inst.instance_id = data.get('instance_id')
        inst.scenario_id = data.get('scenario_id')
        inst.scenario = ScenarioManager.get_scenario(inst.scenario_id)
        inst.state = GameState.from_dict(data.get('state', {}))
        inst.players = data.get('players', [])
        inst.created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else datetime.now()
        inst.started = False
        inst.active = data.get('active', True)
        return inst


class ScenarioInstanceManager:
    def __init__(self):
        self.instances: Dict[str, ScenarioInstance] = {}

    def create_instance(self, scenario_id: str) -> ScenarioInstance:
        inst = ScenarioInstance(scenario_id)
        self.instances[inst.instance_id] = inst
        return inst

    def list_instances(self) -> List[ScenarioInstance]:
        return list(self.instances.values())

    def get_instance(self, instance_id: str) -> Optional[ScenarioInstance]:
        inst = self.instances.get(instance_id)
        if inst:
            return inst

        # Try to load from persistent storage
        try:
            data = db.load_instance_dict(instance_id)
            if data:
                inst = ScenarioInstance.from_dict(data)
                self.instances[inst.instance_id] = inst
                return inst
        except Exception:
            pass

        return None

    def stop_instance(self, instance_id: str) -> bool:
        inst = self.instances.get(instance_id)
        if not inst:
            return False
        inst.active = False
        try:
            db.save_instance_dict(inst.to_dict())
            db.mark_instance_inactive(instance_id)
        except Exception:
            pass
        return True

    def delete_instance(self, instance_id: str) -> bool:
        # Remove from memory and DB
        if instance_id in self.instances:
            del self.instances[instance_id]
        try:
            db.delete_instance(instance_id)
        except Exception:
            pass
        return True


# Global manager
scenario_instance_manager = ScenarioInstanceManager()

# Load persisted instances on startup
try:
    db.init_db()
    for d in db.list_instance_dicts(active_only=True):
        inst = ScenarioInstance.from_dict(d)
        scenario_instance_manager.instances[inst.instance_id] = inst
except Exception:
    pass
