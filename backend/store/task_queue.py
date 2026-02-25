"""
NPC Task Queue — per-instance queue of pending NPC decisions.

Design
------
When the engine tick determines an NPC needs to react or act autonomously,
it enqueues a task here instead of calling an internal LLM.  External system
agents (npc_admin role) poll ``GET /instances/{id}/npc-tasks``, run their own
reasoning loop, and resolve tasks via ``POST /instances/{id}/npc-tasks/{task_id}/resolve``.

If a task is not resolved within ``TASK_TTL_SECONDS``, the engine's next tick
will apply a rule-based fallback so the world never stalls waiting for an agent.

Task lifecycle:  pending → resolved | expired
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


# How long a task stays pending before the engine applies a rule-based fallback.
TASK_TTL_SECONDS: float = 12.0


@dataclass
class NpcTask:
    """A single pending NPC decision task."""

    task_id: str
    instance_id: str
    task_type: str          # "npc_reaction" | "npc_idle" | "npc_interaction"
    npc_id: str
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending" # pending | resolved | expired
    resolution: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None  # agent_id that resolved it
    resolved_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        return (datetime.now() - self.created_at).total_seconds() > TASK_TTL_SECONDS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id":     self.task_id,
            "instance_id": self.instance_id,
            "task_type":   self.task_type,
            "npc_id":      self.npc_id,
            "context":     self.context,
            "created_at":  self.created_at.isoformat(),
            "status":      self.status,
            "resolution":  self.resolution,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class NpcTaskQueue:
    """
    In-memory task queue for all instances.

    Thread/async safety: all mutations are synchronous dict/list operations,
    which are atomic in CPython for single-process deployments.
    """

    def __init__(self) -> None:
        # instance_id → {task_id: NpcTask}
        self._tasks: Dict[str, Dict[str, NpcTask]] = {}

    # ------------------------------------------------------------------
    # Producer (engine)
    # ------------------------------------------------------------------

    def enqueue(
        self,
        instance_id: str,
        task_type: str,
        npc_id: str,
        context: Dict[str, Any],
    ) -> NpcTask:
        """Create and enqueue a new NPC decision task.  Returns the task."""
        task = NpcTask(
            task_id=str(uuid.uuid4()),
            instance_id=instance_id,
            task_type=task_type,
            npc_id=npc_id,
            context=context,
        )
        self._tasks.setdefault(instance_id, {})[task.task_id] = task
        return task

    # ------------------------------------------------------------------
    # Consumer (external agent poll)
    # ------------------------------------------------------------------

    def get_pending(self, instance_id: str, limit: int = 20) -> List[NpcTask]:
        """Return up to ``limit`` pending (non-expired) tasks for an instance."""
        instance_tasks = self._tasks.get(instance_id, {})
        pending = []
        for task in list(instance_tasks.values()):
            if task.status == "pending":
                if task.is_expired():
                    task.status = "expired"
                else:
                    pending.append(task)
            if len(pending) >= limit:
                break
        return pending

    def resolve(
        self,
        instance_id: str,
        task_id: str,
        resolution: Dict[str, Any],
        resolved_by: str,
    ) -> Optional[NpcTask]:
        """Mark a task resolved and store the agent's decision.  Returns the task or None."""
        task = self._tasks.get(instance_id, {}).get(task_id)
        if not task or task.status != "pending":
            return None
        task.status = "resolved"
        task.resolution = resolution
        task.resolved_by = resolved_by
        task.resolved_at = datetime.now()
        return task

    # ------------------------------------------------------------------
    # Engine: drain expired + resolved tasks for NPC updates
    # ------------------------------------------------------------------

    def drain_resolved(self, instance_id: str) -> List[NpcTask]:
        """
        Return all resolved tasks for an instance and remove them from the queue.
        Also expires and removes stale pending tasks (after TTL) for cleanup.
        """
        instance_tasks = self._tasks.get(instance_id, {})
        resolved = []
        to_remove = []

        for task_id, task in list(instance_tasks.items()):
            if task.status == "resolved":
                resolved.append(task)
                to_remove.append(task_id)
            elif task.status == "pending" and task.is_expired():
                task.status = "expired"
                to_remove.append(task_id)
            elif task.status == "expired":
                to_remove.append(task_id)

        for tid in to_remove:
            instance_tasks.pop(tid, None)

        return resolved

    def get_task(self, instance_id: str, task_id: str) -> Optional[NpcTask]:
        return self._tasks.get(instance_id, {}).get(task_id)

    def clear_instance(self, instance_id: str) -> None:
        self._tasks.pop(instance_id, None)


# Global singleton
npc_task_queue = NpcTaskQueue()
