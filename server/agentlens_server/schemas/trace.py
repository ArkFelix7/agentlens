"""Pydantic schemas for trace event API endpoints."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class TraceEventCreate(BaseModel):
    id: Optional[str] = None           # Auto-generated (ULID) if not provided
    session_id: str
    parent_event_id: Optional[str] = None
    event_type: str                    # llm_call, tool_call, decision, memory_read, memory_write, user_input, error
    event_name: str
    timestamp: Optional[datetime] = None
    duration_ms: float = 0.0
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    model: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: Optional[float] = None   # Auto-calculated from model+tokens if not provided
    status: str = "success"
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class TraceEventResponse(BaseModel):
    id: str
    session_id: str
    parent_event_id: Optional[str]
    event_type: str
    event_name: str
    timestamp: datetime
    duration_ms: float
    input_data: Optional[Any]
    output_data: Optional[Any]
    model: Optional[str]
    tokens_input: int
    tokens_output: int
    cost_usd: float
    status: str
    error_message: Optional[str]
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class TraceIngestRequest(BaseModel):
    session_id: str
    events: list[TraceEventCreate]


class TraceIngestResponse(BaseModel):
    ingested: int
    session_id: str


class TraceEventTreeNode(TraceEventResponse):
    children: list["TraceEventTreeNode"] = []

    class Config:
        from_attributes = True
