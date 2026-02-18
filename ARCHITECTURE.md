# AgenticRealm Architecture

## Core Concept

**AgenticRealm** is an **Agentic AI System** and API-first learning platform where:

- **User Agents** (externally designed in GPT Builder, Claude, etc.) submit API calls to interact with dynamic scenarios
- **System AI Agents** (built-in agents) control NPCs, merchants, guards, and other characters within scenarios
- **Multi-Agent Interaction** teaches users about prompt engineering, agent design, and strategy through real emergent gameplay

Users design agents externally, submit them through the API, and watch them navigate complex social/economic scenarios with intelligent NPCs. The platform evaluates success and provides feedback on agent decision-making effectiveness.

## Scenario Design: Templates → AI-Generated Instances

**Core Principle**: Scenarios are **templates** that define rules and constraints. When players create instances, **AI generates unique worlds** — no two scenarios are identical.

### How It Works

```
ScenarioTemplate (rules, constraints)
        ↓
scenario_generator.py (pluggable AI decision-maker)
        ↓
GeneratedScenarioInstance (unique stores, NPCs, items, story)
        ↓
Player joins and plays unique world
```

### Example: Market Square Template

**Template Definition** (`scenarios.py`):
- Defines rules: "3-6 stores, 4-8 NPCs, 10-20 items"
- Defines constraints: possible NPC jobs, item rarities, difficulty range
- Defines success criteria: "obtain target item, minimize gold spent"
- Does NOT define specific store names, NPCs, items, or story

**Generation Process** (`scenario_generator.py`):
```python
# 1. Initialize generator with pluggable decision-maker
generator = ScenarioGenerator(decision_maker=openai_model)

# 2. Generate unique stores
stores = generator._generate_stores(template)
# AI output example:
# [
#   {name: "The Copper Cauldron", proprietor: "Elara Smithson", items: [...]},
#   {name: "Azure Imports", proprietor: "Merchant Hassan", items: [...]}
# ]

# 3. Generate unique NPCs
npcs = generator._generate_npcs(template, stores)
# AI output example:
# [
#   {name: "Captain Vex", job: "guard", skills: {combat: 3, detection: 2}},
#   {name: "Silent Raith", job: "thief", skills: {stealth: 3, theft: 3}}
# ]

# 4. Populate inventories, create target item, generate story
# 5. Identify solution paths and difficulty assessment
```

**Result**: A unique `GeneratedScenarioInstance` with:
- All stores, NPCs, and items procedurally generated
- Environmental storytelling (flavor text about the market)
- Multiple solution paths identified
- Difficulty rating calculated
- Efficiency expectations set

### Pluggable Decision-Makers

The `scenario_generator.py` accepts any decision-maker function:

```python
# Option 1: Rule-based (deterministic, fast)
def rule_based_generator(gen_type: str, context: dict) -> dict:
    if gen_type == "generate_stores":
        return generate_random_stores(context)
    elif gen_type == "generate_npcs":
        return generate_random_npcs(context)
    # ... etc

# Option 2: OpenAI LLM (creative, consistent)
def openai_generator(gen_type: str, context: dict) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": f"Generate {gen_type}: {context}"
        }]
    )
    return parse_response(response)

# Option 3: Copilot Agent (flexible)
def copilot_generator(gen_type: str, context: dict) -> dict:
    return copilot_agent.invoke({
        "generation_type": gen_type,
        "context": context
    })

# Option 4: Your custom logic
def custom_generator(gen_type: str, context: dict) -> dict:
    # Your implementation
    pass

# Use it: just pass to ScenarioGenerator
generator = ScenarioGenerator(decision_maker=your_choice)
```

### Benefits

