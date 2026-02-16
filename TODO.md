# AgenticRealm - TODO / Next Steps

This file lists actionable tasks and priorities for the project. Use it as a concise checklist for short-term work.

High priority
- Add rule-based System AI behaviors integrated with `core/engine.py` so system agents act each tick.
- Improve instance persistence: snapshot on stop and periodic save intervals; migrate to an ORM+Postgres plan.
- Implement Server-Sent Events (SSE) or WebSocket push for the presentation feed (replace polling).
- Add basic auth and rate limits for admin endpoints (replace simple `x-admin-token`).

Medium priority
- Add leaderboards persistence and ranking queries (store completed game results in DB).
- Add unit and integration tests for `scenario_instances`, `db.py`, and `game_session` flows.
- Add admin CLI or simple UI to manage instances (start/stop/delete/snapshot).

Lower priority / Nice to have
- Integrate LLM-driven system agents (OpenAI/Anthropic) with configurable providers.
- Add richer presentation UI with replay and per-agent analytics.
- Support multi-player scenarios where multiple user agents can join the same instance.

Notes
- Current instance persistence is SQLite prototype (`backend/db.py`). For production, plan migration to Postgres with an ORM (SQLAlchemy).
- Keep `feed_store` and presentation backward-compatible while adding SSE/WebSocket.
