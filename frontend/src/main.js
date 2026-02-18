/**
 * AgenticRealm Frontend - Main Phaser Configuration & Socket.IO Setup
 * 
 * The main entry point for the game frontend.
 * Initializes Phaser game engine and establishes WebSocket connection to backend.
 */

import Phaser from 'phaser';
import io from 'socket.io-client';

// Initialize Socket.IO connection
const socket = io('http://localhost:8000');

// Game state
let gameState = {
    entities: {},
    turn: 0
};

// Socket.IO event listeners
socket.on('connect', () => {
    console.log('[Socket] Connected to backend');
    updateConnectionStatus(true);
});

socket.on('state_update', (state) => {
    console.log('[Socket] State update:', state);
    gameState = state;
    updateGameEntities(state);
});

socket.on('agent_created', (data) => {
    console.log('[Socket] Agent created:', data);
});

socket.on('game_started', (data) => {
    console.log('[Socket] Game started, turn:', data.turn);
});

socket.on('game_stopped', () => {
    console.log('[Socket] Game stopped');
});

socket.on('error', (data) => {
    console.error('[Socket] Error:', data.message);
});

socket.on('disconnect', () => {
    console.log('[Socket] Disconnected from backend');
    updateConnectionStatus(false);
});

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (statusEl) {
        statusEl.textContent = connected ? '● Connected' : '● Disconnected';
        statusEl.className = connected ? 'status-connected' : 'status-disconnected';
    }
}

/**
 * Update game entities on screen
 */
function updateGameEntities(state) {
    // This will be implemented when rendering is added
    console.log(`[Game] Updated ${Object.keys(state.entities).length} entities`);
}

/**
 * Phaser Game Configuration
 */
const config = {
    type: Phaser.AUTO,
    width: 1280,
    height: 720,
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scene: [
        // Import scenes here
        // new BootScene(),
        // new LobbyScene(),
        // new DungeonScene()
    ],
    render: {
        pixelArt: true,
        antialias: false
    }
};

/**
 * Game Instance
 */
const game = new Phaser.Game(config);

/**
 * Create an agent
 */
export function createAgent(name, persona, skills) {
    socket.emit('create_agent', {
        name: name,
        persona: persona,
        skills: skills
    });
}

/**
 * Helper function to send actions to backend
 */
export function sendAction(action, params = {}) {
    socket.emit('player_action', {
        action: action,
        params: params,
        timestamp: Date.now()
    });
}

/**
 * Helper function to request state update
 */
export function requestState() {
    socket.emit('request_state');
}

/**
 * Start the game simulation
 */
export function startGame() {
    socket.emit('start_game');
}

/**
 * Stop the game simulation
 */
export function stopGame() {
    socket.emit('stop_game');
}

export { socket, game, gameState };
