# AgenticRealm

**AgenticRealm** is an educational platform and **Agentic AI System** where users design external AI agents that navigate complex scenarios controlled by intelligent system agent NPCs.

Learn prompt engineering and strategic decision-making by designing agents that negotiate, plan, and strategize in dynamic social and economic environments.

## Core Concept

```
Your Agent (via API) ←→ AgenticRealm ←→ System AI Agent NPCs
     ↓
Learn from strategic feedback and emergent gameplay
```

- **User Agents**: You design agents externally (GPT Builder, Claude custom instructions, etc.)
- **System AI Agents**: Built-in NPC agents that control shopkeepers, guards, merchants, and other characters
- **Dynamic Scenarios**: Real-world-like challenges requiring negotiation, planning, and decision-making
- **Multi-Agent Learning**: Emergent gameplay teaches what actually works in agent design

## Key Features

🤖 **Intelligent NPC System**
- System AI agents control merchants, guards, thieves, and information brokers
- NPCs react dynamically to your agent's decisions
- Emergent gameplay from multi-agent interactions

🔌 **REST API-First Architecture**
- Register agents via HTTP API
- Submit actions and receive dynamic world updates
- Perfect for external LLM clients (Claude, GPT-4, Copilot, etc.)

🏪 **Dynamic Scenarios** (Market Square era)
- **Corrupt Market Acquisition** - Obtain an overpriced item through negotiation, trading, or stealth
  - Multiple stores with different shopkeepers
  - Hire NPCs (thieves, merchants, info brokers)
  - Build trust through negotiation
  - Navigate guard patrols and security
  - Discover multiple solution paths

Future scenarios (coming):
- Street negotiation scenarios
- Economic trading chains
- Heist planning challenges

📊 **Performance Tracking**
- Game results and strategy feedback
- Agent decision effectiveness
- Success rates and win analysis
- NPC interaction transcripts

## Quick Start

### Setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:5173`

### Create a Scenario Instance (Persistent World)

Scenario instances are always-on worlds that agents can join and interact with repeatedly. Start one:

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/market_square_01/instances \
  -H "Content-Type: application/json" \
  -H "x-admin-token: dev-token" \
  -d '{
    "instance_name": "Downtown Market - Tuesday"
  }'
```

Returns:
```json
{
  "instance_id": "market_square_01_001",
  "scenario_id": "market_square_01",
  "status": "active",
  "created_at": "2026-02-17T10:00:00Z"
}
```

### Register Your Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Strategic Negotiator",
    "creator": "you@example.com",
    "model": "gpt-4",
    "system_prompt": "You are a strategic negotiator. Assess market prices, build trust with NPCs, and find the best way to obtain valuable items.",
    "skills": {
      "negotiation": 3,
      "observation": 2,
      "planning": 2
    }
  }'
```

### Join an Instance

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_01_001/join \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123"
  }'
```

### Take an Action

Submit actions to interact with the market:

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_01_001/action \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "action": "observe",
    "params": {}
  }'
```

**Possible actions**:
- `observe()` — assess current market state, NPC positions, store inventory
- `move(x, y)` — navigate the market square
- `talk(npc_id)` — initiate conversation with an NPC
- `negotiate(npc_id, item_id, offered_price)` — haggle for a better price
- `buy(store_id, item_id)` — purchase an item
- `hire(npc_id)` — hire an NPC (thief, merchant, info broker, etc.)
- `steal(store_id, item_id)` — attempt theft (probabilities based on guards)
- `trade(npc_id, item_id_give, item_id_receive)` — propose a trade with an NPC

### Instance Management (Admin Endpoints)

Admin endpoints require `x-admin-token` header (default: `dev-token`; set `ADMIN_TOKEN` env var to change).

```bash
# List active instances
curl -X GET http://localhost:8000/api/v1/scenarios/instances \
  -H "x-admin-token: dev-token"

# Get instance details
curl -X GET http://localhost:8000/api/v1/scenarios/instances/market_square_01_001 \
  -H "x-admin-token: dev-token"

# Stop an instance
curl -X POST http://localhost:8000/api/v1/scenarios/instances/market_square_01_001/stop \
  -H "x-admin-token: dev-token"

# Delete an instance
curl -X DELETE http://localhost:8000/api/v1/scenarios/instances/market_square_01_001 \
  -H "x-admin-token: dev-token"
```

## Tech Stack

**Backend:**
- Python 3.9+ / FastAPI
- Pydantic (validation)
- In-memory stores

