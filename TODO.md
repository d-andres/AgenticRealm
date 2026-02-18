# AgenticRealm - TODO / Next Steps

This file lists actionable tasks and priorities for the project. Use it as a concise checklist for short-term work.

## Architecture Overview
**Scenarios = TEMPLATES, Instances = AI-GENERATED UNIQUE WORLDS**

- `scenarios.py` - Defines **templates** with rules, constraints, and generation guidance
- `scenario_generator.py` - Uses pluggable AI decision-maker to generate unique scenario instances
- Each time a scenario is created, AI generates new stores, NPCs, items, and stories
- No two scenario instances are identical

---

**CRITICAL Priority** (Required for core learning platform value)

**1. Scenario Generator Implementation**
- [ ] Implement decision-maker interface in `scenario_generator.py`:
  - Signature: `(generation_type: str, context: dict) -> dict`
  - Support multiple AI providers: rule-based, OpenAI, Copilot, AgentGPT, custom
- [ ] Implement parser methods in ScenarioGenerator:
  - `_parse_generated_stores()` - convert AI output to GeneratedStore objects
  - `_parse_generated_npcs()` - convert AI output to GeneratedNPC objects
  - `_assign_items_to_stores()` - distribute items across store inventories
- [ ] Create rule-based decision maker (baseline):
  - Can generate diverse stores, NPCs, items procedurally
  - Uses template constraints to guide generation
  - Fast, deterministic, good for testing
- [ ] Implement generation endpoints in `main.py`:
  - When instance is created, call scenario_generator with template

**2. System Agent Framework for Market Square**
- [ ] Create `SystemAgent` base class in `backend/agents/base.py` with:
  - `perceive(world_state: dict, agent_context: dict) -> dict` - what NPC observes
  - `decide(perception: dict, decision_maker: Callable) -> dict` - returns action (pluggable decision logic)
  - `act(action: dict, world_state: dict) -> dict` - executes action, updates state
  - **Design note**: `decide()` accepts a pluggable decision-maker function, allowing any AI provider (custom rule-based, OpenAI, Copilot, AgentGPT, etc.)
- [ ] Implement Market Square NPC agents in `backend/agents/market_square/`:
  - `CorruptShopkeeper` - Resists negotiation, tracks trust, defends item
  - `CityGuard` - Patrols, detects theft attempts, can be bribed/hired
  - `HonestShopkeeper` - Reacts to haggling, adjusts pricing based on demand
  - `HiredThief` - Calculates theft success probability, refuses if guards present
  - `MerchantHelper` - Facilitates trades, provides market intelligence
  - `InformationBroker` - Reveals guard schedules, pricing, vulnerabilities
- [ ] Store NPC instances in ScenarioInstance alongside GameState
- [ ] Create NPC state tracking: position, inventory, trust_levels[agent_id], mood

**3. Fix Engine Orchestration for Market Scenarios**
- [ ] Connect `core/engine.py` to market action pipeline:
  - When user submits action → parse action (move, talk, negotiate, buy, hire, steal, trade)
  - Validate action against world rules (gold available, guards present, etc.)
  - Execute user action + update user state
  - Broadcast event to relevant NPCs (NPCs perceive the action)
  - Call each affected NPC's `decide()` method
  - Execute NPC actions
  - Return combined state + all events to user
- [ ] Implement action-type handlers:
  - `Handle_move`: Update position, check proximity to NPCs/stores
  - `Handle_negotiate`: Evaluate persuasion + trust, generate counter-offer
  - `Handle_buy`: Verify gold, update inventory, trust level
  - `Handle_hire`: Verify gold, set NPC availability, add to player team
  - `Handle_steal`: Calculate success probability (guards + thief skill), execute theft or catch
  - `Handle_trade`: Verify item values, execute if mutually beneficial
- [ ] Implement trust dynamics: each action affects NPC trust levels

**4. System Agent Decision Logic (Provider-Agnostic)**
- [ ] Create `DecisionMaker` interface in `backend/agents/decision_manager.py`:
  - `evaluate(npc_type: str, perception: dict, npc_state: dict) -> dict` - returns structured action
  - Signature: `Callable[[str, dict, dict], dict]` for easy plugging of external providers
  - Supports: rule-based (no AI), OpenAI LLM, Copilot, AgentGPT, custom logic
