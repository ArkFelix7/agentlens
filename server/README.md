# agentlens-server

FastAPI backend for [AgentLens](https://github.com/aarya/agentlens) — real-time observability for AI agents.

## Install

```bash
pip install agentlens-server
```

## Run

```bash
agentlens-server
# REST API: http://localhost:8766/api/v1
# WebSocket: ws://localhost:8766/ws
# Dashboard: http://localhost:5173 (start separately)
```

## Run from source

```bash
git clone https://github.com/aarya/agentlens
cd agentlens
make install && make dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/traces/{session_id}` | Get all trace events for a session |
| POST | `/api/v1/traces/{session_id}` | Ingest trace events |
| GET | `/api/v1/costs/{session_id}` | Cost breakdown |
| GET | `/api/v1/hallucinations/{session_id}` | Hallucination alerts |
| POST | `/api/v1/hallucinations/{session_id}/detect` | Run detection |
| GET | `/api/v1/memory/{session_id}` | Memory entries |
| PATCH | `/api/v1/memory/entry/{id}` | Edit memory entry |
| DELETE | `/api/v1/memory/entry/{id}` | Delete memory entry |
| GET | `/api/v1/replay/{session_id}` | Replay event stream |
| GET | `/health` | Health check |

## WebSocket Protocol

Connect to `ws://localhost:8766/ws` and send a hello message:

```json
{ "type": "hello", "role": "sdk" }
```

Roles: `"sdk"` (agent sending events) or `"dashboard"` (browser receiving events).

## Configuration

Environment variables (all optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///agentlens.db` | Database URL |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8766` | Port |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## License

MIT