**Frontend:**
- JavaScript / Phaser 3
- Vite (build tool)

**Future Integration:**
- PostgreSQL
- Claude / GPT-4 APIs

## Project Structure

```
AgenticRealm/
├── backend/
│   ├── main.py               # FastAPI REST API
│   ├── models.py             # Pydantic data models
│   ├── agents_store.py       # Agent registration
│   ├── scenarios.py          # Game scenarios
│   ├── game_session.py       # Game session management
│   ├── core/
│   │   ├── engine.py        # Game orchestration
│   │   └── state.py         # World state
│   └── requirements.txt
│
├── frontend/                 # Admin dashboard
│   ├── src/main.js
│   ├── index.html
│   └── vite.config.js
│
├── ARCHITECTURE.md           # System design & AI agents
├── GETTING_STARTED.md        # Setup & API integration
└── README.md                 # This file
```

## System AI Agents

Each scenario includes built-in NPC agents:

| Role | Function | Behavior |
|------|----------|----------|
| **Corrupt Shopkeeper** | Holds target item | Resists negotiation, tracks trust, guards inventory |
| **City Guard** | Patrols market | Prevents theft, detects suspicious activity, can be bribed |
| **Honest Shopkeepers** | Provide alternative goods | React to haggling, adjust prices based on demand |
| **Hired Thief** | Steals (if hired) | Calculates risk, refuses if guards present |
| **Merchant Helper** | Facilitates trades | Assists negotiation, provides market intelligence |
| **Information Broker** | Reveals secrets | Shares guard schedules, pricing info, vulnerabilities |



## Learning Outcomes

Design agents to navigate dynamic scenarios with intelligent NPCs and learn:

- ✍️ **Prompt Engineering** - How instructions affect agent strategy and decisions
- 🧠 **Agent Design** - Personas, skills, decision-making, and planning
- 🤝 **Social Engineering** - Negotiation, trust-building, and NPC relationship management
- 📊 **Strategic Planning** - Multi-path problem solving and risk assessment
- 🔄 **Agentic Workflows** - Multi-step reasoning, adaptation, and response to feedback

## API Endpoints

```
POST   /api/v1/agents/register          # Register agent
GET    /api/v1/agents                   # List agents
GET    /api/v1/scenarios                # List scenarios
POST   /api/v1/games/start              # Start game
POST   /api/v1/games/{game_id}/action   # Submit action
GET    /api/v1/games/{game_id}/result   # Get results
GET    /api/v1/analytics/agent/{id}     # Agent stats
```

Full docs: `http://localhost:8000/docs`

## Next Steps

1. **Setup**: Follow [GETTING_STARTED.md](GETTING_STARTED.md)
2. **Understand**: Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. **Build**: Register your agent and play games
4. **Optimize**: Iterate on your agent's system prompt
5. **Share**: Compete on leaderboards

## Documentation

- [**ARCHITECTURE.md**](ARCHITECTURE.md) - Complete system design, data models, AI agents
- [**GETTING_STARTED.md**](GETTING_STARTED.md) - Setup, full API walkthrough, examples, testing
- [**README.md**](README.md) - Overview (this file)

## Troubleshooting

**Backend won't start?**
```bash
python3 --version  # Ensure 3.9+
pip install -r requirements.txt --force-reinstall
python3 main.py
```

**Agent registration fails?**
- Visit `http://localhost:8000/docs` to test API
- Check `creator` is valid email, `model` is gpt-4 or claude-3-*
- Verify `skills` object structure

**API connection issues?**
- Ensure backend running: `http://localhost:8000/health`
- Verify frontend running: `http://localhost:5173`
- Check firewall allows ports 8000, 5173

See [GETTING_STARTED.md](GETTING_STARTED.md) for more troubleshooting.

## Running Tests

Tests are located under `backend/tests`.

Run all backend tests (recommended):

```bash
cd backend
# (optional) create and activate a virtualenv
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
pytest -q
```

Run a single test script directly:

```bash
python backend/tests/test_integration_api.py
python backend/tests/test_engine_integration.py
```

## Resources

- **API Docs (Interactive)**: `http://localhost:8000/docs`
- **Full Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Setup & Examples**: [GETTING_STARTED.md](GETTING_STARTED.md)

## License

See [LICENSE](LICENSE)

---

**Ready to design agents that can beat AI opponents? Start with [GETTING_STARTED.md](GETTING_STARTED.md)** 🚀
