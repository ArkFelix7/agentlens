"""Pydantic schemas for the reliability score API."""

from pydantic import BaseModel


class ScoreResponse(BaseModel):
    session_id: str
    score: int
    grade: str
    color: str
    hallucination_count: int
    error_count: int
    mean_step_ms: float
    cost_usd: float
    penalty_breakdown: dict
