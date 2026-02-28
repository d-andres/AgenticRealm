"""
Game Engine — Simulation loop orchestrator.

Each tick processes every active ScenarioInstance through three phases:

  Apply Phase
    Drain NpcTaskQueue for resolved tasks submitted by external agents.
    Apply each resolution to the relevant NPC entity.

  Reaction Phase
    Drain the EventBus queue for the instance.
    Group events by target NPC.
    Enqueue an NpcTask of type "npc_reaction" for each affected NPC.
    External npc_admin agents poll GET /instances/{id}/npc-tasks and
    resolve tasks via POST /instances/{id}/npc-tasks/{task_id}/resolve.
    Tasks not resolved within TASK_TTL_SECONDS are expired silently.

  Autonomous Phase  (every NPC_IDLE_EVERY_TICKS ticks, default 60 = ~2 min at 2 s/tick)
    Each NPC that was not already handled in the reaction phase receives
    an "npc_idle" task so external agents can drive patrol/mood/dialogue.
    Configurable via the NPC_IDLE_EVERY_TICKS env var to control token spend.

This design makes all AI decision-making external and truly agentic:
  - External agents run their own loop with memory and planning
  - The backend never blocks on AI; it only stores and dispatches tasks
  - Any language, framework, or service can act as a system agent
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

# How often (in engine ticks) each NPC receives an autonomous "idle" task.
# Reaction tasks (triggered by player actions) are unaffected by this value.
# At the default tick rate of 2 s:  60 ticks = 2 minutes between idle bursts.
# Lower this for more responsive idle behaviour (more LLM calls/tokens).
# Override at runtime with the NPC_IDLE_EVERY_TICKS environment variable.
_NPC_IDLE_EVERY_TICKS: int = int(os.getenv('NPC_IDLE_EVERY_TICKS', '60'))


class GameEngine:
    """
    Simulation loop.

    Maintains a registry of active ScenarioInstances.
    On every tick it processes each instance's event queue and drives NPC AI.
    """

    def __init__(self, tick_rate: float = 1.0) -> None:
        self.tick_rate = tick_rate
        self.running   = False
        self.turn      = 0
        self.loop_task: Optional[asyncio.Task] = None

        # instance_id → ScenarioInstance (registered when instance status → active)
        self._instances: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Instance registry
    # ------------------------------------------------------------------

    def register_instance(self, instance: Any) -> None:
        """Register an active ScenarioInstance so the engine processes it."""
        self._instances[instance.instance_id] = instance
        scenario = getattr(instance, "scenario_id", "?")
        print(f"[Engine] Registered instance {instance.instance_id[:8]}… ({scenario})")

    def unregister_instance(self, instance_id: str) -> None:
        """Remove a stopped/deleted instance and discard its event queue."""
        self._instances.pop(instance_id, None)
        from core.event_bus import event_bus
        event_bus.clear_instance(instance_id)
        print(f"[Engine] Unregistered instance {instance_id[:8]}…")

    # ------------------------------------------------------------------
    # Loop lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        print("[Engine] Starting simulation loop…")
        self.loop_task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self.running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        print("[Engine] Stopped")

    async def _run_loop(self) -> None:
        try:
            while self.running:
                await asyncio.sleep(self.tick_rate)
                await self.tick()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Engine] Loop error: {e}")

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    async def tick(self) -> None:
        self.turn += 1

        active = [
            inst for inst in self._instances.values()
            if getattr(inst, 'status', 'active') == 'active'
        ]
        if not active:
            return  # no active instances → silent tick

        for instance in active:
            try:
                await self._process_instance(instance)
            except Exception as e:
                print(f"[Engine] Error in instance {instance.instance_id[:8]}: {e}")

    # ------------------------------------------------------------------
    # Per-instance processing
    # ------------------------------------------------------------------

    async def _process_instance(self, instance: Any) -> None:
        from core.event_bus import event_bus
        from store.task_queue import npc_task_queue

        # ---- Apply Phase -------------------------------------------
        # Pull any tasks that external agents have already resolved and
        # apply their NPC updates to the live world state.
        applied = 0
        for task in npc_task_queue.drain_resolved(instance.instance_id):
            if task.resolution:
                self._apply_npc_update(instance, task.npc_id, task.resolution)
                applied += 1
        # Persist any NPC state changes (trust, mood, dialogue) to SQLite.
        if applied:
            try:
                import store.db as db
                db.save_instance_dict(instance.to_dict())
            except Exception:
                pass

        # ---- Reaction Phase ----------------------------------------
        events = event_bus.drain_instance(instance.instance_id)
        npc_events: Dict[str, List[Any]] = {}
        for ev in events:
            # Resolve the affected entity from whichever ID field was logged.
            # store actions (buy, negotiate, steal) log store_id; NPC actions log npc_id.
            entity_id = (
                ev.data.get('npc_id')
                or ev.data.get('store_id')
                or ev.data.get('target_npc_id')
                or ev.data.get('entity_id')
            )
            if not entity_id:
                continue
            npc = instance.state.entities.get(entity_id)
            # Include both free-roaming NPCs and store proprietors (type='store').
            if not npc or npc.type not in ('npc', 'store'):
                continue
            npc_events.setdefault(entity_id, []).append(ev)

        for npc_id, evs in npc_events.items():
            npc = instance.state.entities[npc_id]
            npc_task_queue.enqueue(
                instance_id=instance.instance_id,
                task_type="npc_reaction",
                npc_id=npc_id,
                context=self._build_npc_context(npc, instance, events=evs),
            )

        # ---- Autonomous Phase --------------------------------------
        if self.turn % _NPC_IDLE_EVERY_TICKS == 0:
            for npc_id, npc in list(instance.state.entities.items()):
                if npc.type not in ('npc', 'store'):
                    continue
                if npc_id in npc_events:
                    continue  # already queued a reaction task this tick
                npc_task_queue.enqueue(
                    instance_id=instance.instance_id,
                    task_type="npc_idle",
                    npc_id=npc_id,
                    context=self._build_npc_context(npc, instance),
                )

        # ---- Movement Phase ----------------------------------------
        # Apply patrol_target movement for all NPCs/stores that have one set.
        self._apply_patrol_movement(instance)

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_npc_context(
        self, npc: Any, instance: Any, events: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Build the context dict passed to an external agent's NPC task."""
        ctx: Dict[str, Any] = {
            "npc_id":          npc.id,
            "npc_name":        npc.properties.get("name", npc.id),
            "npc_job":         npc.properties.get("job", "unknown"),
            "npc_personality": npc.properties.get("personality", "neutral"),
            "npc_trust":       npc.properties.get("trust", 0.5),
            "npc_mood":        npc.properties.get("mood", "neutral"),
            "npc_health":      npc.properties.get("health", npc.properties.get("max_health", 100)),
            "npc_max_health":  npc.properties.get("max_health", 100),
            "npc_status":      npc.properties.get("status", "alive"),
            "last_ai_message": npc.properties.get("last_ai_message", ""),
            "world_turn":      self.turn,
            "instance_id":     instance.instance_id,
        }
        if events:
            ctx["events"] = [{"type": ev.event_type, "data": ev.data} for ev in events]
        return ctx

    # ------------------------------------------------------------------
    # NPC movement
    # ------------------------------------------------------------------

    def _apply_patrol_movement(self, instance: Any, speed: float = 8.0) -> None:
        """Move entities that have a ``patrol_target`` set toward that target.

        Called each tick after the Autonomous Phase.  When an NPC reaches its
        target it clears ``patrol_target`` so it does not overshoot on the
        following tick.  The speed parameter is world-units per tick.
        """
        for entity in instance.state.entities.values():
            if entity.type not in ('npc', 'store'):
                continue
            target_id = entity.properties.get('patrol_target')
            if not target_id:
                continue
            target = instance.state.entities.get(target_id)
            if not target:
                # Target entity no longer exists — clear the stale reference.
                entity.properties['patrol_target'] = None
                continue
            dx = target.x - entity.x
            dy = target.y - entity.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist <= speed:
                entity.x = target.x
                entity.y = target.y
                entity.properties['patrol_target'] = None
            else:
                entity.x = round(entity.x + (dx / dist) * speed, 1)
                entity.y = round(entity.y + (dy / dist) * speed, 1)

    # ------------------------------------------------------------------
    # AI dispatch helpers (kept for reference — no longer used by engine)
    # _dispatch_npc_reaction and _dispatch_npc_idle have been replaced by
    # npc_task_queue.enqueue() calls in _process_instance.
    # Resolutions are applied in the Apply Phase via _apply_npc_update.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def _apply_npc_update(
        self, instance: Any, npc_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Apply AI-returned NPC updates to the live world state.

        The AI may return any subset of these keys:
          trust_delta     (float)  — added to current trust, clamped [0, 1]
          health_delta    (float)  — added to current health, clamped [0, max_health];
                                     reaching 0 sets status to 'incapacitated'
          mood            (str)    — replaces current mood
          last_ai_message (str)    — dialogue line stored for next player observe
          patrol_target   (str)    — entity_id the NPC is moving toward
        """
        npc = instance.state.entities.get(npc_id)
        if not npc:
            return

        trust_delta = result.get("trust_delta")
        if trust_delta is not None:
            current = npc.properties.get("trust", 0.5)
            npc.properties["trust"] = round(max(0.0, min(1.0, current + float(trust_delta))), 3)

        health_delta = result.get("health_delta")
        if health_delta is not None:
            max_hp  = npc.properties.get("max_health", 100.0)
            current_hp = npc.properties.get("health", max_hp)
            new_hp = round(max(0.0, min(float(max_hp), current_hp + float(health_delta))), 1)
            npc.properties["health"] = new_hp
            if new_hp <= 0 and npc.properties.get("status") != "incapacitated":
                npc.properties["status"] = "incapacitated"
                # Preserve any AI message; fall back to a generic collapse line.
                if "last_ai_message" not in result:
                    npc.properties["last_ai_message"] = (
                        f"{npc.properties.get('name', npc_id)} collapses."
                    )
            elif new_hp > 0 and npc.properties.get("status") == "incapacitated":
                npc.properties["status"] = "alive"

        for key in ("mood", "last_ai_message", "patrol_target"):
            if key in result:
                npc.properties[key] = result[key]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    # _get_pool removed — the engine no longer calls LLM providers directly.
    # All AI decisions are handled by external agents via the NpcTaskQueue.


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_engine_instance: Optional[GameEngine] = None


def get_engine() -> GameEngine:
    """Return the global GameEngine singleton.  Created lazily if not yet set."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = GameEngine()
    return _engine_instance


def set_engine(engine: GameEngine) -> None:
    """Register the engine created in main.py as the global singleton."""
    global _engine_instance
    _engine_instance = engine
