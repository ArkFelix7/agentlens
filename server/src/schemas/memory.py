"""Pydantic schemas for memory API endpoints."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MemoryEntryUpdate(BaseModel):
    content: str


class MemoryEntryCreate(BaseModel):
    session_id: str
    agent_id: str = "default"
    memory_key: str
    content: str
    action: str  # created, updated, accessed, deleted
    influenced_events: Optional[list[str]] = None
    metadata: Optional[dict] = None


class MemoryEntryResponse(BaseModel):
    id: str
    session_id: str
    agent_id: str
    memory_key: str
    content: str
    action: str
    version: int
    timestamp: datetime
    influenced_events: Optional[list[str]]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    entries: list[MemoryEntryResponse]


class MemoryKeyResponse(BaseModel):
    current: MemoryEntryResponse
    history: list[MemoryEntryResponse]
