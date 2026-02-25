# AgenticRealm — TODO

Active task list. See [ARCHITECTURE.md](ARCHITECTURE.md) for full design context.

---

## CRITICAL — Core Platform Value

### 1. System Agent Integration

The task-queue model is live.  The next milestone is ensuring the round-trip
(engine enqueues → agent resolves → engine applies) works end-to-end with a
real external agent.

- [x] Engine enqueues `npc_reaction` tasks when player events are queued
- [x] Engine enqueues `npc_idle` tasks every 15 ticks (≈30 s)
- [x] `GET /instances/{id}/npc-tasks` — external agents poll pending tasks
- [x] `POST /instances/{id}/npc-tasks/{task_id}/resolve` — agent submits decision
- [x] `_apply_npc_update()` writes trust, mood, last_ai_message, patrol_target to NPC entity
- [x] Task TTL (12 s) — expired tasks silently dropped; world continues
- [ ] End-to-end test: minimal Python polling agent → resolves tasks → confirm NPC state changes visible in `observe`
- [ ] Document a reference `npc_admin` agent implementation in `backend/clients/`

### 2. Scenario Generator Parsers

- [x] `_parse_generated_stores()` — converts generation output → `GeneratedStore` objects
- [x] `_parse_generated_npcs()` — converts generation output → `GeneratedNPC` objects
- [x] `_assign_items_to_stores()` — distributes items across store inventories
- [x] Rule-based decision-maker (baseline — deterministic, no LLM)

### 3. Engine Orchestration for Market Actions

- [x] Event Bus (`core/event_bus.py`) — `GameState.log_event()` publishes `GameEvent`; engine drains per tick
- [x] NPC Apply Phase — drain resolved tasks from `NpcTaskQueue`; apply to NPC entity
- [x] NPC Reaction Phase — group queued events by NPC; enqueue `npc_reaction` task per NPC
- [x] NPC Autonomous Phase — enqueue `npc_idle` task every 15 ticks per unhandled NPC
- [x] `_apply_npc_update()` — writes `trust_delta`, `mood`, `last_ai_message`, `patrol_target`
- [x] Full action pipeline: validate → execute → return combined state
- [x] Action handlers: `move`, `observe`, `talk`, `negotiate`, `buy`, `hire`, `steal`, `trade`
- [x] Trust-based pricing: `negotiate`, `buy`, `hire`, `steal` all read NPC `trust`

---

## HIGH — Core Platform Features

- [x] NPC position updates on each tick (`patrol_target` applied to NPC coordinates via `_apply_patrol_movement` in engine)
- [x] Instance world state persisted to SQLite after every player action and after every engine Apply Phase that resolves NPC tasks
- [x] **Bug fix**: Reaction Phase now resolves `store_id` events and includes `type='store'` entities — store interactions (buy/negotiate/steal) now correctly trigger `npc_reaction` tasks for the shopkeeper
- [x] **Bug fix**: `max_turns` removed from `ScenarioInstance.state.properties` and score formula; no longer leaks into external agent task context
- [ ] AI-driven action outcomes — route `negotiate`, `trade`, `hire` decisions through resolved task context for authentic acceptance logic (currently deterministic with trust modifier)
- [ ] Negotiation feedback — explain why offers were accepted or rejected (requires `last_ai_message` surfaced in action reply)
- [ ] SSE / WebSocket push for live NPC state (replace polling)
- [ ] Leaderboard persistence — store completed instance outcomes and strategy analysis
- [ ] Tests for scenario instance interactions (agent actions, NPC responses, action validation)

---

## MEDIUM — Admin & Usability

- [ ] Reference system agent implementations in `backend/clients/`:
  - `npc_admin_client.py` — minimal polling loop example
  - `storyteller_client.py` — writes narrative to shared memory
- [ ] Admin CLI — reset NPC trust, replenish inventory, inspect instance state
- [ ] Trust level and NPC state visualization in frontend dashboard
- [ ] Additional scenario templates (street negotiation, economic trading chain, heist)

---

## LOWER — Nice to Have

- [ ] Replay system — decision-by-decision analysis, compare agent to optimal path
- [ ] Strategic feedback — tell agents why their approach worked or failed
- [ ] Memory store usage examples — show how `storyteller` + `npc_admin` can share context

---

## Technical Notes

**Current State**
- Backend is a pure game runtime — no LLM calls, no API keys stored
- All AI (player and system) is external; agents connect via `POST /agents/register` with a `role` field
- Engine 3-phase tick: Apply (drain resolved tasks) → Reaction (enqueue npc_reaction) → Autonomous (enqueue npc_idle every 15 ticks)
- `NpcTask` TTL = 12 s; expired tasks silently dropped
- `store/task_queue.py` — `NpcTaskQueue` singleton; `store/memory_store.py` — optional shared blackboard
- Agent roles: `player`, `npc_admin`, `scenario_generator`, `storyteller`, `game_master`, `judge`
- `SYSTEM_ROLES` set in `store/agent_store.py`; `is_system_agent` property auto-derived from role
- Action pipeline complete: `process_action` validates against `scenario.allowed_actions`; all 8 handlers implemented with trust-based dynamic pricing
- Frontend is a simulation host screen — shows connected agents (by role), scenario selector, join key, world map, activity log

**Architecture Constraints**
- `scenarios/__init__.py` intentionally does NOT import from `instances.py` (prevents eager DB init)
- No prefix in `APIRouter()` — prefix set exclusively in `main.py` `include_router()`
- `ai_agents/` package retained on disk but is no longer imported by the engine or any route
