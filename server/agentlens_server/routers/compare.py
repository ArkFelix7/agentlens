"""Model comparison endpoint — re-runs a session against a different model."""

import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agentlens_server.database import get_db
from agentlens_server.services.compare_service import run_comparison

logger = logging.getLogger(__name__)
router = APIRouter(tags=["compare"])


class CompareRequest(BaseModel):
    target_model: str
    provider: str = "openai"      # openai | anthropic | google
    api_key: str                  # NEVER stored or logged
    max_steps: int = 20


class CompareStepResult(BaseModel):
    event_id: str
    event_name: str
    original_model: str
    original_output: str
    original_cost_usd: float
    original_latency_ms: float
    original_hallucinations: int
    comparison_model: str
    comparison_output: str
    comparison_cost_usd: float
    comparison_latency_ms: float
    comparison_hallucinations: int
    output_diff_score: float


class CompareResponse(BaseModel):
    session_id: str
    original_model: str
    comparison_model: str
    total_original_cost_usd: float
    total_comparison_cost_usd: float
    cost_delta_pct: float
    original_hallucination_count: int
    comparison_hallucination_count: int
    steps: List[CompareStepResult]
    recommendation: str


@router.post("/compare/{session_id}", response_model=CompareResponse)
async def compare_models(
    session_id: str,
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Re-run a session's LLM calls against a different model and compare results.

    The api_key field is used only for the comparison calls — it is never persisted
    to the database, never logged, and never broadcast over WebSocket.
    """
    # Validate max_steps range
    max_steps = max(1, min(body.max_steps, 50))

    result = await run_comparison(
        session_id=session_id,
        target_model=body.target_model,
        provider=body.provider,
        api_key=body.api_key,   # passed through; never stored
        max_steps=max_steps,
        db=db,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or has no LLM call events",
        )

    return CompareResponse(
        session_id=result["session_id"],
        original_model=result["original_model"],
        comparison_model=result["comparison_model"],
        total_original_cost_usd=result["total_original_cost_usd"],
        total_comparison_cost_usd=result["total_comparison_cost_usd"],
        cost_delta_pct=result["cost_delta_pct"],
        original_hallucination_count=result["original_hallucination_count"],
        comparison_hallucination_count=result["comparison_hallucination_count"],
        steps=[CompareStepResult(**s) for s in result["steps"]],
        recommendation=result["recommendation"],
    )
