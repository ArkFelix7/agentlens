"""REST endpoints for trace event ingestion and retrieval."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from agentlens_server.database import get_db
from agentlens_server.schemas.trace import TraceIngestRequest, TraceIngestResponse, TraceEventResponse, TraceEventTreeNode
from agentlens_server.services import trace_service
from agentlens_server.services.budget_service import check_budget_rules
from agentlens_server.services.score_service import compute_score
from agentlens_server.websocket.manager import manager as ws_manager
from agentlens_server.models.trace_event import TraceEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", response_model=TraceIngestResponse)
async def ingest_traces(
    request: TraceIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> TraceIngestResponse:
    """Ingest a batch of trace events. Auto-creates session if it doesn't exist."""
    count = await trace_service.ingest_events(db, request.session_id, request.events)

    # Broadcast each event to connected dashboard clients and run budget checks
    for event in request.events:
        event_dict = event.model_dump()
        # Convert datetime to string for JSON serialization
        if event_dict.get("timestamp"):
            event_dict["timestamp"] = event_dict["timestamp"].isoformat() if hasattr(event_dict["timestamp"], "isoformat") else str(event_dict["timestamp"])
        await ws_manager.broadcast_to_dashboards({
            "type": "trace_event",
            "data": event_dict,
        })

        # Budget guardrail check — construct a lightweight ORM proxy with the fields
        # needed by budget_service (session_id, event_name, cost_usd)
        proxy_event = TraceEvent(
            id="",
            session_id=request.session_id,
            event_type=event.event_type,
            event_name=event.event_name,
            cost_usd=event.cost_usd if event.cost_usd is not None else 0.0,
        )
        try:
            budget_alerts = await check_budget_rules(request.session_id, proxy_event, db)
            for alert in budget_alerts:
                await ws_manager.broadcast_to_dashboards({
                    "type": "budget_alert",
                    "data": alert.model_dump(mode="json"),
                })
        except Exception as e:
            logger.warning("Budget guardrail check failed: %s", e)

    # Broadcast score_update after all events ingested
    try:
        score = await compute_score(request.session_id, db)
        if score:
            await ws_manager.broadcast_to_dashboards({
                "type": "score_update",
                "session_id": request.session_id,
                "data": {
                    "session_id": score.session_id,
                    "score": score.score,
                    "grade": score.grade,
                    "color": score.color,
                },
            })
    except Exception as e:
        logger.warning("Score broadcast failed: %s", e)

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
