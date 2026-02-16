# AgenticRealm

An educational platform for designing and testing AI agents in an interactive simulation environment. Users create custom AI agents that navigate challenges, solve puzzles, and interact with a dynamic world.

## Project Overview

**AgenticRealm** is an agentic AI system that combines:
- **Backend Orchestration Engine** (Python/FastAPI) - Manages agents, world state, and game rules
- **Interactive Game Frontend** (JavaScript/Phaser) - Real-time visualization and interaction
- **AI Agent Framework** - Support for LLM-powered, script-based, or custom ML agents
- **Physics & Rules Engine** - Environment logic, traps, and win/lose conditions

Perfect for educational purposes, research, and experimentation with AI decision-making.

## Features

✨ **Agent Creation**
- Design AI agents with custom logic
- Support for multiple AI backends (LLM, Python scripts, custom models)
- Skill-based agent system with validation

🎮 **Interactive Simulation**
- Real-time multiplayer simulation environment
- Dynamic world state with entities and physics
- Trap systems and environmental challenges

🧠 **Flexible Agent Logic**
- LLM-powered agents (OpenAI, Claude, Gemini, Azure)
- Script-based agent controllers
- ML model integration framework

📊 **Observation & Analysis**
- Full action history and perception logs
- Real-time state synchronization via WebSocket
- Event-based world updates

## Tech Stack

**Backend:**
- Python 3.9+
- FastAPI (web framework)
- Socket.IO (real-time communication)
- Pydantic (data validation)

**Frontend:**
- JavaScript/ES6+
- Phaser 3 (2D game engine)
- Socket.IO Client (WebSocket)
- Vite (build tooling)

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16+ and npm
- Git

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AgenticRealm
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Configure Environment**
   ```bash
   # In the project root, edit .env with your API keys
   cp .env.example .env
   # Add your LLM provider API keys to .env
   ```

### Running the Application

**Terminal 1 - Start Backend Server:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

Backend will be available at `http://localhost:8000`

**Terminal 2 - Start Frontend Dev Server:**
```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

Open your browser and navigate to `http://localhost:5173` to interact with the simulation.

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed information about the project structure and components.

```
AgenticRealm/
├── backend/                    # Python/FastAPI backend
│   ├── main.py                # Server entry point
│   ├── core/                  # Core game engine
│   │   ├── engine.py         # Orchestration engine
│   │   └── state.py          # World state management
│   ├── agents/                # Agent implementations
│   │   ├── registrar.py      # Agent registration
│   │   ├── user_agent.py     # User agent logic
│   │   └── judge.py          # Environment rules
│   ├── prompts/               # System prompts
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # JavaScript/Phaser frontend
│   ├── src/
│   │   ├── main.js           # Game setup & Socket.IO
│   │   ├── scenes/           # Game scenes
│   │   └── sprites/          # Entity classes
│   ├── public/assets/         # Game assets
│   ├── index.html
│   ├── package.json
│   └── vite.config.js        # Build configuration
│
├── assets/                     # Raw design files (Tiled maps, etc.)
├── .env                        # Configuration (API keys, settings)
├── README.md                   # This file
└── ARCHITECTURE.md            # Detailed architecture documentation
```

## Core Concepts

### Game Engine
The orchestration engine (`backend/core/engine.py`) manages:
- Agent registration and lifecycle
- Simulation tick loop
- Action processing and validation
- State synchronization with clients

### World State
Authoritative game state (`backend/core/state.py`) tracks:
- All entities (agents, NPCs, obstacles)
- Environmental properties
- Event history
- Turn counter and progression

### Agents
Three types of agent implementations available:

1. **LLM-Based Agents** - Use language models for decision-making
2. **Script-Based Agents** - User-written Python controllers
3. **Custom Logic** - Arbitrary decision-making systems

### Judge System
Environment rules enforcer (`backend/agents/judge.py`):
- Movement validation
- Collision detection
- Trap mechanics
- Win/lose condition checking

## Creating Your First Agent

### Example: LLM-Powered Agent

```python
from backend.agents.user_agent import UserAgent, LLMAgentLogic

# Create agent logic
logic = LLMAgentLogic(
    llm_provider='openai',
    model='gpt-4',
    system_prompt='You are a clever dungeon explorer...'
)

# Create agent
agent = UserAgent('player_1', logic)
```

### Example: Script-Based Agent

```python
from backend.agents.user_agent import UserAgent, ScriptAgentLogic

script = """
def decide_action(perception):
    # Your custom logic here
    return {
        'type': 'move',
        'direction': 'forward'
    }
"""

logic = ScriptAgentLogic(script)
agent = UserAgent('player_1', logic)
```

## API Documentation

### Socket.IO Events

**Client → Server:**
- `connect` - Client connects to server
- `player_action` - Send action for processing
- `request_state` - Request current game state

**Server → Client:**
- `state_update` - World state changed
- `action_result` - Result of player action
- `game_event` - Significant game event occurred

## Configuration

Edit `.env` to customize:

```env
# Backend
BACKEND_HOST=localhost
BACKEND_PORT=8000

# Frontend
FRONTEND_HOST=localhost
FRONTEND_PORT=5173

# LLM Providers (choose one or more)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Simulation
TICK_RATE=1.0
MAX_AGENTS=10
WORLD_WIDTH=800
WORLD_HEIGHT=600
```

## Development

### Adding Components

**New Game Scene:**
1. Create class extending `GameScene` in `frontend/src/scenes/scenes.js`
2. Register in Phaser config
3. Implement `create()` and `update()` methods

**New Agent Type:**
1. Extend `BaseAgentLogic` in `backend/agents/user_agent.py`
2. Implement `decide_action()` method
3. Register through `AgentRegistrar`

**System Prompts:**
Add `.txt` files to `backend/prompts/` for complex LLM instructions.

## Troubleshooting

**Backend connection fails:**
- Ensure backend is running on `http://localhost:8000`
- Check firewall/CORS settings
- Verify `.env` configuration

**Assets not loading:**
- Ensure asset files exist in `frontend/public/assets/`
- Check browser console for specific missing files
- Run `npm run build` to validate asset paths

**Agent registration fails:**
- Check skill requirements in `backend/agents/registrar.py`
- Verify agent data structure matches expected format
- Review logs for validation errors

## Contributing

Contributions welcome! Areas for enhancement:
- Additional agent types and examples
- Advanced physics simulation
- Multiplayer agent coordination
- Persistence and replay systems
- Admin dashboard for monitoring

## Roadmap

- [ ] Multi-agent collaboration scenarios
- [ ] Complex environment scripting system
- [ ] Agent training playground
- [ ] Replay and analysis tools
- [ ] Web-based agent editor
- [ ] Performance metrics dashboard

## License

See [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or ideas:
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details
- Review example agents in `backend/agents/`
- Check implementation status in [Roadmap](#roadmap)

---

**Happy agent designing! 🚀**
