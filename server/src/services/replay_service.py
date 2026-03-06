"""Session replay data assembly service."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.trace_event import TraceEvent
from src.schemas.trace import TraceEventResponse
from src.services.trace_service import _orm_to_response

logger = logging.getLogger(__name__)


async def get_replay_data(db: AsyncSession, session_id: str) -> list[TraceEventResponse]:
    """Get ordered trace events for replay. Events returned in chronological order."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .order_by(TraceEvent.timestamp)
    )
    events = result.scalars().all()
    return [_orm_to_response(e) for e in events]
