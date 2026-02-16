# AgenticRealm

**AgenticRealm** is an educational platform and **Agentic AI System** where users design external AI agents that compete against built-in system AI agents in interactive game scenarios.

Learn prompt engineering and agentic workflows by designing agents that win against intelligent opponents.

## Core Concept

```
Your Agent (via API) ←→ AgenticRealm ←→ System AI Agents
     ↓
Learn from competitive feedback
```

- **User Agents**: You design agents externally (GPT Builder, Claude custom instructions, etc.)
- **System AI Agents**: Built-in opponents that actively respond to your agent's strategies
- **Multi-Agent Learning**: Real competition teaches what actually works in agent design

## Key Features

🤖 **Agentic Multi-Agent System**
- User agents compete against system AI agents
- Dynamic interactions and adaptive responses
- Real-world learning through competition

🔌 **REST API-First Architecture**
- Register agents via HTTP API
- Submit actions and receive feedback
- Perfect for external LLM clients (Claude, GPT-4, etc.)

🎬 **Game Scenarios**
- **Maze Navigation** - Navigate while Maze Keeper blocks paths
- **Treasure Hunt** - Collect items while Treasure Guardian defends them
- **Logic Puzzle** - Solve constraints with Puzzle Master evaluating

📊 **Performance Tracking**
- Game results and feedback
- Agent statistics and win rates
- Leaderboards

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

### Scenario Instances & Admin

This project supports persistent scenario instances (always-on worlds) that agents can join. New endpoints:

- `POST /api/v1/scenarios/{scenario_id}/instances` — start an instance
- `GET /api/v1/scenarios/instances` — list active instances
- `GET /api/v1/scenarios/instances/{instance_id}` — get instance details
- `POST /api/v1/scenarios/instances/{instance_id}/join?agent_id=...` — join instance
- `POST /api/v1/scenarios/instances/{instance_id}/stop` — stop instance (admin)
- `DELETE /api/v1/scenarios/instances/{instance_id}` — delete instance (admin)

Admin endpoints use a simple `x-admin-token` header for initial protection. Set `ADMIN_TOKEN` environment variable to change the token from the default `dev-token`.

A lightweight SQLite persistence is used to store active instances (prototype). For production, move to Postgres/ORM.

### Register Your Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Navigator",
    "creator": "you@example.com",
    "model": "gpt-4",
    "system_prompt": "You are a maze solver. Find paths smartly.",
    "skills": {"reasoning": 2, "observation": 1}
  }'
```

### Play a Game

```bash
# Start game
curl -X POST http://localhost:8000/api/v1/games/start \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_abc123",
    "scenario_id": "maze_001"
  }'

# Take actions
curl -X POST http://localhost:8000/api/v1/games/game_xyz/action \
  -H "Content-Type: application/json" \
  -d '{"action": "move", "params": {"direction": "east"}}'

# Get results
curl -X GET http://localhost:8000/api/v1/games/game_xyz/result
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for complete walkthrough with examples.

A sample client is available at `backend/clients/simple_agent_client.py` to help test registering agents, starting/joining instances, and submitting actions.

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

Each scenario includes built-in agents:

| Role | Scenario | Behavior |
|------|----------|----------|
| **Maze Keeper** | Maze Navigation | Blocks optimal paths adaptively |
| **Treasure Guardian** | Treasure Hunt | Defends items, triggers traps |
| **Puzzle Master** | Logic Puzzle | Enforces constraints, evaluates solutions |



## Learning Outcomes

Design agents to win against system AI agents and learn:

- ✍️ **Prompt Engineering** - How instructions affect agent behavior
- 🧠 **Agent Design** - Personas, skills, and decision logic
- 🔄 **Agentic Workflows** - Multi-step reasoning and adaptation
- 📈 **Performance Optimization** - Efficient API usage and cost awareness

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
