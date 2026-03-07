"""Business logic for trace event ingestion, retrieval, and tree construction."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ulid import ULID

from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.session import Session
from agentlens_server.schemas.trace import TraceEventCreate, TraceEventResponse, TraceEventTreeNode
from agentlens_server.utils.pricing import calculate_cost

logger = logging.getLogger(__name__)


def _serialize_json(data) -> Optional[str]:
    """Serialize data to JSON string, redacting sensitive fields."""
    if data is None:
        return None
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    sensitive_keys = {"api_key", "token", "password", "secret", "authorization", "auth"}
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if k.lower() in sensitive_keys:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = v
        data = cleaned
    return json.dumps(data)


def _deserialize_json(text: Optional[str]):
    """Deserialize JSON string to Python object."""
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _orm_to_response(event: TraceEvent) -> TraceEventResponse:
    """Convert ORM TraceEvent to Pydantic response schema."""
    return TraceEventResponse(
        id=event.id,
        session_id=event.session_id,
        parent_event_id=event.parent_event_id,
        event_type=event.event_type,
        event_name=event.event_name,
        timestamp=event.timestamp,
        duration_ms=event.duration_ms,
        input_data=_deserialize_json(event.input_data),
        output_data=_deserialize_json(event.output_data),
        model=event.model,
        tokens_input=event.tokens_input,
        tokens_output=event.tokens_output,
        cost_usd=event.cost_usd,
        status=event.status,
        error_message=event.error_message,
        metadata=_deserialize_json(event.metadata_),
    )


async def ingest_events(
    db: AsyncSession,
    session_id: str,
    events: list[TraceEventCreate],
) -> int:
    """Ingest a batch of trace events. Creates session if it doesn't exist. Returns count ingested."""
    # Ensure session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        session = Session(id=session_id, agent_name="unnamed", status="active")
        db.add(session)

    ingested = 0
    total_cost = 0.0
    total_tokens_input = 0
    total_tokens_output = 0

    for event_data in events:
        try:
            event_id = event_data.id or str(ULID())
            ts = event_data.timestamp or datetime.now(timezone.utc)

            # Auto-calculate cost if not provided
            cost = event_data.cost_usd
            if cost is None and event_data.model:
                cost = calculate_cost(event_data.model, event_data.tokens_input, event_data.tokens_output)
            if cost is None:
                cost = 0.0

            # Check for duplicate — skip if event ID already exists
            existing = await db.get(TraceEvent, event_id)
            if existing is not None:
                continue

            event = TraceEvent(
                id=event_id,
                session_id=session_id,
                parent_event_id=event_data.parent_event_id,
                event_type=event_data.event_type,
                event_name=event_data.event_name,
                timestamp=ts,
                duration_ms=event_data.duration_ms,
                input_data=_serialize_json(event_data.input_data),
                output_data=_serialize_json(event_data.output_data),
                model=event_data.model,
                tokens_input=event_data.tokens_input,
                tokens_output=event_data.tokens_output,
                cost_usd=cost,
                status=event_data.status,
                error_message=event_data.error_message,
                metadata_=_serialize_json(event_data.metadata),
            )
            db.add(event)
            total_cost += cost
            total_tokens_input += event_data.tokens_input
            total_tokens_output += event_data.tokens_output
            ingested += 1
        except Exception as e:
            logger.error(f"Failed to ingest event: {e}")

    # Update session aggregates
    session.total_events = (session.total_events or 0) + ingested
    session.total_cost_usd = (session.total_cost_usd or 0.0) + total_cost
    session.total_tokens_input = (session.total_tokens_input or 0) + total_tokens_input
    session.total_tokens_output = (session.total_tokens_output or 0) + total_tokens_output

    await db.commit()
    return ingested


async def get_events_for_session(
    db: AsyncSession,
    session_id: str,
    event_type: Optional[str] = None,
) -> list[TraceEventResponse]:
    """Get all trace events for a session, optionally filtered by event type."""
    query = select(TraceEvent).where(TraceEvent.session_id == session_id).order_by(TraceEvent.timestamp)
    if event_type:
        query = query.where(TraceEvent.event_type == event_type)
    result = await db.execute(query)
    events = result.scalars().all()
    return [_orm_to_response(e) for e in events]


async def get_event_tree(
    db: AsyncSession,
    session_id: str,
) -> list[TraceEventTreeNode]:
    """Get trace events for a session as a nested tree structure."""
    events = await get_events_for_session(db, session_id)
    # Build lookup dict
    nodes: dict[str, TraceEventTreeNode] = {}
    for e in events:
        nodes[e.id] = TraceEventTreeNode(**e.model_dump(), children=[])

    roots = []
    for node in nodes.values():
        if node.parent_event_id and node.parent_event_id in nodes:
            nodes[node.parent_event_id].children.append(node)
        else:
            roots.append(node)
    return roots
