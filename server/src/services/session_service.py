"""Session CRUD service."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ulid import ULID

from src.models.session import Session
from src.schemas.session import SessionCreate, SessionResponse, SessionListResponse

logger = logging.getLogger(__name__)


def _orm_to_response(session: Session) -> SessionResponse:
    metadata = None
    if session.metadata_:
        try:
            metadata = json.loads(session.metadata_)
        except (json.JSONDecodeError, TypeError):
            metadata = None
    return SessionResponse(
        id=session.id,
        agent_name=session.agent_name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_events=session.total_events,
        total_cost_usd=session.total_cost_usd,
        total_tokens_input=session.total_tokens_input,
        total_tokens_output=session.total_tokens_output,
        status=session.status,
        metadata=metadata,
    )


async def create_session(db: AsyncSession, data: SessionCreate) -> SessionResponse:
    """Create a new session."""
    session_id = data.id or str(ULID())
    session = Session(
        id=session_id,
        agent_name=data.agent_name,
        status="active",
        started_at=datetime.now(timezone.utc),
        metadata_=json.dumps(data.metadata) if data.metadata else None,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _orm_to_response(session)


async def get_sessions(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
) -> list[SessionResponse]:
    """List sessions ordered by start time descending."""
    query = select(Session).order_by(Session.started_at.desc()).limit(limit).offset(offset)
    if status:
        query = query.where(Session.status == status)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return [_orm_to_response(s) for s in sessions]


async def get_session_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Session))
    return result.scalar_one()


async def get_session(db: AsyncSession, session_id: str) -> Optional[SessionResponse]:
    """Get a single session by ID."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        return None
    return _orm_to_response(session)


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """Delete a session and all its associated data (cascades)."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        return False
    await db.delete(session)
    await db.commit()
    return True


async def end_session(db: AsyncSession, session_id: str, status: str = "completed") -> Optional[SessionResponse]:
    """Mark a session as ended."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        return None
    session.ended_at = datetime.now(timezone.utc)
    session.status = status
    await db.commit()
    await db.refresh(session)
    return _orm_to_response(session)