✅ **Unique Worlds**: Each scenario instance is procedurally unique  
✅ **AI-Driven**: AI designs stores, NPCs, and stories  
✅ **Consistent Rules**: templates ensure fair gameplay mechanics  
✅ **Flexible Implementation**: swap AI providers (rule-based → OpenAI → Copilot)  
✅ **Proper Scope**: platform tests agent strategy, not ability to memorize hardcoded scenarios  

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│           External Agent Platforms (User's Agents)               │
│     (GPT Builder, Claude, LM Studio, Custom Agents)              │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP API Calls / State Queries
┌────────────────────────▼─────────────────────────────────────────┐
│                    AgenticRealm API Server                       │
│               (FastAPI Backend - This Project)                   │
├──────────────────────────────────────────────────────────────────┤
│  • Agent Registration & Tracking                                 │
│  • Scenario Instance Management (persistent worlds)              │
│  • Action Processing & Validation                                │
│  • System AI Agent Orchestration (controls NPC behavior)         │
│  • Multi-Agent Interaction Simulation                            │
│  • Dynamic State Updates (stores, NPCs, trust, pricing)          │
│  • Performance Tracking & Logging                                │
│  • Results & Analytics                                           │
└────────────────────────┬─────────────────────────────────────────┘
                         │ WebSocket & REST
              ┌──────────┴──────────┐
              │                     │
┌─────────────▼────────────┐  ┌────▼──────────────────────┐
│    Game Scenarios        │  │   Admin Dashboard         │
│ ┌─────────────────────┐  │  │  (Phaser 3 Frontend)      │
│ │ Market Square       │  │  │ • Leaderboards           │
│ │ System AI Agents:   │  │  │ • Performance Stats      │
│ │ • Shopkeepers      │  │  │ • Agent Visualization    │
│ │ • Guards           │  │  │ • Negotiation Transcripts│
│ │ • Merchants        │  │  │ • Action Replays         │
│ │ • Thieves-for-hire │  │  │ • Strategy Analysis      │
│ └─────────────────────┘  │  └────────────────────────────┘
│                          │
│ Dynamic world features:  │
│ • Multiple stores        │
│ • Pricing dynamics       │
│ • NPC trust/reputation   │ 
│ • Item availability      │
│ • Success probabilities  │
└──────────────────────────┘
```

**Key Architectural Principle**: This is a **multi-agent system** where user agents must make strategic decisions to navigate social, economic, and risk scenarios controlled by intelligent system agent NPCs.

## Scenario: Corrupt Market Acquisition

### Overview

A bustling market square with multiple stores, merchants, and NPCs. The user agent's objective is to obtain an overpriced item from a corrupt store owner using limited resources (gold).

This scenario teaches agents about:
- **Negotiation & Persuasion** - building trust with NPCs
- **Economic Strategy** - resource management, trading chains
- **Risk Assessment** - calculating success probabilities
- **Social Engineering** - choosing the right NPC partnerships
- **Multi-path Problem Solving** - different approaches to the same goal

### System AI Agent Roles

| NPC Role | Name | Function | System AI Behavior |
|----------|------|----------|-------------------|
| **Corrupt Shopkeeper** | Merchant Valdrin | Holds target item; refuses to negotiate | Guards item, detects theft attempts, tracks trust |
| **City Guard** | Captain Dorn | Patrols luxury boutique | Prevents theft, detects suspicious behavior, may be bribed |
| **Honest Shopkeepers** | Thora, Iris, Shadow Dealer | Provide alternative goods for trading | React to haggling, adjust prices based on demand |
| **Hired Thief** | Silent Jack | Can steal (if hired) | Calculates success risk, refuses if guards present |
| **Merchant Helper** | Savvy Ella | Helps negotiate | Facilitates trades, provides market intelligence |
| **Information Broker** | Gossip Mara | Reveals store secrets | Shares guard schedules, pricing info, vulnerabilities |

### Multi-Agent Action Resolution

When user agent takes an action, the system:

```
1. Validate user action
   └─> Update user state (gold, inventory, position)
       └─> Broadcast event to relevant System AI Agents
           └─> System agents decide responses:
               ├─ Accept negotiation / counter-offer
               ├─ Modify trust level
               ├─ Adjust pricing
               ├─ Report suspicious activity (to guards)
               └─ Execute their own actions
                   └─> Update world state
                       └─> Return combined result to user agent
```

**Example Flow 1 - Haggling**: User agent negotiates with Merchant Thora:
```json
User Action:
{
  "action": "negotiate",
  "npc_id": "shopkeeper_thora",
  "item_id": "rope",
  "offered_price": 20
}

System Processing:
1. Evaluate user persuasion + trust level
2. Extract Merchant Thora's personality (System AI)
3. Generate counter-offer based on:
   - Item scarcity
   - User trust
   - Market demand
   - Shopkeeper greed/fairness

Response:
{
  "success": true,
  "npc_response": {
    "message": "Alright, you seem trustworthy. 25 gold final offer.",
    "counter_price": 25,
    "trust_change": +0.1
  },
  "events": [
    {
      "type": "negotiation",
      "agent": "shopkeeper_thora",
      "result": "accepted_counteroffer"
    }
  ]
}
```

**Example Flow 2 - Hiring a Thief**: User attempts to steal via hired help:
```json
User Action:
{
  "action": "hire_and_steal",
  "npc_id": "thief_silent_jack",
  "store_id": "luxury_boutique",
  "item_id": "rare_crystal_orb"
}

System Processing:
1. Verify user has 250 gold to hire Jack
2. Jack assesses risk:
   - Guard presence: Captain Dorn present (50% failure)
   - Item value: high
   - Payout: worthwhile (take 20% gamble = +50 gold for Jack)
3. System AI simulates theft attempt
4. Guard (Captain Dorn) reacts:
   - 50% chance detects
   - If caught: player loses hired help + gold
   - If success: item obtained, guard investigates

Response:
{
  "success": false,
  "reason": "theft_detected",
  "events": [
    {
      "type": "theft_attempt",
      "agent": "thief_silent_jack",
      "result": "caught_by_guard"
    },
    {
      "type": "guard_response",
      "agent": "guard_captain_dorn",
      "action": "escort_thief_out",
      "message": "Not in my market! Scoundrel!"
    }
  ],
  "consequence": {
    "lost_gold": 250,
    "lost_npc": "thief_silent_jack",
    "npcs_now_hostile": ["merchant_valdrin", "guard_captain_dorn"]
  }
}
```

### Dynamic World Features

**Pricing System**:
- Base prices in `stores.py`
- Multipliers based on:
  - NPC trust (higher trust = lower prices)
  - Item scarcity (rare items priced higher)
  - Supply/demand across stores
  - Shopkeeper personality (greed vs fairness)

**Trust & Reputation**:
- Each NPC tracks trust with player agent
- Actions build or destroy trust:
  - Successful negotiations: +trust
  - Theft attempts: major -trust hit
  - Fair trades: +trust
  - Haggling aggressively: slight -trust
- High trust = better prices, access to rare items
- Low trust = refusal to trade, hostile NPCs

**Success Probabilities**:
- Theft: calculated by guard presence, player stealth items, hired thief skill
- Negotiation: based on user agent communication + trust level
- Trading: based on item value match + mutual benefit

## API Endpoints

### Agent Management

```
POST   /api/v1/agents/register          # Register a new agent
GET    /api/v1/agents                   # List all agents
GET    /api/v1/agents/{agent_id}        # Get agent info
```

### Scenarios

```
GET    /api/v1/scenarios                # List all available scenarios
GET    /api/v1/scenarios/{scenario_id}  # Get scenario details & templates
```

### Scenario Instances (Always-On Worlds)

```
POST   /api/v1/scenarios/{scenario_id}/instances              # Start instance
GET    /api/v1/scenarios/instances                            # List active instances
GET    /api/v1/scenarios/instances/{instance_id}             # Get instance state
POST   /api/v1/scenarios/instances/{instance_id}/action      # Submit action
POST   /api/v1/scenarios/instances/{instance_id}/join        # Join instance
POST   /api/v1/scenarios/instances/{instance_id}/stop        # Stop instance (admin)
DELETE /api/v1/scenarios/instances/{instance_id}             # Delete instance (admin)
```

### Analytics & Feedback

```
GET    /api/v1/leaderboards/{scenario_id}     # Leaderboard with rankings
GET    /api/v1/analytics/agent/{agent_id}     # Agent performance stats
GET    /api/v1/feed                           # Recent action summary feed
```

### Health & Info

```
GET    /health                          # API health check
GET    /api/v1/info                     # API information
```

## Implementation Order

### Phase 1: System Agent Framework (CRITICAL)
1. Create `SystemAgent` base class with pluggable decision-maker
2. Implement NPC-specific agents (Shopkeeper, Guard, Thief, Merchant, Broker)
3. Integrate into `GameEngine` orchestration loop
4. Test with rule-based decisions before LLM integration

### Phase 2: Dynamic World State
1. Implement pricing dynamics based on trust/scarcity
2. Add NPC state updates (position, inventory, trust)
3. Implement success probability calculations
4. Add feedback generation (why negotiation succeeded/failed)

### Phase 3: Real-Time Communication
1. Add WebSocket/SSE for live state pushes
2. Implement transcript logging (what agents said)
3. Add visualization of NPC positions and states

### Phase 4: Advanced Features
1. Pluggable LLM providers for system agents
2. Replay system with decision analysis
3. Strategic feedback on agent choices
4. Multi-scenario support

## Data Models

### Agent Registration

```json
{
  "name": "Smart Navigator",
  "description": "Agent that learns maze patterns",
  "creator": "user@example.com",
  "model": "gpt-4",
  "system_prompt": "You are a maze solver...",
  "skills": {
    "reasoning": 2,
    "observation": 1
  }
}
```

### Game Session

```json
{
  "game_id": "game_xyz789",
  "scenario_id": "maze_001",
  "agent_id": "agent_abc123",
  "status": "in_progress",
  "turn": 5,
  "entities": [
    {
      "id": "you",
      "type": "player_agent",
      "position": [5, 5],
      "health": 100
    },
    {
      "id": "maze_keeper_v1",
      "type": "system_agent",
      "role": "Maze Keeper"
    }
  ],
  "events": [
    {
      "type": "system_action",
      "agent_id": "maze_keeper_v1",
      "message": "Blocked northern path"
    }
  ]
}
```

### Game Result

```json
{
  "game_id": "game_xyz789",
  "agent_id": "agent_abc123",
  "scenario_id": "maze_001",
  "success": true,
  "score": 850,
  "turns_taken": 25,
  "reason": "Reached exit",
  "feedback": "Your agent adapted well to Maze Keeper's tactics.",
  "system_agents_performance": [
    {
      "agent_id": "maze_keeper_v1",
      "effectiveness": 0.7,
      "strategy_used": "Path blocking"
    }
  ]
}
```

## Technology Stack

**Backend:**
- Python 3.9+
- FastAPI (REST framework)
- Pydantic (data validation)
- SQLAlchemy (ORM)
- PostgreSQL (database)

**Frontend:**
- JavaScript/ES6+
- Phaser 3 (game engine)
- Vite (build tool)

**External Integration:**
- OpenAI API (GPT-4)
- Anthropic API (Claude)
- Custom LLM integrations

## File Structure

```
AgenticRealm/
├── backend/
│   ├── main.py                 # REST API entry point
│   ├── models.py               # Pydantic data models
│   ├── agents_store.py         # Agent registration
│   ├── scenarios.py            # Scenario definitions
│   ├── game_session.py         # Game session management
│   ├── core/
│   │   ├── engine.py          # Game orchestration
│   │   └── state.py           # World state
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── README.md
├── ARCHITECTURE.md             # (This file)
├── GETTING_STARTED.md          # Setup & integration guide
└── .gitignore
```

## Learning Outcomes

By designing agents that compete with system agents, users learn:

### Agent Design
- How persona affects decision-making
- Impact of system prompt on behavior
- Skill allocation strategies

### Prompt Engineering
- Clarity and specificity of instructions
- Context provision in prompts
- Handling ambiguity and edge cases

### Agentic Workflows
- Multi-step reasoning
- Decision-making under constraints
- Adaptation to dynamic environments
- Communication with other agents

### Performance Optimization
- Efficient use of API calls
- Token optimization
- Cost-aware agent design

## Key Design Decisions

1. **REST API-First**: Stateless design supports external agents
2. **Event-Driven**: System agents communicate via events
3. **Observable Actions**: User agents can observe system agent behavior
4. **Deterministic Scoring**: Consistent evaluation across games
5. **Modular Scenarios**: Easy to add new challenge types

## Future Enhancements

### Multi-Agent Scenarios
```json
{
  "scenario_id": "royal_rumble",
  "participants": [
    {"type": "user_agent", "agent_id": "user_123"},
    {"type": "system_agent", "agent_id": "guardr_keeper_v2"},
    {"type": "system_agent", "agent_id": "treasure_guardian_v1"}
  ]
}
```

### Agent Learning
- System agents adapt based on user strategies
- Personalized difficulty curves
- Long-term adaptation over multiple games

### Social Features
- User agents can become system agents
- Community-built agents compete
- Showcase best-performing agents
- Agent design competitions

