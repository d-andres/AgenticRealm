"""
Integration Test - Game Engine & Agent Creation

Moved from top-level test file to `backend/tests` for clarity.
"""

import asyncio
from core.state import GameState, Entity
from core.engine import GameEngine
from agents.registrar import AgentRegistrar
from agents.judge import Judge, Trap
import json

async def test_integration():
    """Test integration: Game Loop & Agent Creation"""

    print("\n" + "="*60)
    print("🎮 AgenticRealm Integration Test")
    print("="*60 + "\n")
    
    # Initialize systems
    state = GameState()
    engine = GameEngine(tick_rate=0.5)  # 0.5 seconds per tick for testing
    registrar = AgentRegistrar()
    judge = Judge()
    
    print("✓ Systems initialized\n")
    
    # Test 1: Register agents
    print("TEST 1: Agent Registration")
    print("-" * 40)
    
    agent1 = registrar.register_agent('user_1_agent', {
        'name': 'CleverBot',
        'skills': {'reasoning': 2, 'observation': 1}
    })
    
    agent2 = registrar.register_agent('user_2_agent', {
        'name': 'ObserverBot',
        'skills': {'reasoning': 1, 'observation': 3}
    })
    
    print(f"✓ Registered {len(registrar.agents)} agents\n")
    
    # Test 2: Add entities to game state
    print("TEST 2: Entity Management")
    print("-" * 40)
    
    agent1_entity = Entity(
        id='user_1_agent',
        type='agent',
        x=100,
        y=100,
        properties={'name': 'CleverBot', 'health': 100}
    )
    
    agent2_entity = Entity(
        id='user_2_agent',
        type='agent',
        x=200,
        y=100,
        properties={'name': 'ObserverBot', 'health': 100}
    )
    
    state.add_entity(agent1_entity)
    state.add_entity(agent2_entity)
    
    print(f"✓ Added {len(state.entities)} agents to game state\n")
    
    # Test 3: Register agents with engine
    print("TEST 3: Engine Registration")
    print("-" * 40)
    
    engine.register_agent('user_1_agent', agent1)
    engine.register_agent('user_2_agent', agent2)
    
    print(f"✓ Registered {len(engine.agents)} agents with engine\n")
    
    # Test 4: Add traps
    print("TEST 4: Environment Setup")
    print("-" * 40)
    
    trap = Trap(
        id='trap_1',
        x=150,
        y=150,
        radius=30,
        damage=10,
        active=True
    )
    judge.add_trap(trap)
    
    print(f"✓ Added {len(judge.traps)} traps to world\n")
    
    # Test 5: Test game loop
    print("TEST 5: Game Loop Execution")
    print("-" * 40)
    
    # Set state callback
    tick_count = [0]
    async def on_state_update():
        tick_count[0] += 1
    
    engine.set_state_callback(on_state_update)
    
    # Start engine
    await engine.start()
    print("✓ Engine started")
    
    # Run for a few ticks
    await asyncio.sleep(3)
    
    print(f"✓ Engine completed {tick_count[0]} ticks")
    print(f"✓ Current turn: {engine.turn}\n")
    
    # Stop engine
    await engine.stop()
    print("✓ Engine stopped\n")
    
    # Test 6: Collision detection
    print("TEST 6: Collision Detection")
    print("-" * 40)
    
    # Agent moving close to trap
    valid, reason = judge.validate_movement((100, 100), (160, 160), {'width': 800, 'height': 600})
    print(f"✓ Movement validation: {valid} ({reason})")
    
    # Check collisions at new position
    collisions = judge.check_collisions('user_1_agent', (160, 160), 20, state.entities)
    
    if collisions:
        print(f"✓ Collision detected: {collisions[0]['type']} (damage: {collisions[0]['damage']})\n")
    else:
        print(f"✓ No collisions detected\n")
    
    # Test 7: Final state
    print("TEST 7: Final Game State")
    print("-" * 40)
    
    final_state = state.to_dict()
    print(f"Entities: {len(final_state['entities'])}")
    print(f"Events logged: {len(final_state['recent_events'])}")
    print(f"World size: {final_state['properties']['world_width']}x{final_state['properties']['world_height']}\n")
    
    # Test 8: Skill validation
    print("TEST 8: Skill Validation")
    print("-" * 40)
    
    # Valid agent
    valid_agent = registrar.register_agent('valid_test', {
        'name': 'ValidAgent',
        'skills': {'reasoning': 1, 'observation': 1}
    })
    print(f"✓ Valid agent created: {valid_agent is not None}")
    
    # Invalid agent (missing required skills)
    invalid_agent = registrar.register_agent('invalid_test', {
        'name': 'InvalidAgent',
        'skills': {}  # No skills
    })
    print(f"✓ Invalid agent rejected: {invalid_agent is None}\n")
    
    # Summary
    print("="*60)
    print("✅ Integration Tests Complete!")
    print("="*60)
    print("\nKey Systems Tested:")
    print("  ✓ Agent registration & skill validation")
    print("  ✓ Game state management")
    print("  ✓ Engine registration & event callbacks")
    print("  ✓ Game loop execution")
    print("  ✓ Collision detection")
    print("  ✓ Entity management")
    print("\nReady for next: Frontend Rendering")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_integration())
