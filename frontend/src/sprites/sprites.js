/**
 * Sprites - Character and NPC Classes
 * 
 * Base classes for player character and NPC entities
 */

import Phaser from 'phaser';

/**
 * Base Sprite Class
 */
export class GameSprite extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, texture, frame = 0) {
        super(scene, x, y, texture, frame);
        
        scene.add.existing(this);
        scene.physics.add.existing(this);
        
        this.health = 100;
        this.speed = 160;
        this.isMoving = false;
    }
    
    move(direction) {
        // Move sprite based on direction
        // direction: 'up', 'down', 'left', 'right'
        this.isMoving = true;
    }
    
    takeDamage(amount) {
        this.health -= amount;
        if (this.health <= 0) {
            this.destroy();
        }
    }
    
    reset() {
        this.health = 100;
        this.isMoving = false;
    }
}

/**
 * Player Character Class
 */
export class PlayerSprite extends GameSprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');
        
        this.agentId = null;
        this.inventory = [];
        this.skills = {};
    }
    
    setAgent(agentId, skills) {
        this.agentId = agentId;
        this.skills = skills;
    }
    
    addToInventory(item) {
        this.inventory.push(item);
    }
    
    removeFromInventory(itemId) {
        this.inventory = this.inventory.filter(item => item.id !== itemId);
    }
}

/**
 * NPC Sprite Class
 */
export class NPCSprite extends GameSprite {
    constructor(scene, x, y, npcType = 'generic') {
        super(scene, x, y, npcType);
        
        this.npcType = npcType;
        this.behavior = null;
    }
    
    setBehavior(behavior) {
        this.behavior = behavior;
    }
    
    update() {
        // Update NPC behavior each frame
        if (this.behavior) {
            this.behavior(this);
        }
    }
}

/**
 * Trap Sprite Class
 */
export class TrapSprite extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, trapType = 'spike') {
        super(scene, x, y, trapType);
        
        scene.add.existing(this);
        scene.physics.add.existing(this);
        
        this.body.setImmovable(true);
        this.trapType = trapType;
        this.damage = 10;
        this.isActive = true;
    }
    
    activate() {
        this.isActive = true;
        this.setAlpha(1);
    }
    
    deactivate() {
        this.isActive = false;
        this.setAlpha(0.5);
    }
}
