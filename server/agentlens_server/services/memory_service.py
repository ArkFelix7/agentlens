"""Memory entry ingestion and retrieval service."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ulid import ULID

from agentlens_server.models.memory_entry import MemoryEntry
from agentlens_server.models.session import Session
from agentlens_server.schemas.memory import MemoryEntryCreate, MemoryEntryResponse, MemoryListResponse, MemoryKeyResponse

logger = logging.getLogger(__name__)


def _orm_to_response(entry: MemoryEntry) -> MemoryEntryResponse:
    influenced = None
    if entry.influenced_events:
        try:
            influenced = json.loads(entry.influenced_events)
        except (json.JSONDecodeError, TypeError):
            influenced = None
    metadata = None
    if entry.metadata_:
        try:
            metadata = json.loads(entry.metadata_)
        except (json.JSONDecodeError, TypeError):
            metadata = None
    return MemoryEntryResponse(
        id=entry.id,
        session_id=entry.session_id,
        agent_id=entry.agent_id,
        memory_key=entry.memory_key,
        content=entry.content,
        action=entry.action,
        version=entry.version,
        timestamp=entry.timestamp,
        influenced_events=influenced,
        metadata=metadata,
    )


async def create_memory_entry(db: AsyncSession, data: MemoryEntryCreate) -> MemoryEntryResponse:
    """Create a new memory entry with auto-versioning. Auto-creates session if it doesn't exist."""
    # Ensure session exists (mirrors trace_service.ingest_events behaviour)
    result = await db.execute(select(Session).where(Session.id == data.session_id))
    if result.scalar_one_or_none() is None:
        db.add(Session(id=data.session_id, agent_name="unnamed", status="active"))

    # Get current version for this memory_key in this session
    result = await db.execute(
        select(MemoryEntry)
        .where(MemoryEntry.session_id == data.session_id)
        .where(MemoryEntry.memory_key == data.memory_key)
        .order_by(MemoryEntry.version.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    version = (latest.version + 1) if latest else 1

    entry = MemoryEntry(
        id=str(ULID()),
        session_id=data.session_id,
        agent_id=data.agent_id,
        memory_key=data.memory_key,
        content=data.content,
        action=data.action,
        version=version,
        timestamp=datetime.now(timezone.utc),
        influenced_events=json.dumps(data.influenced_events) if data.influenced_events else None,
        metadata_=json.dumps(data.metadata) if data.metadata else None,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return _orm_to_response(entry)


async def get_memory_for_session(db: AsyncSession, session_id: str) -> MemoryListResponse:
    """Get all memory entries for a session."""
    result = await db.execute(
        select(MemoryEntry)
        .where(MemoryEntry.session_id == session_id)
        .order_by(MemoryEntry.timestamp.desc())
    )
    entries = result.scalars().all()
    return MemoryListResponse(entries=[_orm_to_response(e) for e in entries])


async def update_memory_entry(db: AsyncSession, entry_id: str, content: str) -> Optional[MemoryEntryResponse]:
    """Update the content of a memory entry by ID."""
    entry = await db.get(MemoryEntry, entry_id)
    if entry is None:
        return None
    entry.content = content
    entry.action = "updated"
    await db.commit()
    await db.refresh(entry)
    return _orm_to_response(entry)


async def delete_memory_entry(db: AsyncSession, entry_id: str) -> bool:
    """Delete a memory entry by ID."""
    entry = await db.get(MemoryEntry, entry_id)
    if entry is None:
        return False
    await db.delete(entry)
    await db.commit()
    return True


async def get_memory_by_key(
    db: AsyncSession, session_id: str, memory_key: str
) -> MemoryKeyResponse:
    """Get a specific memory key with full version history."""
    result = await db.execute(
        select(MemoryEntry)
        .where(MemoryEntry.session_id == session_id)
        .where(MemoryEntry.memory_key == memory_key)
        .order_by(MemoryEntry.version.desc())
    )
    entries = result.scalars().all()
    if not entries:
        return None
    return MemoryKeyResponse(
        current=_orm_to_response(entries[0]),
        history=[_orm_to_response(e) for e in entries[1:]],
    )
