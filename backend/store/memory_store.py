"""
Memory Store — per-instance shared memory for system agents.

Design
------
External system agents (npc_admin, scenario_generator, storyteller, etc.) need
persistent context across ticks so they can remember:
  - What a player did three turns ago
  - What a specific NPC has said and felt over time
  - Running world narrative threads
  - Decisions already made so agents don't repeat themselves

Any external agent can write entries keyed by a namespaced string.
Any other agent can read those entries.  The host screen can also surface
relevant memory entries for observers.

Suggested key namespaces:
  player:{agent_id}:interactions   — chronological log of all player actions
  player:{agent_id}:relationship   — trust/standing summaries per NPC
  npc:{npc_id}:context             — NPC admin's running notes on this NPC
  npc:{npc_id}:dialogue_history    — recent things the NPC has said
  world:narrative                  — storyteller's running narrative thread
  world:facts                      — key world facts agents have established
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """A single piece of shared memory written by an agent."""
    key: str
    value: Any
    agent_id: str           # who wrote it
    instance_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    ttl_turns: Optional[int] = None  # if set, expires after N world turns

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key":        self.key,
            "value":      self.value,
            "agent_id":   self.agent_id,
            "timestamp":  self.timestamp,
            "ttl_turns":  self.ttl_turns,
        }


class InstanceMemory:
    """
    Memory bag for a single scenario instance.

    Keys are arbitrary strings; each key stores a list of entries in
    chronological order (newest = last).  Callers can:
      - write(key, value, agent_id) — append a new entry
      - read(key, n) — return the last n entries for a key
      - read_all() — return all keys and their latest values
      - search(prefix) — return all keys matching a prefix
    """

    def __init__(self, instance_id: str) -> None:
        self.instance_id = instance_id
        # key → [MemoryEntry, ...]  newest last
        self._data: Dict[str, List[MemoryEntry]] = {}

    def write(
        self,
        key: str,
        value: Any,
        agent_id: str,
        ttl_turns: Optional[int] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            key=key,
            value=value,
            agent_id=agent_id,
            instance_id=self.instance_id,
            ttl_turns=ttl_turns,
        )
        self._data.setdefault(key, []).append(entry)
        return entry

    def read(self, key: str, n: int = 10) -> List[Dict[str, Any]]:
        """Return the last ``n`` entries for ``key``, newest last."""
        entries = self._data.get(key, [])
        return [e.to_dict() for e in entries[-n:]]

    def read_latest(self, key: str) -> Optional[Dict[str, Any]]:
        """Return the most recent entry for ``key``, or None."""
        entries = self._data.get(key, [])
        return entries[-1].to_dict() if entries else None

    def search(self, prefix: str) -> Dict[str, Any]:
        """Return the latest value for every key that starts with ``prefix``."""
        result = {}
        for key, entries in self._data.items():
            if key.startswith(prefix) and entries:
                result[key] = entries[-1].to_dict()
        return result

    def read_all_latest(self) -> Dict[str, Any]:
        """Return the latest value for every key in this instance's memory."""
        return {key: entries[-1].to_dict() for key, entries in self._data.items() if entries}

    def keys(self) -> List[str]:
        return list(self._data.keys())


class MemoryStore:
    """Global registry of per-instance memory bags."""

    def __init__(self) -> None:
        self._instances: Dict[str, InstanceMemory] = {}

    def get_or_create(self, instance_id: str) -> InstanceMemory:
        if instance_id not in self._instances:
            self._instances[instance_id] = InstanceMemory(instance_id)
        return self._instances[instance_id]

    def get(self, instance_id: str) -> Optional[InstanceMemory]:
        return self._instances.get(instance_id)

    def clear_instance(self, instance_id: str) -> None:
        self._instances.pop(instance_id, None)


# Global singleton
memory_store = MemoryStore()
