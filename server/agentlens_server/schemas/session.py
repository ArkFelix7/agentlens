"""Pydantic schemas for session API endpoints."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    id: Optional[str] = None
    agent_name: str = "unnamed"
    metadata: Optional[dict] = None


class SessionResponse(BaseModel):
    id: str
    agent_name: str
    started_at: datetime
    ended_at: Optional[datetime]
    total_events: int
    total_cost_usd: float
    total_tokens_input: int
    total_tokens_output: int
    status: str
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class SessionEndRequest(BaseModel):
    status: str = "completed"
