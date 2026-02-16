import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'agentic_realm.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS instances (
        instance_id TEXT PRIMARY KEY,
        scenario_id TEXT,
        state_json TEXT,
        players_json TEXT,
        created_at TEXT,
        updated_at TEXT,
        active INTEGER
    )
    ''')
    conn.commit()
    conn.close()


def save_instance_dict(instance_dict: dict):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute('''
    INSERT OR REPLACE INTO instances (instance_id, scenario_id, state_json, players_json, created_at, updated_at, active)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        instance_dict['instance_id'],
        instance_dict['scenario_id'],
        json.dumps(instance_dict.get('state') or {}),
        json.dumps(instance_dict.get('players') or []),
        instance_dict.get('created_at', now),
        now,
        1 if instance_dict.get('active', True) else 0
    ))
    conn.commit()
    conn.close()


def load_instance_dict(instance_id: str):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM instances WHERE instance_id = ?', (instance_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'instance_id': row['instance_id'],
        'scenario_id': row['scenario_id'],
        'state': json.loads(row['state_json'] or '{}'),
        'players': json.loads(row['players_json'] or '[]'),
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'active': bool(row['active'])
    }


def list_instance_dicts(active_only=True):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    if active_only:
        cur.execute('SELECT * FROM instances WHERE active = 1')
    else:
        cur.execute('SELECT * FROM instances')
    rows = cur.fetchall()
    conn.close()
    out = []
    for row in rows:
        out.append({
            'instance_id': row['instance_id'],
            'scenario_id': row['scenario_id'],
            'state': json.loads(row['state_json'] or '{}'),
            'players': json.loads(row['players_json'] or '[]'),
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'active': bool(row['active'])
        })
    return out


def delete_instance(instance_id: str):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM instances WHERE instance_id = ?', (instance_id,))
    conn.commit()
    conn.close()


def mark_instance_inactive(instance_id: str):
    init_db()
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute('UPDATE instances SET active = 0, updated_at = ? WHERE instance_id = ?', (now, instance_id))
    conn.commit()
    conn.close()
