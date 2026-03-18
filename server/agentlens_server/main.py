"""AgentLens FastAPI server — main application entry point.

Runs on port 8766 with:
  - REST API at /api/v1/*
  - WebSocket at /ws
  - Auto-creates SQLite database on first run
"""

import logging
import signal
import asyncio
from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from agentlens_server.config import settings
from agentlens_server.database import create_all_tables
from agentlens_server.websocket.manager import manager
from agentlens_server.websocket.handlers import handle_dashboard_client
from agentlens_server.routers import traces, sessions, costs, hallucinations, memory, privacy, score, budget, testgen, prompts, compare

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, clean up on shutdown."""
    logger.info("AgentLens server starting up...")
    await create_all_tables()
    logger.info("Database tables ready.")
    await manager.start_heartbeat()
    yield
    logger.info("AgentLens server shutting down...")


app = FastAPI(
    title="AgentLens Server",
    description="Real-time observability backend for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow dashboard dev server and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST routers
app.include_router(traces.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(costs.router, prefix="/api/v1")
app.include_router(hallucinations.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1")
app.include_router(score.router, prefix="/api/v1")
app.include_router(budget.router, prefix="/api/v1")
app.include_router(testgen.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(compare.router, prefix="/api/v1")


# Serve compiled dashboard (present when installed via pip)
import os as _os
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles

_static_dir = _Path(__file__).parent / "static"
if _static_dir.exists() and _static_dir.is_dir():
    # Mount SPA catch-all LAST so API routes take precedence
    app.mount("/app", StaticFiles(directory=str(_static_dir), html=True), name="static")


@app.get("/")
async def root():
    return {"status": "ok", "service": "AgentLens Server", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Unified WebSocket endpoint for both dashboard and SDK clients.

    The client sends a 'hello' message to identify itself:
      {"type": "hello", "role": "dashboard"} — dashboard browser client
      {"type": "hello", "role": "sdk"} — SDK/agent client (default)
    """
    await ws.accept()
    try:
        # Wait for identification
        try:
            raw = await asyncio.wait_for(ws.receive_text(), timeout=5.0)
            import json
            msg = json.loads(raw)
            role = msg.get("role", "sdk")
        except asyncio.TimeoutError:
            role = "sdk"
        except Exception:
            role = "sdk"

        if role == "dashboard":
            # Re-use manager's dashboard tracking (already accepted above)
            manager.dashboard_clients.add(ws)
            # Hand off to dashboard handler (skipping re-accept)
            await _handle_dashboard_after_accept(ws)
        else:
            manager.sdk_clients.add(ws)
            await _handle_sdk_after_accept(ws)
    except Exception as e:
        logger.error(f"WS endpoint error: {e}")
    finally:
        manager.disconnect(ws)


async def _handle_dashboard_after_accept(ws: WebSocket) -> None:
    """Handle a dashboard client that has already been accepted."""
    import json
    from fastapi import WebSocketDisconnect
    from agentlens_server.database import AsyncSessionLocal
    from agentlens_server.services import trace_service
    from agentlens_server.services.session_service import get_sessions, delete_session

    try:
        while True:
            try:
                raw = await ws.receive_text()
            except (WebSocketDisconnect, Exception):
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            async with AsyncSessionLocal() as db:
                if msg_type == "get_sessions":
                    sessions_list = await get_sessions(db)
                    await manager.send_to_client(ws, {
                        "type": "sessions_list",
                        "data": [s.model_dump(mode="json") for s in sessions_list],
                    })
                elif msg_type == "get_session_events":
                    session_id = msg.get("session_id")
                    if session_id:
                        events = await trace_service.get_events_for_session(db, session_id)
                        await manager.send_to_client(ws, {
                            "type": "session_events",
                            "session_id": session_id,
                            "data": [e.model_dump(mode="json") for e in events],
                        })
                elif msg_type == "clear_session":
                    session_id = msg.get("session_id")
                    if session_id:
                        await delete_session(db, session_id)
                        await manager.send_to_client(ws, {
                            "type": "session_cleared",
                            "session_id": session_id,
                        })
                elif msg_type == "pong":
                    pass
    except Exception:
        pass
    finally:
        manager.dashboard_clients.discard(ws)


async def _handle_sdk_after_accept(ws: WebSocket) -> None:
    """Handle an SDK client that has already been accepted."""
    import json
    from fastapi import WebSocketDisconnect
    from agentlens_server.database import AsyncSessionLocal
    from agentlens_server.services import trace_service, memory_service
    from agentlens_server.services.session_service import create_or_update_session
    from agentlens_server.schemas.trace import TraceEventCreate
    from agentlens_server.schemas.memory import MemoryEntryCreate

    try:
        while True:
            try:
                raw = await ws.receive_text()
            except (WebSocketDisconnect, Exception):
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            async with AsyncSessionLocal() as db:
                if msg_type == "trace_events":
                    session_id = msg.get("session_id")
                    events_data = msg.get("events", [])
                    if session_id and events_data:
                        try:
                            events = [TraceEventCreate(**e) for e in events_data]
                            await trace_service.ingest_events(db, session_id, events)
                            for e_dict in events_data:
                                await manager.broadcast_to_dashboards({
                                    "type": "trace_event",
                                    "data": e_dict,
                                })
                        except Exception as e:
                            logger.error(f"Failed to ingest trace_events: {e}")
                elif msg_type == "session_start":
                    data = msg.get("data", {})
                    sid = data.get("session_id")
                    aname = data.get("agent_name", "agent")
                    if sid:
                        session_resp = await create_or_update_session(
                            db, sid, aname,
                            agent_id=data.get("agent_id"),
                            agent_role=data.get("agent_role"),
                            parent_session_id=data.get("parent_session_id"),
                        )
                        # Use mode='json' to get datetime as ISO strings (json.dumps-safe)
                        data = session_resp.model_dump(mode="json")
                    await manager.broadcast_to_dashboards({"type": "session_start", "data": data})
                elif msg_type == "session_end":
                    await manager.broadcast_to_dashboards({"type": "session_end", "data": msg.get("data", {})})
                elif msg_type == "memory_update":
                    data = msg.get("data", {})
                    if data:
                        try:
                            entry = await memory_service.create_memory_entry(db, MemoryEntryCreate(**data))
                            await manager.broadcast_to_dashboards({"type": "memory_update", "data": entry.model_dump(mode="json")})
                        except Exception as e:
                            logger.error(f"Memory update failed: {e}")
                elif msg_type == "pong":
                    pass
    except Exception:
        pass
    finally:
        manager.sdk_clients.discard(ws)


def run() -> None:
    """Entry point for `agentlens-server` CLI — starts server only."""
    uvicorn.run("agentlens_server.main:app", host="0.0.0.0", port=8766, reload=False)


def start() -> None:
    """Entry point for `agentlens` CLI — starts server and opens browser."""
    import threading
    import webbrowser
    import time

    def _open_browser() -> None:
        time.sleep(2.0)
        webbrowser.open("http://localhost:8766")

    threading.Thread(target=_open_browser, daemon=True).start()

    print("")
    print("  AgentLens v0.2.0 starting...")
    print("  Dashboard: http://localhost:8766")
    print("  API:       http://localhost:8766/api/v1")
    print("")
    print("  Instrument your agent:")
    print("    from agentlens_sdk import auto_instrument")
    print("    auto_instrument()")
    print("")
    uvicorn.run("agentlens_server.main:app", host="0.0.0.0", port=8766, reload=False)
