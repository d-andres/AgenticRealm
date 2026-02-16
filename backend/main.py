"""
AgenticRealm Backend - FastAPI + Socket.IO Entry Point

The main orchestrator that manages connections to the Agentic AI System.
Handles WebSocket communication between the frontend and the AI orchestration engine.
"""

from fastapi import FastAPI, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
import asyncio
from dotenv import load_dotenv

from core.engine import GameEngine
from core.state import GameState

# Load environment variables
load_dotenv()

# Initialize FastAPI and Socket.IO
app = FastAPI(title="AgenticRealm Backend")
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize game engine and state
game_engine = GameEngine()
game_state = GameState()

# Socket.IO events
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")

@sio.event
async def player_action(sid, data):
    """
    Handle player action from frontend
    
    Expected data:
    {
        "action": "move",
        "params": {...}
    }
    """
    print(f"Player action from {sid}: {data}")
    # Process action through game engine
    # await game_engine.process_action(sid, data)

@sio.event
async def request_state(sid):
    """Send current game state to client"""
    state = game_state.to_dict()
    await sio.emit('state_update', state, to=sid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
