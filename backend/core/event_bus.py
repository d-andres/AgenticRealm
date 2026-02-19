"""
Event Bus — Non-blocking pub/sub for simulation events.

Design:
  - GameState.log_event() publishes events here (fire-and-forget, no blocking).
  - GameEngine.tick() drains each instance's queue and dispatches to AI agents.
  - Events are scoped per instance_id so instances are fully isolated from each other.
  - No circular imports: this module has ZERO imports from the rest of the project.

Flow:
  Player action
    → GameSession handler (deterministic result returned immediately)
    → GameState.log_event()
        → EventBus.publish()          ← this file
            → engine tick drains queue
                → AgentPool.request(NPC_ADMIN, "npc_reaction", ...)
                    → AI updates NPC properties asynchronously
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List


@dataclass
class GameEvent:
    """A discrete event that occurred in the game world.

    Attributes:
        instance_id: The ScenarioInstance this event belongs to.
        event_type:  Matches the ``event_type`` passed to GameState.log_event().
        data:        Arbitrary context — npc_id, agent_id, item_id, price, etc.
        x, y:        World position where the event occurred (for proximity filters).
        timestamp:   ISO-8601 creation time.
    """

    instance_id: str
    event_type: str
    data: Dict[str, Any]
    x: float = 0.0
    y: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EventBus:
    """
    Central event queue for the entire simulation.

    One queue per ScenarioInstance.  The engine drains each queue on every tick.

    Thread/async safety: ``deque.append`` and ``list(deque)`` + ``deque.clear``
    are both atomic in CPython, so no asyncio lock is needed for single-process use.
    """

    def __init__(self) -> None:
        # instance_id → deque[GameEvent]
        self._queues: Dict[str, Deque[GameEvent]] = defaultdict(deque)

    # ------------------------------------------------------------------
    # Publisher side  (called from GameState, always synchronous)
    # ------------------------------------------------------------------

    def publish(self, event: GameEvent) -> None:
        """Enqueue an event.  Returns immediately — never blocks."""
        self._queues[event.instance_id].append(event)

    # ------------------------------------------------------------------
    # Consumer side  (called from GameEngine, always async context)
    # ------------------------------------------------------------------

    def drain_instance(self, instance_id: str) -> List[GameEvent]:
        """Return all queued events for *instance_id* and clear the queue."""
        q = self._queues.get(instance_id)
        if not q:
            return []
        events = list(q)
        q.clear()
        return events

    def clear_instance(self, instance_id: str) -> None:
        """Discard all queued events for a stopped instance."""
        self._queues.pop(instance_id, None)

    def pending_count(self, instance_id: str) -> int:
        """Number of events waiting for *instance_id*."""
        return len(self._queues.get(instance_id, []))

    def all_pending(self) -> Dict[str, int]:
        """Diagnostic snapshot: {instance_id: pending_count}."""
        return {iid: len(q) for iid, q in self._queues.items() if q}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

# Imported by:
#   - core/state.py     → GameState.log_event() calls event_bus.publish()
#   - core/engine.py    → GameEngine.tick() calls event_bus.drain_instance()
#   - scenarios/instances.py → clear_instance() on stop/delete

event_bus = EventBus()
