"""Pydantic schemas for hallucination detection API endpoints."""

from pydantic import BaseModel
from datetime import datetime


class HallucinationAlertResponse(BaseModel):
    id: str
    session_id: str
    trace_event_id: str
    source_event_id: str
    severity: str  # critical, warning, info
    description: str
    expected_value: str
    actual_value: str
    similarity_score: float
    detected_at: datetime

    class Config:
        from_attributes = True


class HallucinationSummary(BaseModel):
    total: int
    critical: int
    warning: int
    info: int


class HallucinationListResponse(BaseModel):
    alerts: list[HallucinationAlertResponse]
    summary: HallucinationSummary


class HallucinationCheckRequest(BaseModel):
    session_id: str
