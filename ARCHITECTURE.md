# AgenticRealm Project Structure

This directory contains the starter structure for the AgenticRealm project - an Agentic AI system and simulation for educational learning.

## Architecture

- **Backend (`/backend`)**: The orchestration engine (Python + FastAPI + Socket.IO)
- **Frontend (`/frontend`)**: The game interface (JavaScript + Phaser.io)
- **Assets (`/assets`)**: Raw design files and resources (Tiled maps, etc.)

## Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend server will start on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available on `http://localhost:5173`

## Project Structure Details

### Backend

```
backend/
├── main.py              # FastAPI entry point with Socket.IO
├── requirements.txt     # Python dependencies
├── core/
│   ├── engine.py       # Game orchestration engine
│   └── state.py        # World state management
├── agents/
│   ├── registrar.py    # Agent registration & validation
│   ├── user_agent.py   # User-designed agent logic
│   └── judge.py        # Environment rules & physics
└── prompts/            # System prompts for LLM agents
```

### Frontend

```
frontend/
├── src/
│   ├── main.js         # Phaser & Socket.IO setup
│   ├── scenes/         # Game scenes (Lobby, Dungeons, etc.)
│   └── sprites/        # Entity classes (Player, NPC, Traps)
├── public/
│   └── assets/         # Game sprites, tilesets, etc.
├── index.html
└── package.json
```

## Key Components

### Backend Components

- **GameEngine**: Orchestrates the simulation loop, manages agents, processes actions
- **GameState**: Maintains authoritative world state
- **AgentRegistrar**: Handles agent registration and skill validation
- **UserAgent**: Represents user-designed AI agents (LLM-powered, script-based, etc.)
- **Judge**: Enforces world rules, physics, and win/lose conditions

### Frontend Components

- **Phaser Game**: 2D game engine for rendering and interaction
- **Socket.IO Client**: Real-time communication with backend
- **Game Scenes**: Lobby, gameplay levels, UI
- **Sprites**: Player character, NPCs, environmental hazards

## Configuration

Edit `.env` to configure:
- Backend/Frontend hosts and ports
- LLM provider API keys (OpenAI, Claude, Gemini, Azure)
- Simulation parameters (tick rate, world size, max agents)
- Logging level

## Development

### Adding a New Scene

1. Create a new class extending `GameScene` in `frontend/src/scenes/scenes.js`
2. Register it in the Phaser config in `frontend/src/main.js`
3. Implement `create()` and `update()` methods

### Adding Agent Logic

1. Extend `BaseAgentLogic` in `backend/agents/user_agent.py`
2. Implement the `decide_action()` method
3. Register agents through `/agents/registrar.py`

### Connecting to LLMs

Implementation placeholders exist in `user_agent.py`:
- `LLMAgentLogic` for LLM-powered agents
- Supports: OpenAI, Anthropic, Google, Azure

## Next Steps

- [ ] Implement Vite configuration (`frontend/vite.config.js`)
- [ ] Create tilemap assets and load them in scenes
- [ ] Implement LLM integration for agent decision-making
- [ ] Add websocket event handlers for state synchronization
- [ ] Implement collision detection and trap mechanics
- [ ] Create agent creation UI in the Lobby scene
- [ ] Add animation and visual feedback systems
- [ ] Implement persistence (database for agent logs, results)

## Resources

- [Phaser Documentation](https://phaser.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Socket.IO Documentation](https://socket.io/docs/)
- [Tiled Map Editor](https://www.mapeditor.org/)
