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
- [ ] Rule-based decision-maker (baseline — deterministic, no LLM):
  - Driven by the NPC's generated attributes (role type, personality, goal) from `ScenarioInstance`
  - Used for testing before hooking in OpenAI/Anthropic
- [ ] Store generated NPC instances inside `ScenarioInstance` alongside `GameState`
- [ ] NPC state: position, inventory, `trust_levels[agent_id]`, generated role attributes

### 2. Scenario Generator Parsers

Stubs exist in `scenarios/generator.py` — implement the actual parsing:

- [ ] `_parse_generated_stores()` — convert AI output → `GeneratedStore` objects
- [ ] `_parse_generated_npcs()` — convert AI output → `GeneratedNPC` objects
- [ ] `_assign_items_to_stores()` — distribute items across store inventories
- [ ] Wire instance creation endpoint to call `ScenarioGenerator` with template

### 3. Engine Orchestration for Market Actions

- [ ] Connect `core/engine.py` to instance action pipeline:
  - Parse action type from request
  - Validate action against world rules defined by the scenario template
  - Execute user action + update state
  - Broadcast event to relevant NPCs (`perceive`)
  - Run each NPC's `decide` + `act`
  - Return combined state + all events
- [ ] Action handlers: one per `ActionType` defined in the scenario template
- [ ] Trust dynamics — every action updates `npc.trust_levels[agent_id]`

---

## HIGH — Core Platform Features

- [ ] NPC state updates on each engine tick (position, inventory, trust)
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
- Scenario instances persist via SQLite; Postgres migration deferred until generation works
- `ScenarioGenerator` parsers are stubs returning empty lists — generation flow not yet connected
- Feed store and analytics work; keep backward-compatible while adding SSE
- Frontend expects WebSocket but backend has none — add once engine orchestration is solid

**Architecture Constraints**
- `scenarios/__init__.py` intentionally does NOT import from `instances.py` (prevents eager DB init)
- Routes set no prefix in `APIRouter()` — prefix is set exclusively in `main.py`
- Decision-maker signature: `(generation_type: str, context: dict) -> dict`
