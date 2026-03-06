"""WebSocket message handlers.

Handles messages from both SDK clients (inbound trace events)
and dashboard clients (query/command messages).
"""

import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

from src.websocket.manager import manager
from src.database import AsyncSessionLocal
from src.services import trace_service, memory_service
from src.schemas.trace import TraceEventCreate, TraceIngestRequest
from src.schemas.memory import MemoryEntryCreate

logger = logging.getLogger(__name__)


async def handle_dashboard_client(ws: WebSocket) -> None:
    """Handle messages from a dashboard browser client."""
    await manager.connect_dashboard(ws)
    try:
        while True:
            try:
                raw = await ws.receive_text()
                msg = json.loads(raw)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse dashboard message: {e}")
                continue

            msg_type = msg.get("type")

            async with AsyncSessionLocal() as db:
                if msg_type == "get_sessions":
                    from src.services.session_service import get_sessions
                    sessions = await get_sessions(db)
                    await manager.send_to_client(ws, {
                        "type": "sessions_list",
                        "data": [s.model_dump() for s in sessions],
                    })

                elif msg_type == "get_session_events":
                    session_id = msg.get("session_id")
                    if session_id:
                        events = await trace_service.get_events_for_session(db, session_id)
                        await manager.send_to_client(ws, {
                            "type": "session_events",
                            "session_id": session_id,
                            "data": [e.model_dump() for e in events],
                        })

                elif msg_type == "clear_session":
                    session_id = msg.get("session_id")
                    if session_id:
                        from src.services.session_service import delete_session
                        await delete_session(db, session_id)
                        await manager.send_to_client(ws, {
                            "type": "session_cleared",
                            "session_id": session_id,
                        })

                elif msg_type == "pong":
                    pass  # Heartbeat response

    except WebSocketDisconnect:
        logger.info("Dashboard client disconnected")
    except Exception as e:
        logger.error(f"Dashboard WS error: {e}")
    finally:
        manager.disconnect(ws)


async def handle_sdk_client(ws: WebSocket) -> None:
    """Handle messages from SDK/agent clients sending trace events."""
    await manager.connect_sdk(ws)
    try:
        while True:
            try:
                raw = await ws.receive_text()
                msg = json.loads(raw)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse SDK message: {e}")
                continue

            msg_type = msg.get("type")

            async with AsyncSessionLocal() as db:
                if msg_type == "trace_events":
                    session_id = msg.get("session_id")
                    events_data = msg.get("events", [])
                    if session_id and events_data:
                        events = [TraceEventCreate(**e) for e in events_data]
                        count = await trace_service.ingest_events(db, session_id, events)

                        # Broadcast each event to dashboard clients
                        for e in events_data:
                            await manager.broadcast_to_dashboards({
                                "type": "trace_event",
                                "data": e,
                            })

                elif msg_type == "session_start":
                    data = msg.get("data", {})
                    await manager.broadcast_to_dashboards({
                        "type": "session_start",
                        "data": data,
                    })

                elif msg_type == "session_end":
                    data = msg.get("data", {})
                    await manager.broadcast_to_dashboards({
                        "type": "session_end",
                        "data": data,
                    })

                elif msg_type == "memory_update":
                    data = msg.get("data", {})
                    if data:
                        try:
                            entry = await memory_service.create_memory_entry(
                                db, MemoryEntryCreate(**data)
                            )
                            await manager.broadcast_to_dashboards({
                                "type": "memory_update",
                                "data": entry.model_dump(),
                            })
                        except Exception as e:
                            logger.error(f"Memory update failed: {e}")

                elif msg_type == "pong":
                    pass

    except WebSocketDisconnect:
        logger.info("SDK client disconnected")
    except Exception as e:
        logger.error(f"SDK WS error: {e}")
    finally:
        manager.disconnect(ws)
