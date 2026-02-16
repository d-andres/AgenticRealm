/**
 * Scenes - Game Levels and Stages
 * 
 * Boot Scene - Initialization and loading
 * Lobby Scene - Character creation and agent setup
 * Game Scenes - Actual gameplay levels/dungeons
 */

import Phaser from 'phaser';

/**
 * Boot Scene - Initial setup and asset loading
 */
export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }
    
    preload() {
        // Load assets
        // this.load.image('player', 'assets/sprites/player.png');
        // this.load.image('spike', 'assets/sprites/trap_spike.png');
        console.log('BootScene: Loading assets...');
    }
    
    create() {
        console.log('BootScene: Assets loaded, starting lobby');
        this.scene.start('LobbyScene');
    }
}

/**
 * Lobby Scene - Character creation and agent selection
 */
export class LobbyScene extends Phaser.Scene {
    constructor() {
        super({ key: 'LobbyScene' });
    }
    
    create() {
        this.cameras.main.setBackgroundColor('#222222');
        
        // Title
        this.add.text(640, 100, 'AgenticRealm', {
            fontSize: '48px',
            fill: '#ffffff'
        }).setOrigin(0.5);
        
        // Create agent button
        const createBtn = this.add.rectangle(640, 350, 200, 60, 0x4444ff)
            .setInteractive()
            .on('pointerdown', () => this.startGameWithAgent());
        
        this.add.text(640, 350, 'Create Agent', {
            fontSize: '24px',
            fill: '#ffffff'
        }).setOrigin(0.5);
        
        // Instructions
        this.add.text(640, 500, 'Design your AI agent and dive into the simulation!', {
            fontSize: '16px',
            fill: '#cccccc'
        }).setOrigin(0.5);
    }
    
    startGameWithAgent() {
        // TODO: Show agent creation dialog or form
        console.log('Starting game with agent...');
        // this.scene.start('DungeonScene');
    }
}

/**
 * Game Scene - Base class for gameplay scenes
 */
export class GameScene extends Phaser.Scene {
    constructor(key) {
        super({ key });
        this.cursors = null;
        this.player = null;
    }
    
    create() {
        this.cameras.main.setBackgroundColor('#1a1a2e');
        
        // Input handling
        this.cursors = this.input.keyboard.createCursorKeys();
        
        // Create tilemap if available
        // const map = this.make.tilemap({ key: 'map' });
        // const tileset = map.addTilesetImage('tileset');
    }
    
    update() {
        if (!this.player) return;
        
        // Handle player input
        if (this.cursors.left.isDown) {
            this.player.move('left');
        } else if (this.cursors.right.isDown) {
            this.player.move('right');
        } else if (this.cursors.up.isDown) {
            this.player.move('up');
        } else if (this.cursors.down.isDown) {
            this.player.move('down');
        }
    }
}

/**
 * Dungeon Scene - Main gameplay level
 */
export class DungeonScene extends GameScene {
    constructor() {
        super({ key: 'DungeonScene' });
    }
    
    create() {
        super.create();
        
        // Load tilemap
        // const map = this.make.tilemap({ key: 'dungeon' });
        // const tileset = map.addTilesetImage('dungeon_tileset');
        // const groundLayer = map.createLayer('Ground', tileset);
        
        // Create player
        // this.player = new PlayerSprite(this, 100, 100);
        
        // Create NPCs and traps
        // TODO: Create entities based on server state
        
        console.log('DungeonScene: Ready for gameplay');
    }
}

export { BootScene, LobbyScene, GameScene, DungeonScene };
