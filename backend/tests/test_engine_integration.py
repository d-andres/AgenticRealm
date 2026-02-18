"""
Integration Test - Core systems: engine, state, agent store, game session.

Tests the current architecture (provider-agnostic, entity-type-based routing).
Run from backend/:  python -m tests.test_engine_integration
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.state import GameState, Entity
from core.engine import GameEngine
from store.agent_store import AgentStore
from scenarios.templates import ScenarioManager
import pytest
from game_session import GameSession, GameSessionManager


@pytest.mark.asyncio
async def test_integration():
    """Smoke-test all core systems together."""

    print("\n" + "=" * 60)
    print("AgenticRealm Integration Test")
    print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Test 1 — Agent Store
    # ------------------------------------------------------------------
    print("TEST 1: Agent Registration (AgentStore)")
    print("-" * 40)

    store = AgentStore()
    agent1 = store.register({
        'name': 'CleverBot',
        'description': 'A test agent',
        'creator': 'tester',
        'model': 'gpt-4o',
        'system_prompt': 'You are a test agent.',
        'skills': {'reasoning': 2, 'observation': 1},
    })
    agent2 = store.register({
        'name': 'ObserverBot',
        'description': 'Another test agent',
        'creator': 'tester',
        'model': 'claude-3',
        'system_prompt': 'You are an observer.',
        'skills': {'observation': 3, 'stealth': 2},
    })

    assert store.agent_exists(agent1.agent_id)
    assert store.agent_exists(agent2.agent_id)
    assert not store.agent_exists('nonexistent-id')
    print(f"✓ Registered {len(store.agents)} agents")
    print(f"  CleverBot skills: {agent1.skills}")
    print(f"  ObserverBot skills: {agent2.skills}\n")

    # ------------------------------------------------------------------
    # Test 2 — Game State & Entity Management
    # ------------------------------------------------------------------
    print("TEST 2: Entity Management (GameState)")
    print("-" * 40)

    state = GameState()
    player = Entity(id='agent_1', type='agent', x=50, y=50,
                    properties={'health': 100, 'gold': 500, 'inventory': []})
    npc = Entity(id='npc_shopkeeper', type='npc', x=200, y=200,
                 properties={'name': 'Gerald the Shopkeeper', 'job': 'shopkeeper',
                             'inventory': {'sword_01': {'name': 'Iron Sword', 'value': 150}},
                             'pricing_multiplier': 1.1})
    hazard = Entity(id='hazard_01', type='hazard', x=300, y=300,
                    properties={'damage': 25, 'radius': 20})
    exit_e = Entity(id='exit_01', type='exit', x=750, y=550,
                    properties={'radius': 25})

    for e in [player, npc, hazard, exit_e]:
        state.add_entity(e)

    assert len(state.entities) == 4
    assert 'npc_shopkeeper' in state.entities
    print(f"✓ Added {len(state.entities)} entities")
    print(f"  Types: {[e.type for e in state.entities.values()]}\n")

    # ------------------------------------------------------------------
    # Test 3 — Scenario Templates
    # ------------------------------------------------------------------
    print("TEST 3: Scenario Templates (ScenarioManager)")
    print("-" * 40)

    templates = ScenarioManager.get_all_templates()
    assert len(templates) > 0, "No scenario templates registered"
    t = ScenarioManager.get_template('market_square')
    assert t is not None
    assert ScenarioManager.template_exists('market_square')
    assert not ScenarioManager.template_exists('nonexistent_scenario')
    print(f"✓ Templates available: {[t.scenario_id for t in templates]}")
    print(f"  market_square: {t.name}")
    print(f"  max_turns={t.max_turns}, starting_gold={t.starting_gold}\n")

    # ------------------------------------------------------------------
    # Test 4 — Game Session (full flow)
    # ------------------------------------------------------------------
    print("TEST 4: Game Session Actions")
    print("-" * 40)

    mgr = GameSessionManager()
    sess = mgr.create_session('market_square', 'agent_test_01')
    mgr.start_session(sess.game_id)

    assert sess.status == 'in_progress'
    assert 'agent_test_01' in sess.state.entities

    # observe
    ok, msg, data = sess.process_action('observe', {'radius': 300})
    assert ok, f"observe failed: {msg}"
    print(f"✓ observe: {msg}")

    # move - valid
    ok, msg, data = sess.process_action('move', {'direction': 'right', 'distance': 20})
    assert ok, f"move failed: {msg}"
    print(f"✓ move right: {msg}")

    # move - out of bounds
    ok, msg, _ = sess.process_action('move', {'direction': 'left', 'distance': 10000})
    assert not ok
    print(f"✓ out-of-bounds rejected: {msg}")

    # unknown action
    ok, msg, _ = sess.process_action('fly', {})
    assert not ok
    print(f"✓ unknown action rejected: {msg}\n")

    # ------------------------------------------------------------------
    # Test 5 — Engine Loop
    # ------------------------------------------------------------------
    print("TEST 5: Game Engine Loop")
    print("-" * 40)

    engine = GameEngine(tick_rate=0.1)
    tick_count = [0]

    async def on_tick():
        tick_count[0] += 1

    engine.set_state_callback(on_tick)
    await engine.start()
    await asyncio.sleep(0.5)
    await engine.stop()

    assert tick_count[0] > 0
    print(f"✓ Engine ran {tick_count[0]} ticks in 0.5s\n")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("All integration tests passed!")
    print("=" * 60)
    print("\nSystems verified:")
    print("  ✓ AgentStore — open-ended skill dict, CRUD")
    print("  ✓ GameState — generic entity types (agent, npc, hazard, exit)")
    print("  ✓ ScenarioManager — template lookup and validation")
    print("  ✓ GameSession — observe, move, bounds check, unknown action")
    print("  ✓ GameEngine — async tick loop\n")


if __name__ == "__main__":
    asyncio.run(test_integration())

