"""Pydantic schemas for cost analysis API endpoints."""

from pydantic import BaseModel
from typing import Optional


class ModelCostDetail(BaseModel):
    cost: float
    tokens_input: int
    tokens_output: int
    call_count: int


class StepCost(BaseModel):
    event_id: str
    event_name: str
    model: str
    cost: float
    tokens: int
    percentage: float


class CostTimelinePoint(BaseModel):
    timestamp: str
    cumulative_cost: float
    event_name: str


class CostBreakdown(BaseModel):
    total_usd: float
    by_model: dict[str, ModelCostDetail]
    by_step: list[StepCost]
    timeline: list[CostTimelinePoint]


class CostHotspot(BaseModel):
    event_id: str
    event_name: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    percentage_of_total: float


class CostHotspotsResponse(BaseModel):
    hotspots: list[CostHotspot]


class CostSuggestion(BaseModel):
    event_id: str
    current_model: str
    suggested_model: str
    current_cost: float
    estimated_savings: float
    reason: str


class CostSuggestionsResponse(BaseModel):
    suggestions: list[CostSuggestion]
