# AgenticRealm — TODO

Active task list. See [ARCHITECTURE.md](ARCHITECTURE.md) for full design context.

---

## CRITICAL — Core Platform Value

### 1. System Agent Framework

The platform's core promise — intelligent NPCs that respond dynamically to user agents.

- [ ] Create `SystemAgent` base class (`backend/agents/base.py`):
  - `perceive(world_state, agent_context) -> dict`
  - `decide(perception, decision_maker) -> dict`  *(pluggable — any provider)*
  - `act(action, world_state) -> dict`
- [ ] NPC roles and their behaviors are defined by the scenario template and generated per instance — `SystemAgent` must be generic enough to represent any role
- [x] Rule-based decision-maker (baseline — deterministic, no LLM):
  - `_rule_based_decision_maker` implemented in `scenarios/generator.py`
- [x] Store generated NPC instances inside `ScenarioInstance` alongside `GameState`
- [x] NPC state: position, inventory, `trust_levels[agent_id]`, generated role attributes
  - Trust delta applied per tick via `engine._apply_npc_update()`; full inventory mutation pending

### 2. Scenario Generator Parsers

Parsers implemented in `scenarios/generator.py`:

- [x] `_parse_generated_stores()` — converts AI output → `GeneratedStore` objects
- [x] `_parse_generated_npcs()` — converts AI output → `GeneratedNPC` objects
- [x] `_assign_items_to_stores()` — distributes items across store inventories
- [x] Wire instance creation endpoint to call `ScenarioGenerator` with template

### 3. Engine Orchestration for Market Actions

- [x] Event Bus (`core/event_bus.py`) — `GameState.log_event()` publishes `GameEvent`; engine drains per tick
- [x] NPC AI Reaction Phase — engine groups queued events by NPC, dispatches `npc_reaction` to AI agent
- [x] NPC Autonomous Phase — `npc_idle` dispatched every 30 ticks per NPC; `asyncio.wait_for` 8 s cap
- [x] `_apply_npc_update()` — writes `trust_delta`, `mood`, `last_ai_message`, `patrol_target` to NPC entity
- [ ] Connect full action pipeline: validate action against template `ActionType` list → execute → return combined state
- [ ] Action handlers: one per `ActionType` defined in the scenario template
- [ ] Pricing and hire/steal outcome calculations based on NPC-generated attributes

---

## HIGH — Core Platform Features

- [ ] `SystemAgent` base class — `perceive → decide → act` loop driven by generated NPC attributes
- [ ] Full action-outcome calculations (pricing multipliers, hire success rates, steal risk)
- [ ] Negotiation feedback — explain why offers were accepted or rejected
- [ ] SSE / WebSocket push for live NPC state (replace polling)
- [ ] Leaderboard persistence — store completed instance game outcomes and strategy analysis
- [ ] Tests for scenario instance interactions (agent actions, NPC responses, action validation)
- [ ] Instance snapshot improvements — persist NPC trust/inventory changes across restarts

---

## MEDIUM — Admin & Usability

- [ ] System prompt library at `backend/prompts/` — per-scenario NPC decision templates (generated at instance creation)
- [ ] Decision-maker factory — swap rule-based → OpenAI → Anthropic via config
- [ ] Admin CLI — reset NPC trust, replenish inventory, inspect instance state
- [ ] Trust level and pricing visualization in frontend dashboard

---

## LOWER — Nice to Have

- [ ] LLM-powered NPC decisions for live scenarios (plug OpenAI/Anthropic into `decide()`)
- [ ] Replay system — decision-by-decision analysis, compare agent to optimal path
- [ ] Additional scenario templates: street negotiation, economic trading chain, heist
- [ ] Strategic feedback — tell agents why their approach worked or failed

---

## Technical Notes

**Current State**
- Backend fully reorganized: `scenarios/`, `store/`, `routes/` packages; `main.py` is a thin entry point
- Scenario instances persist via SQLite; `generate_world_entities()` generates stores, NPCs, items on creation (rule-based fallback, ~0.5 s)
- `core/event_bus.py` — pub/sub `GameEvent` queue; `GameState.log_event()` publishes when `_instance_id` is set
- `core/engine.py` — `_instances` registry; Reaction Phase dispatches `npc_reaction` per NPC when events queued; Autonomous Phase dispatches `npc_idle` every 30 ticks; all AI calls are async and timeout-guarded
- Both OpenAI and Anthropic NPC_ADMIN agents implement `npc_reaction` and `npc_idle`
- Feed store and analytics work; keep backward-compatible while adding SSE
- Frontend expects WebSocket but backend has none — add once action pipeline is solid

**Architecture Constraints**
- `scenarios/__init__.py` intentionally does NOT import from `instances.py` (prevents eager DB init)
- Routes set no prefix in `APIRouter()` — prefix is set exclusively in `main.py`
- Decision-maker signature: `(generation_type: str, context: dict) -> dict`
