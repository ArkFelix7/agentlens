"""REST endpoints for session management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.schemas.session import SessionCreate, SessionResponse, SessionListResponse
from src.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new session."""
    return await session_service.create_session(db, data)


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all sessions."""
    sessions = await session_service.get_sessions(db, limit=limit, offset=offset, status=status)
    total = await session_service.get_session_count(db)
    return SessionListResponse(sessions=sessions, total=total)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a session by ID."""
    session = await session_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its events."""
    deleted = await session_service.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}
