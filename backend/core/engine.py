"""
Game Engine — Simulation loop orchestrator.

Each tick processes every active ScenarioInstance through two phases:

  Reaction Phase
    Drain the EventBus queue for the instance.
    Group events by target NPC.
    Dispatch a batched "npc_reaction" request to the NPC_ADMIN AI agent.
    AI updates are applied asynchronously via fire-and-forget tasks.

  Autonomous Phase  (every _AI_IDLE_EVERY_TICKS ticks)
    Each NPC that was not already handled in the reaction phase receives a
    "npc_idle" request so it can patrol, change mood, or update dialogue.

Cost controls:
  - AI is only called when there are queued events OR on the idle interval.
  - Multiple events for the same NPC are merged into a single request.
  - Each AI call is capped at _AI_CALL_TIMEOUT seconds; timed-out calls are
    silently dropped — the deterministic result already reached the player.
  - Idle interval defaults to 30 ticks (≈30 s at tick_rate=1.0).

The player's HTTP request is never blocked by AI calls.
"""

import asyncio
from typing import Any, Dict, List, Optional

# How often (in engine ticks) each NPC gets an autonomous "idle" AI call.
# At tick_rate=1.0 this means roughly once every 30 seconds per NPC.
_AI_IDLE_EVERY_TICKS: int = 30

# Maximum seconds to wait for a single NPC_ADMIN AI response before discarding.
_AI_CALL_TIMEOUT: float = 8.0


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

        try:
            pool = await self._get_pool()
        except Exception:
            pool = None

        for instance in active:
            try:
                await self._process_instance(instance, pool)
            except Exception as e:
                print(f"[Engine] Error in instance {instance.instance_id[:8]}: {e}")

    # ------------------------------------------------------------------
    # Per-instance processing
    # ------------------------------------------------------------------

    async def _process_instance(self, instance: Any, pool: Any) -> None:
        from core.event_bus import event_bus
        from ai_agents.interfaces import AgentRole

        events = event_bus.drain_instance(instance.instance_id)

        # Check whether NPC_ADMIN is available before attempting any dispatch
        npc_admin_available = (
            pool is not None
            and AgentRole.NPC_ADMIN in pool.agents
            and len(pool.agents[AgentRole.NPC_ADMIN]) > 0
        )

        # ---- Reaction Phase ----------------------------------------
        # Group queued events by the target NPC so multiple events from one
        # player turn are batched into a single AI request.
        npc_events: Dict[str, List[Any]] = {}
        if npc_admin_available:
            for ev in events:
                npc_id = ev.data.get('npc_id') or ev.data.get('target_npc_id')
                if not npc_id:
                    continue
                npc = instance.state.entities.get(npc_id)
                if not npc or npc.type != 'npc':
                    continue
                npc_events.setdefault(npc_id, []).append(ev)

            for npc_id, evs in npc_events.items():
                npc = instance.state.entities[npc_id]
                asyncio.create_task(
                    self._dispatch_npc_reaction(pool, instance, npc, evs)
                )

        # ---- Autonomous Phase ---------------------------------------
        # Fire once every _AI_IDLE_EVERY_TICKS ticks per NPC not already
        # handled in the reaction phase this tick.
        if npc_admin_available and (self.turn % _AI_IDLE_EVERY_TICKS == 0):
            for npc_id, npc in list(instance.state.entities.items()):
                if npc.type != 'npc':
                    continue
                if npc_id in npc_events:
                    continue  # already handled above
                asyncio.create_task(
                    self._dispatch_npc_idle(pool, instance, npc)
                )

    # ------------------------------------------------------------------
    # AI dispatch helpers
    # ------------------------------------------------------------------

    async def _dispatch_npc_reaction(
        self, pool: Any, instance: Any, npc: Any, events: List[Any]
    ) -> None:
        """Ask NPC_ADMIN to react to one or more queued events for this NPC."""
        from ai_agents.interfaces import AgentRole
        try:
            response = await asyncio.wait_for(
                pool.request(
                    role=AgentRole.NPC_ADMIN,
                    action="npc_reaction",
                    context={
                        "npc_id":          npc.id,
                        "npc_name":        npc.properties.get("name", npc.id),
                        "npc_job":         npc.properties.get("job", "unknown"),
                        "npc_personality": npc.properties.get("personality", "neutral"),
                        "npc_trust":       npc.properties.get("trust", 0.5),
                        "events":          [{"type": ev.event_type, "data": ev.data} for ev in events],
                        "instance_id":     instance.instance_id,
                    },
                ),
                timeout=_AI_CALL_TIMEOUT,
            )
            if response and response.success:
                self._apply_npc_update(instance, npc.id, response.result)
        except asyncio.TimeoutError:
            pass  # deterministic result already returned to player; skip
        except Exception as e:
            print(f"[Engine] NPC reaction error ({npc.id}): {e}")

    async def _dispatch_npc_idle(
        self, pool: Any, instance: Any, npc: Any
    ) -> None:
        """Ask NPC_ADMIN for autonomous idle/patrol behaviour."""
        from ai_agents.interfaces import AgentRole
        try:
            response = await asyncio.wait_for(
                pool.request(
                    role=AgentRole.NPC_ADMIN,
                    action="npc_idle",
                    context={
                        "npc_id":          npc.id,
                        "npc_name":        npc.properties.get("name", npc.id),
                        "npc_job":         npc.properties.get("job", "unknown"),
                        "npc_personality": npc.properties.get("personality", "neutral"),
                        "npc_trust":       npc.properties.get("trust", 0.5),
                        "npc_mood":        npc.properties.get("mood", "neutral"),
                        "world_turn":      self.turn,
                        "instance_id":     instance.instance_id,
                    },
                ),
                timeout=_AI_CALL_TIMEOUT,
            )
            if response and response.success:
                self._apply_npc_update(instance, npc.id, response.result)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"[Engine] NPC idle error ({npc.id}): {e}")

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def _apply_npc_update(
        self, instance: Any, npc_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Apply AI-returned NPC updates to the live world state.

        The AI may return any subset of these keys:
          trust_delta  (float)  — added to current trust, clamped [0, 1]
          mood         (str)    — replaces current mood
          last_ai_message (str) — dialogue line stored for next player observe
          patrol_target   (str) — entity_id the NPC is moving toward
        """
        npc = instance.state.entities.get(npc_id)
        if not npc:
            return

        trust_delta = result.get("trust_delta")
        if trust_delta is not None:
            current = npc.properties.get("trust", 0.5)
            npc.properties["trust"] = round(max(0.0, min(1.0, current + float(trust_delta))), 3)

        for key in ("mood", "last_ai_message", "patrol_target"):
            if key in result:
                npc.properties[key] = result[key]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_pool(self) -> Any:
        from ai_agents.agent_pool import get_agent_pool
        return await get_agent_pool()


# ---------------------------------------------------------------------------
# Module-level singleton accessor (mirrors the agent_pool pattern)
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