- [ ] Implement rule-based decision maker (baseline, no LLM):
  - CorruptShopkeeper: increase price if player shows interest, refuse low offers
  - CityGuard: patrol pattern, react to nearby theft, increase detection on repeated offenses
  - HonestShopkeeper: fair pricing, gradual discounts as trust builds
  - HiredThief: assess guard presence, theft difficulty, success probability; decline suicidal jobs
  - MerchantHelper: facilitate mutually beneficial trades, suggest good deals
  - InformationBroker: share info strategically for gold
- [ ] System agents use DecisionMaker interface; users swap provider later (OpenAI, Copilot, etc.)


---

**High Priority** (Core platform features)

- [ ] Implement dynamic NPC state updates in game loop (position, inventory changes, trust changes)
- [ ] Add negotiation transcripts/feedback: explain why NPC accepted/rejected offers
- [ ] Implement Server-Sent Events (SSE) or WebSocket push for real-time NPC actions and state changes (replace polling)
- [ ] Add leaderboards persistence: store completed market games with strategy analysis (which approach won)
- [ ] Add comprehensive tests for market scenario interactions (negotiation, theft, hiring, trading flows)
- [ ] Improve instance persistence: periodic snapshots of NPC state (reputation, inventory changes)

---

**Medium Priority** (Admin & Usability)

- [ ] Create system prompts library in `/backend/prompts/market_square/` with decision templates
- [ ] Add pluggable decision-maker factory: allow swapping between rule-based, OpenAI, custom implementations
- [ ] Add admin CLI to reset NPC trust levels, replenish inventory, manage instance state
- [ ] Create visualization of NPC trust levels and pricing changes over time
- [ ] Extend tests to cover edge cases (low gold, all paths blocked, high vs low trust scenarios)

---

**Lower Priority / Nice to Have**

- [ ] Integrate LLM providers (OpenAI Assistants, Copilot AI, AgentGPT, etc.) into DecisionMaker factory
- [ ] Add richer presentation UI showing NPC positions, store inventory, trust levels in real-time
- [ ] Support additional market scenarios: espionage (infiltrate, extract secrets), economic (trading chains), heist (multi-NPC coordination)
- [ ] Add replay system: show agent decisions vs. NPC decisions with analysis of why one strategy won
- [ ] Strategic feedback: compare agent approach to optimal path, suggest improvements

---

**Technical Notes**

- **AI-Driven Scenario Generation**: 
  - `scenarios.py` defines **TEMPLATES** (rules, constraints, generation guidance)
  - `scenario_generator.py` uses pluggable decision-maker to generate **UNIQUE INSTANCES**
  - Each scenario instance is procedurally generated with unique stores, NPCs, items, stories
  - No two market squares are identical - examples: stores named "The Copper Cauldron" vs "Azure Imports", different shopkeeper personalities, different items available
- **Scenario Generator Workflow**:
  1. API creates instance from template (e.g., "market_square")
  2. Generator calls decision_maker("generate_stores", context)
  3. AI generates 3-6 unique stores with names, locations, proprietor personalities
  4. Generator calls decision_maker("generate_npcs", context)
  5. AI generates 4-8 NPCs with names, jobs, skills, personalities
  6. Generator calls decision_maker("generate_items_and_inventory", context)
  7. AI populates unique items across all stores
  8. Generator calls decision_maker for target item selection
  9. Returns complete, ready-to-play scenario instance
- **Pluggable Decision-Maker**:
  - Signature: `(generation_type: str, context: dict) -> dict`
  - Can be rule-based (deterministic baseline for testing)
  - Can be OpenAI LLM (creative, consistent)
  - Can be Copilot (flexible, multi-modal)
  - Can be AgentGPT (autonomously creative)
  - Easy to swap implementations based on your preference
- **Current Debt**:
  - Instance persistence is SQLite prototype; plan Postgres+ORM migration after generation works
  - Feed store and presentation work; keep backward-compatible while adding SSE/WebSocket
  - Unused files to remove: `agents/judge.py`, `agents/registrar.py`, `agents/user_agent.py`
  - Frontend expects WebSocket but backend has none; add once market orchestration is solid
- **Future Scenarios**: 
  - Current structure supports adding new scenario TEMPLATES (street negotiation, heist, economic)
  - Each template generates unique instances with pluggable AI decision-maker
  - Templates define rules; AI fills in the specifics
