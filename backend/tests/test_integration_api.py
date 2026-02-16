"""
Simple API integration test moved into `backend/tests`.

Registers an agent, starts a game, submits an observe action with prompt_summary,
and polls the feed to verify logging.
"""
import requests
import time

BASE = "http://localhost:8000/api/v1"


def register_agent():
    payload = {
        "name": "Test Agent",
        "description": "Integration test agent",
        "creator": "tester@example.com",
        "model": "gpt-4",
        "system_prompt": "You are a test agent.",
        "skills": {"reasoning": 1, "observation": 1}
    }
    r = requests.post(f"{BASE}/agents/register", json=payload)
    r.raise_for_status()
    return r.json()['agent_id']


def start_game(agent_id):
    payload = {"agent_id": agent_id, "scenario_id": "maze_001"}
    r = requests.post(f"{BASE}/games/start", json=payload)
    r.raise_for_status()
    return r.json()['game_id']


def submit_observe(game_id):
    payload = {
        "action": "observe",
        "params": {"observation_type": "nearby_entities"},
        "prompt_summary": "Test: Observe nearby entities and blockers"
    }
    r = requests.post(f"{BASE}/games/{game_id}/action", json=payload)
    r.raise_for_status()
    return r.json()


def get_feed():
    r = requests.get(f"{BASE}/feed?limit=10")
    r.raise_for_status()
    return r.json()


if __name__ == '__main__':
    print("Registering agent...")
    aid = register_agent()
    print("Agent id:", aid)

    print("Starting game...")
    gid = start_game(aid)
    print("Game id:", gid)

    print("Submitting observe action with prompt summary...")
    resp = submit_observe(gid)
    print("Action response:", resp)

    print("Waiting briefly for feed to update...")
    time.sleep(1.5)

    feed = get_feed()
    print("Feed entries (recent):")
    for e in feed.get('entries', []):
        print(e)

    print("Integration test completed.")
