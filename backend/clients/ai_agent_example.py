"""
Example: Connecting AI Agents to AgenticRealm

This script demonstrates how to:
1. Register a Scenario Generator AI agent (uses GPT-4)
2. Register an NPC Admin AI agent (uses GPT-4)
3. Request scenario generation
4. Request NPC responses to player actions
"""

import asyncio
import httpx
import json
import os
from typing import Optional

# Configuration
API_URL = "http://localhost:8000"
GPT_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")


async def register_scenario_generator_agent():
    """Register a GPT-4 Scenario Generator agent"""
    print("\n📋 Registering Scenario Generator Agent...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/ai-agents/register",
            json={
                "agent_name": "gpt4-scenario-generator",
                "agent_role": "scenario_generator",
                "agent_type": "gpt",
                "config": {
                    "api_key": GPT_API_KEY,
                    "model": "gpt-4"
                }
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False


async def register_npc_admin_agent():
    """Register a GPT-4 NPC Admin agent"""
    print("\n👥 Registering NPC Admin Agent...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/ai-agents/register",
            json={
                "agent_name": "gpt4-npc-admin",
                "agent_role": "npc_admin",
                "agent_type": "gpt",
                "config": {
                    "api_key": GPT_API_KEY,
                    "model": "gpt-4"
                }
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False


async def request_scenario_generation():
    """Request the Scenario Generator agent to create stores"""
    print("\n🏪 Requesting scenario generation...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/ai-agents/request/scenario_generator/generate_stores",
            json={
                "context": {
                    "num_stores": 4,
                    "themes": ["urban_market", "bustling"]
                }
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            stores = data["result"].get("stores", [])
            print(f"✓ Generated {len(stores)} stores:")
            for store in stores[:2]:  # Show first 2
                print(f"  - {store.get('name', 'Unknown')} (owned by {store.get('proprietor', 'Unknown')})")
            return True
        else:
            print(f"✗ Generation failed: {data['result']}")
            return False
    else:
        print(f"✗ Request failed: {response.text}")
        return False


async def request_npc_decision():
    """Request the NPC Admin agent to make an NPC decision"""
    print("\n💬 Requesting NPC decision...")
    
    npc_data = {
        "name": "Captain Dorn",
        "job": "guard",
        "personality": "stern, protective, but fair",
        "skills": {"combat": 3, "detection": 2}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/ai-agents/request/npc_admin/npc_decision",
            json={
                "context": {
                    "npc_id": "guard_001",
                    "npc_data": npc_data,
                    "situation": "A suspicious person is trying to sneak into the luxury boutique"
                }
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            result = data["result"]
            print(f"✓ NPC Decision:")
            print(f"  Action: {result.get('action', 'unknown')}")
            print(f"  Message: {result.get('message', 'silence')}")
            print(f"  Emotion: {result.get('emotion', 'neutral')}")
            return True
        else:
            print(f"✗ Decision failed: {data['result']}")
            return False
    else:
        print(f"✗ Request failed: {response.text}")
        return False


async def request_npc_interaction():
    """Request NPC response to player interaction"""
    print("\n🎭 Requesting NPC interaction response...")
    
    npc_data = {
        "name": "Merchant Thora",
        "job": "shopkeeper",
        "personality": "friendly, business-minded, loves haggling",
        "skills": {"negotiation": 2, "persuasion": 1}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/ai-agents/request/npc_admin/npc_interaction",
            json={
                "context": {
                    "npc_id": "shopkeeper_001",
                    "npc_data": npc_data,
                    "player_action": "negotiate",
                    "player_message": "Can you give me a discount on the rope? I'm a regular customer."
                }
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            result = data["result"]
            print(f"✓ NPC Response:")
            print(f"  Reply: {result.get('response', 'silence')}")
            print(f"  Accepts: {result.get('accepts', False)}")
            print(f"  Trust Change: {result.get('trust_change', 0)}")
            return True
        else:
            print(f"✗ Interaction failed: {data['result']}")
            return False
    else:
        print(f"✗ Request failed: {response.text}")
        return False


async def list_agents():
    """List all connected agents"""
    print("\n📊 Checking registered agents...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/api/v1/ai-agents/list")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total agents: {data['total_agents']}")
        for agent in data["agents"]:
            status = "🟢 connected" if agent["is_connected"] else "🔴 disconnected"
            print(f"  - {agent['agent_name']} ({agent['agent_role']}) {status}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False


async def check_health():
    """Check agent pool health"""
    print("\n🏥 Checking agent pool health...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/api/v1/ai-agents/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Pool Status: {data['pool_status']}")
        print(f"  Connected: {data['connected_agents']}/{data['total_agents']}")
        print(f"  Roles: {data['agents_by_role']}")
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False


async def main():
    """Main example workflow"""
    print("=" * 60)
    print("AgenticRealm AI Agent Integration Example")
    print("=" * 60)
    
    # Step 1: Check health
    await check_health()
    
    # Step 2: Register agents
    scenario_ok = await register_scenario_generator_agent()
    npc_ok = await register_npc_admin_agent()
    
    if not scenario_ok or not npc_ok:
        print("\n⚠️  Failed to register agents. Check your API key and connection.")
        print("   Continuing with demonstration...")
    
    # Step 3: List agents
    await list_agents()
    
    # Step 4: Request scenario generation
    await request_scenario_generation()
    
    # Step 5: Request NPC decision
    await request_npc_decision()
    
    # Step 6: Request NPC interaction
    await request_npc_interaction()
    
    # Step 7: Check updated health
    await check_health()
    
    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT:")
    print("   Before running this example:")
    print("   1. Set OPENAI_API_KEY environment variable with your GPT API key")
    print("   2. Ensure AgenticRealm backend is running on http://localhost:8000")
    print("\nExample command:")
    print("  export OPENAI_API_KEY='sk-...your-key...'")
    print("  python backend/clients/ai_agent_example.py")
    print()
    
    asyncio.run(main())
