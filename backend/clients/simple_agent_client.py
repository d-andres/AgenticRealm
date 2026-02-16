"""
Simple Agent Client

Lightweight example demonstrating how an external AI agent can:
- register with the platform
- start or join a persistent scenario instance
- submit actions (with a condensed `prompt_summary`)

Requires `requests`.
"""
import os
import time
import requests
import uuid

BASE = os.getenv('AGENTICREALM_BASE', 'http://localhost:8000/api/v1')


def register_agent(name: str, creator: str = 'dev@example.com') -> str:
    payload = {
        'name': name,
        'description': 'Test agent (simple client)',
        'creator': creator,
        'model': 'gpt-4',
        'system_prompt': 'You are a test agent.',
        'skills': {'reasoning': 1, 'observation': 1}
    }
    r = requests.post(f"{BASE}/agents/register", json=payload)
    r.raise_for_status()
    return r.json()['agent_id']


def start_instance(scenario_id: str, admin_token: str = None) -> dict:
    headers = {}
    if admin_token:
        headers['x-admin-token'] = admin_token
    r = requests.post(f"{BASE}/scenarios/{scenario_id}/instances", headers=headers)
    r.raise_for_status()
    return r.json()


def join_instance(instance_id: str, agent_id: str) -> dict:
    r = requests.post(f"{BASE}/scenarios/instances/{instance_id}/join", params={'agent_id': agent_id})
    r.raise_for_status()
    return r.json()


def submit_action(game_id: str, action: str, params: dict = None, prompt_summary: str = None):
    body = {'action': action, 'params': params or {}}
    if prompt_summary:
        body['prompt_summary'] = prompt_summary
    r = requests.post(f"{BASE}/games/{game_id}/action", json=body)
    r.raise_for_status()
    return r.json()


def main():
    name = f"simple-client-{uuid.uuid4().hex[:6]}"
    print('Registering agent...')
    agent_id = register_agent(name)
    print('Agent id:', agent_id)

    # Start a scenario instance (optional - requires admin token if set on server)
    scenario_id = os.getenv('SCENARIO_ID', 'maze_001')
    admin_token = os.getenv('ADMIN_TOKEN')
    print('Starting instance for scenario:', scenario_id)
    inst = start_instance(scenario_id, admin_token=admin_token)
    instance_id = inst['instance_id']
    print('Instance started:', instance_id)

    print('Joining instance as agent...')
    join = join_instance(instance_id, agent_id)
    game_id = join['game_id']
    print('Joined, game id:', game_id)

    # Simple loop: observe then move with prompt_summary
    for i in range(3):
        print('Observing...')
        obs = submit_action(game_id, 'observe', params={'observation_type': 'nearby_entities'}, prompt_summary=f'Observation summary turn {i}')
        print('Obs response turn', obs.get('turn'))
        time.sleep(0.5)

        print('Moving east...')
        move = submit_action(game_id, 'move', params={'direction': 'east'}, prompt_summary=f'Move intent turn {i}')
        print('Move response:', move.get('message'))
        time.sleep(0.5)

    print('Finished sample run. Fetching result...')
    res = requests.get(f"{BASE}/games/{game_id}/result")
    print(res.json())


if __name__ == '__main__':
    main()
