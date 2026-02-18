"""
Game session management

Handles active game sessions and their state.
Sessions are intentionally thin — they know about world bounds and
entity state but do NOT hardcode what entities mean.  The entities
in GameState (stores, NPCs, items, hazards, exits, etc.) are defined
by the AI-generated scenario instance, not by this class.
"""

from typing import Any, Dict, List, Optional, Tuple
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
        self.state = existing_state if existing_state is not None else GameState()
        self.actions_taken: List[Dict] = []
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.instance_id = instance_id

        # Load the scenario TEMPLATE (constraints only — no hardcoded entities)
        self.scenario = ScenarioManager.get_template(scenario_id)
        if self.scenario and existing_state is None:
            self._setup_scenario()
        elif self.scenario and existing_state is not None:
            # Ensure player entity exists in the shared world state
            if self.agent_id not in self.state.entities:
                start = self.state.properties.get('starting_position', [50, 50])
                player = Entity(
                    id=self.agent_id,
                    type='agent',
                    x=start[0],
                    y=start[1],
                    properties={
                        'health': 100,
                        'score': 0,
                        'gold': getattr(self.scenario, 'starting_gold', 500),
                        'inventory': []
                    }
                )
                self.state.add_entity(player)
    
    def _setup_scenario(self):
        """Bootstrap world state from template constraints.

        The template defines bounds and metadata only.  Specific entities
        (NPCs, stores, items, hazards) are added by the AI ScenarioGenerator
        AFTER this call.  Only the player entity is created here so the agent
        can act immediately while generation completes asynchronously.
        """
        # Record world bounds in state properties
        self.state.properties.update({
            'world_width': self.scenario.world_width,
            'world_height': self.scenario.world_height,
            'scenario_id': self.scenario_id,
            'scenario_name': self.scenario.name,
            'max_turns': self.scenario.max_turns,
            'allowed_actions': [a.value for a in self.scenario.allowed_actions],
        })

        # Place the player entity; position may be overridden later by generator
        start = self.state.properties.get('starting_position', [50, 50])
        player = Entity(
            id=self.agent_id,
            type='agent',
            x=start[0],
            y=start[1],
            properties={
                'health': 100,
                'score': 0,
                'gold': self.scenario.starting_gold,
                'inventory': []
            }
        )
        self.state.add_entity(player)
    
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
                    from store.feed import feed_store
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
            elif action == 'talk':
                success, message, update = self._handle_talk(params)
            elif action == 'negotiate':
                success, message, update = self._handle_negotiate(params)
            elif action == 'buy':
                success, message, update = self._handle_buy(params)
            elif action == 'hire':
                success, message, update = self._handle_hire(params)
            elif action == 'steal':
                success, message, update = self._handle_steal(params)
            elif action == 'trade':
                success, message, update = self._handle_trade(params)
            elif action == 'interact':
                success, message, update = self._handle_interact(params)
            else:
                return False, f"Unknown action '{action}'. Allowed: {self.state.properties.get('allowed_actions', [])}", {}

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
        """Handle movement action.

        Checks world bounds from the template.  Any entity in the world with
        type 'hazard' will deal damage if the player moves into its radius.
        Any entity with type 'exit' will trigger a win condition.
        These types are defined by the AI generator, not hardcoded here.
        """
        direction = params.get('direction')
        valid_directions = ['up', 'down', 'left', 'right']
        if direction not in valid_directions:
            return False, f"Invalid direction: {direction}. Must be one of {valid_directions}", {}

        agent = self.state.entities.get(self.agent_id)
        if not agent:
            return False, "Agent entity not found in world state", {}

        move_distance = int(params.get('distance', 10))
        new_x, new_y = agent.x, agent.y

        if direction == 'up':
            new_y -= move_distance
        elif direction == 'down':
            new_y += move_distance
        elif direction == 'left':
            new_x -= move_distance
        elif direction == 'right':
            new_x += move_distance

        # Bounds check against template world size
        world_w = self.state.properties.get('world_width', self.scenario.world_width if self.scenario else 800)
        world_h = self.state.properties.get('world_height', self.scenario.world_height if self.scenario else 600)
        if new_x < 0 or new_x > world_w or new_y < 0 or new_y > world_h:
            return False, "Movement out of world bounds", {}

        # Generic proximity checks — entity types are AI-defined
        for eid, entity in self.state.entities.items():
            if eid == self.agent_id:
                continue
            dist = ((new_x - entity.x) ** 2 + (new_y - entity.y) ** 2) ** 0.5
            radius = entity.properties.get('radius', 15)

            if dist < radius:
                if entity.type == 'hazard':
                    damage = entity.properties.get('damage', 10)
                    agent.properties['health'] = agent.properties.get('health', 100) - damage
                    self.state.log_event('hazard_hit', {'entity_id': eid, 'damage': damage})
                    if agent.properties['health'] <= 0:
                        self.status = 'failed'
                        return False, f"Eliminated by hazard '{eid}'. Health reached 0.", {}
                    return False, f"Hit hazard '{eid}'! Health: {agent.properties['health']}", {}

                if entity.type == 'exit':
                    agent.x, agent.y = new_x, new_y
                    self.status = 'completed'
                    self.completed_at = datetime.now()
                    turns_used = self.turn
                    max_t = self.state.properties.get('max_turns', getattr(self.scenario, 'max_turns', 150))
                    score = max(0.0, 100.0 - (turns_used / max_t) * 50)
                    agent.properties['score'] = score
                    self.state.log_event('exit_reached', {'entity_id': eid, 'score': score})
                    return True, f"Exit reached via '{eid}'! Scenario complete.", {'score': score}

        agent.x, agent.y = new_x, new_y
        return True, f"Moved {direction} to ({new_x}, {new_y})", {
            'position': {'x': agent.x, 'y': agent.y}
        }
    
    def _handle_observe(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Return all nearby entities with their full public properties.

        The agent uses this to make decisions.  Entity types are AI-defined
        so we return them verbatim rather than filtering by known type names.
        """
        agent = self.state.entities.get(self.agent_id)
        if not agent:
            return False, "Agent entity not found", {}

        radius = int(params.get('radius', 150))
        nearby = []
        for eid, entity in self.state.entities.items():
            if eid == self.agent_id:
                continue
            dist = ((entity.x - agent.x) ** 2 + (entity.y - agent.y) ** 2) ** 0.5
            if dist <= radius:
                nearby.append({
                    'id': eid,
                    'type': entity.type,
                    'distance': round(dist, 1),
                    'position': {'x': entity.x, 'y': entity.y},
                    'properties': entity.properties,
                })

        nearby.sort(key=lambda e: e['distance'])
        return True, f"Observed {len(nearby)} entities within radius {radius}", {
            'entities': nearby,
            'agent_position': {'x': agent.x, 'y': agent.y},
        }

    # ------------------------------------------------------------------
    # Rich social / economic actions
    # All of these produce structured events and return observable results.
    # When an NPC_ADMIN AI agent is connected via AgentPool it will provide
    # the NPC response; until then a default neutral response is returned.
    # ------------------------------------------------------------------

    def _resolve_npc(self, params: Dict) -> Optional['Entity']:
        """Look up a target NPC/store entity from params, return None if not found."""
        entity_id = params.get('npc_id') or params.get('store_id') or params.get('entity_id')
        return self.state.entities.get(entity_id) if entity_id else None

    def _handle_talk(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Initiate a conversation with an NPC entity."""
        npc = self._resolve_npc(params)
        if not npc:
            return False, "Target entity not found. Provide 'npc_id'.", {}
        message = params.get('message', '')
        self.state.log_event('talk', {
            'agent_id': self.agent_id,
            'npc_id': npc.id,
            'message': message
        })
        # TODO: route to NPC_ADMIN AI agent via AgentPool for authentic response
        response = npc.properties.get('default_response',
            f"{npc.properties.get('name', npc.id)} acknowledges you.")
        return True, response, {'npc_id': npc.id, 'npc_response': response}

    def _handle_negotiate(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Attempt to haggle with a shopkeeper over an item price."""
        npc = self._resolve_npc(params)
        if not npc:
            return False, "Target store/NPC not found. Provide 'store_id' or 'npc_id'.", {}
        item_id = params.get('item_id')
        offered_price = params.get('offered_price')
        if item_id is None or offered_price is None:
            return False, "Provide 'item_id' and 'offered_price'.", {}
        self.state.log_event('negotiate', {
            'agent_id': self.agent_id,
            'npc_id': npc.id,
            'item_id': item_id,
            'offered_price': offered_price
        })
        # TODO: route to NPC_ADMIN AI agent for authentic acceptance logic
        multiplier = npc.properties.get('pricing_multiplier', 1.0)
        inventory = npc.properties.get('inventory', {})
        item = inventory.get(item_id)
        if not item:
            return False, f"Item '{item_id}' not found in {npc.id}'s inventory.", {}
        base = item.get('value', 100) * multiplier
        accepted = offered_price >= base * 0.8
        return accepted, (
            f"Offer accepted at {offered_price} gold." if accepted
            else f"Offer refused. Counter-price: {round(base, 0)} gold."
        ), {'accepted': accepted, 'item_id': item_id, 'counter_price': round(base, 0)}

    def _handle_buy(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Purchase an item from a store entity."""
        store = self._resolve_npc(params)
        if not store:
            return False, "Store not found. Provide 'store_id'.", {}
        item_id = params.get('item_id')
        if not item_id:
            return False, "Provide 'item_id'.", {}
        agent = self.state.entities.get(self.agent_id)
        inventory = store.properties.get('inventory', {})
        item = inventory.get(item_id)
        if not item:
            return False, f"Item '{item_id}' not in store inventory.", {}
        price = round(item.get('value', 100) * store.properties.get('pricing_multiplier', 1.0))
        gold = agent.properties.get('gold', 0)
        if gold < price:
            return False, f"Insufficient gold. Need {price}, have {gold}.", {}
        # Transfer item
        agent.properties['gold'] = gold - price
        agent_inv = agent.properties.setdefault('inventory', [])
        agent_inv.append({**item, 'item_id': item_id})
        del inventory[item_id]
        self.state.log_event('buy', {'agent_id': self.agent_id, 'store_id': store.id, 'item_id': item_id, 'price': price})
        # Check win condition: agent acquired the target item
        target = self.state.properties.get('target_item_id')
        if target and item_id == target:
            self.status = 'completed'
            self.completed_at = datetime.now()
            agent.properties['score'] = max(0.0, 100.0 - (self.turn / max(1, self.state.properties.get('max_turns', 150))) * 30)
        return True, f"Bought '{item.get('name', item_id)}' for {price} gold.", {
            'item': item, 'gold_remaining': agent.properties['gold']
        }

    def _handle_hire(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Hire an NPC to assist the agent."""
        npc = self._resolve_npc(params)
        if not npc:
            return False, "NPC not found. Provide 'npc_id'.", {}
        cost = npc.properties.get('hiring_cost')
        if cost is None:
            return False, f"'{npc.id}' is not available for hire.", {}
        agent = self.state.entities.get(self.agent_id)
        gold = agent.properties.get('gold', 0)
        if gold < cost:
            return False, f"Cannot afford. Hire cost: {cost}, have {gold}.", {}
        agent.properties['gold'] = gold - cost
        npc.properties['hired_by'] = self.agent_id
        self.state.log_event('hire', {'agent_id': self.agent_id, 'npc_id': npc.id, 'cost': cost})
        return True, f"Hired '{npc.properties.get('name', npc.id)}' for {cost} gold.", {
            'npc_id': npc.id, 'gold_remaining': agent.properties['gold']
        }

    def _handle_steal(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Attempt to steal an item from a store entity."""
        store = self._resolve_npc(params)
        if not store:
            return False, "Store not found. Provide 'store_id'.", {}
        item_id = params.get('item_id')
        if not item_id:
            return False, "Provide 'item_id'.", {}
        inventory = store.properties.get('inventory', {})
        item = inventory.get(item_id)
        if not item:
            return False, f"Item '{item_id}' not in store inventory.", {}
        # Success chance based on guard presence; NPC_ADMIN will refine this
        # TODO: route to NPC_ADMIN AI agent for authentic outcome resolution
        guards = [e for e in self.state.entities.values() if e.type == 'npc'
                  and e.properties.get('job') == 'guard'
                  and ((e.x - store.x) ** 2 + (e.y - store.y) ** 2) ** 0.5 < 100]
        success_chance = max(0.1, 0.7 - len(guards) * 0.2)
        import random
        success = random.random() < success_chance
        self.state.log_event('steal_attempt', {
            'agent_id': self.agent_id, 'store_id': store.id,
            'item_id': item_id, 'success': success, 'guards_nearby': len(guards)
        })
        if success:
            agent = self.state.entities.get(self.agent_id)
            agent.properties.setdefault('inventory', []).append({**item, 'item_id': item_id})
            del inventory[item_id]
            return True, f"Successfully stole '{item.get('name', item_id)}'.", {'item': item}
        penalty = 20
        agent = self.state.entities.get(self.agent_id)
        agent.properties['health'] = max(0, agent.properties.get('health', 100) - penalty)
        return False, f"Steal failed! Caught by guard. Health -{penalty}.", {
            'health': agent.properties['health']
        }

    def _handle_trade(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Propose a trade with an NPC."""
        npc = self._resolve_npc(params)
        if not npc:
            return False, "NPC not found. Provide 'npc_id'.", {}
        give_item_id = params.get('give_item_id')
        receive_item_id = params.get('receive_item_id')
        if not give_item_id or not receive_item_id:
            return False, "Provide 'give_item_id' and 'receive_item_id'.", {}
        agent = self.state.entities.get(self.agent_id)
        agent_inv = agent.properties.get('inventory', [])
        give_items = [i for i in agent_inv if i.get('item_id') == give_item_id]
        if not give_items:
            return False, f"You don't have item '{give_item_id}' to trade.", {}
        npc_inv = npc.properties.get('inventory', {})
        receive_item = npc_inv.get(receive_item_id)
        if not receive_item:
            return False, f"NPC doesn't have item '{receive_item_id}'.", {}
        # TODO: route to NPC_ADMIN AI agent for acceptance decision
        give_val = give_items[0].get('value', 0)
        recv_val = receive_item.get('value', 0)
        accepted = give_val >= recv_val * 0.8
        self.state.log_event('trade_proposal', {
            'agent_id': self.agent_id, 'npc_id': npc.id,
            'give_item_id': give_item_id, 'receive_item_id': receive_item_id, 'accepted': accepted
        })
        if accepted:
            agent_inv.remove(give_items[0])
            agent_inv.append({**receive_item, 'item_id': receive_item_id})
            del npc_inv[receive_item_id]
            npc_inv[give_item_id] = give_items[0]
            return True, f"Trade accepted! Gave '{give_item_id}', received '{receive_item_id}'.", {
                'gave': give_item_id, 'received': receive_item_id
            }
        return False, f"Trade refused. Your offer undervalues what you want.", {'accepted': False}

    def _handle_interact(self, params: Dict) -> Tuple[bool, str, Dict]:
        """Generic interaction fallback for AI-defined entity types."""
        entity_id = params.get('entity_id')
        if not entity_id:
            return False, "Provide 'entity_id'.", {}
        entity = self.state.entities.get(entity_id)
        if not entity:
            return False, f"Entity '{entity_id}' not found in world.", {}
        action_type = params.get('action_type', 'use')
        self.state.log_event('interact', {
            'agent_id': self.agent_id,
            'entity_id': entity_id,
            'entity_type': entity.type,
            'action_type': action_type,
            'extra_params': {k: v for k, v in params.items()
                             if k not in ('entity_id', 'action_type')}
        })
        return True, f"Interacted with '{entity_id}' ({entity.type}) via '{action_type}'.", {
            'entity_id': entity_id,
            'entity_type': entity.type,
            'properties': entity.properties
        }
    
    def get_state(self) -> Dict:
        """Get current game state"""
        max_turns = self.state.properties.get(
            'max_turns',
            getattr(self.scenario, 'max_turns', 150) if self.scenario else 150
        )
        world_w = self.state.properties.get(
            'world_width',
            getattr(self.scenario, 'world_width', 800) if self.scenario else 800
        )
        world_h = self.state.properties.get(
            'world_height',
            getattr(self.scenario, 'world_height', 600) if self.scenario else 600
        )
        return {
            'game_id': self.game_id,
            'scenario_id': self.scenario_id,
            'agent_id': self.agent_id,
            'status': self.status,
            'turn': self.turn,
            'max_turns': max_turns,
            'state': self.state,
            'scenario_info': {
                'name': self.scenario.name if self.scenario else self.scenario_id,
                'world_width': world_w,
                'world_height': world_h,
                'allowed_actions': self.state.properties.get('allowed_actions', []),
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
        """Generate contextual feedback for the agent."""
        if success:
            if score >= 80:
                return "Excellent! Your agent achieved the objective very efficiently."
            elif score >= 60:
                return "Good work. Your agent completed the scenario with room for improvement."
            else:
                return "Objective achieved, but efficiency was low. Consider a more direct strategy."
        else:
            if self.status == 'failed':
                return "Your agent was eliminated. Improve hazard avoidance or situational awareness."
            elif self.scenario and self.turn >= self.scenario.max_turns:
                return "Turn limit reached. Your agent needs faster decision-making or a clearer strategy."
            else:
                return "Scenario incomplete. Review the objectives and available actions."

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
