"""REST endpoints for memory inspection."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.memory import MemoryEntryCreate, MemoryEntryUpdate, MemoryEntryResponse, MemoryListResponse, MemoryKeyResponse
from src.services import memory_service
from src.websocket.manager import manager

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryEntryResponse)
async def create_memory(
    data: MemoryEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new memory entry."""
    entry = await memory_service.create_memory_entry(db, data)
    # Broadcast memory update to dashboard
    await manager.broadcast_to_dashboards({
        "type": "memory_update",
        "data": entry.model_dump(mode="json"),
    })
    return entry


@router.get("/{session_id}", response_model=MemoryListResponse)
async def get_memory(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all memory entries for a session."""
    return await memory_service.get_memory_for_session(db, session_id)


@router.get("/{session_id}/{memory_key}", response_model=MemoryKeyResponse)
async def get_memory_key(
    session_id: str,
    memory_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific memory key with version history."""
    result = await memory_service.get_memory_by_key(db, session_id, memory_key)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory key not found")
    return result


@router.patch("/entry/{entry_id}", response_model=MemoryEntryResponse)
async def update_memory_entry(
    entry_id: str,
    data: MemoryEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the content of a memory entry."""
    entry = await memory_service.update_memory_entry(db, entry_id, data.content)
    if entry is None:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    await manager.broadcast_to_dashboards({"type": "memory_update", "data": entry.model_dump(mode="json")})
    return entry


@router.delete("/entry/{entry_id}", status_code=204)
async def delete_memory_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a memory entry."""
    deleted = await memory_service.delete_memory_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    await manager.broadcast_to_dashboards({"type": "memory_deleted", "entry_id": entry_id})
