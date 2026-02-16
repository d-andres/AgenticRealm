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

// Socket.IO event listeners
socket.on('connect', () => {
    console.log('Connected to backend');
});

socket.on('state_update', (state) => {
    console.log('State update received:', state);
    // Update game entities based on state
});

socket.on('disconnect', () => {
    console.log('Disconnected from backend');
});

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
            gravity: { y: 300 },
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

export { socket, game };
