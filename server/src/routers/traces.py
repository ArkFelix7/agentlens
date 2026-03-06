"""REST endpoints for trace event ingestion and retrieval."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.schemas.trace import TraceIngestRequest, TraceIngestResponse, TraceEventResponse, TraceEventTreeNode
from src.services import trace_service
from src.websocket.manager import manager

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", response_model=TraceIngestResponse)
async def ingest_traces(
    request: TraceIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a batch of trace events. Auto-creates session if it doesn't exist."""
    count = await trace_service.ingest_events(db, request.session_id, request.events)

    # Broadcast each event to connected dashboard clients
    for event in request.events:
        event_dict = event.model_dump()
        # Convert datetime to string for JSON serialization
        if event_dict.get("timestamp"):
            event_dict["timestamp"] = event_dict["timestamp"].isoformat() if hasattr(event_dict["timestamp"], "isoformat") else str(event_dict["timestamp"])
        await manager.broadcast_to_dashboards({
            "type": "trace_event",
            "data": event_dict,
        })

    return TraceIngestResponse(ingested=count, session_id=request.session_id)


@router.get("/{session_id}", response_model=dict)
async def get_traces(
    session_id: str,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all trace events for a session."""
    events = await trace_service.get_events_for_session(db, session_id, event_type=event_type)
    return {"events": [e.model_dump() for e in events]}


@router.get("/{session_id}/tree", response_model=dict)
async def get_trace_tree(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get trace events as a nested tree structure."""
    tree = await trace_service.get_event_tree(db, session_id)
    return {"tree": [node.model_dump() for node in tree]}
