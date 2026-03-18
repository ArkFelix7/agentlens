"""REST endpoints for session management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel

from agentlens_server.database import get_db
from agentlens_server.models.session import Session
from agentlens_server.schemas.session import SessionCreate, SessionResponse, SessionListResponse
from agentlens_server.services import session_service

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


# F9: Multi-Agent Coordination Map — topology models and endpoint

class AgentTopologyNode(BaseModel):
    session_id: str
    agent_name: str
    agent_id: Optional[str]
    agent_role: Optional[str]
    total_cost_usd: float
    total_events: int
    status: str


class AgentTopologyEdge(BaseModel):
    source_session_id: str
    target_session_id: str


class AgentTopologyResponse(BaseModel):
    root_session_id: str
    nodes: List[AgentTopologyNode]
    edges: List[AgentTopologyEdge]


@router.get("/{session_id}/topology", response_model=AgentTopologyResponse)
async def get_session_topology(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the multi-agent coordination topology rooted at this session.

    Performs a BFS over parent_session_id to find all connected agents.
    """
    # BFS to find all sessions in the same agent topology
    visited: set[str] = set()
    queue: list[str] = [session_id]
    all_sessions: list = []

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        sess_result = await db.execute(
            select(Session).where(Session.id == current_id)
        )
        sess = sess_result.scalar_one_or_none()
        if sess:
            all_sessions.append(sess)
            # Find children
            children_result = await db.execute(
                select(Session).where(Session.parent_session_id == current_id)
            )
            for child in children_result.scalars().all():
                if child.id not in visited:
                    queue.append(child.id)
            # Find parent
            if sess.parent_session_id and sess.parent_session_id not in visited:
                queue.append(sess.parent_session_id)

    nodes = [
        AgentTopologyNode(
            session_id=s.id,
            agent_name=s.agent_name or "agent",
            agent_id=s.agent_id if hasattr(s, "agent_id") else None,
            agent_role=s.agent_role if hasattr(s, "agent_role") else None,
            total_cost_usd=float(s.total_cost_usd or 0),
            total_events=s.total_events or 0,
            status=s.status or "unknown",
        )
        for s in all_sessions
    ]

    edges = [
        AgentTopologyEdge(
            source_session_id=s.parent_session_id,
            target_session_id=s.id,
        )
        for s in all_sessions
        if s.parent_session_id and s.parent_session_id in visited
    ]

    return AgentTopologyResponse(
        root_session_id=session_id,
        nodes=nodes,
        edges=edges,
    )
