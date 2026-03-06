"""Cost calculation and analysis service."""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.trace_event import TraceEvent
from src.schemas.cost import (
    CostBreakdown, ModelCostDetail, StepCost, CostTimelinePoint,
    CostHotspot, CostHotspotsResponse, CostSuggestion, CostSuggestionsResponse,
)
from src.utils.pricing import calculate_cost, get_cheaper_alternative, estimate_savings, estimate_savings_pct

logger = logging.getLogger(__name__)


async def get_cost_breakdown(db: AsyncSession, session_id: str) -> CostBreakdown:
    """Compute full cost breakdown for a session."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .order_by(TraceEvent.timestamp)
    )
    events = result.scalars().all()

    total_usd = 0.0
    by_model: dict[str, dict] = {}
    by_step: list[StepCost] = []
    timeline: list[CostTimelinePoint] = []
    cumulative = 0.0

    for e in events:
        total_usd += e.cost_usd
        cumulative += e.cost_usd

        if e.model:
            if e.model not in by_model:
                by_model[e.model] = {"cost": 0.0, "tokens_input": 0, "tokens_output": 0, "call_count": 0}
            by_model[e.model]["cost"] += e.cost_usd
            by_model[e.model]["tokens_input"] += e.tokens_input
            by_model[e.model]["tokens_output"] += e.tokens_output
            by_model[e.model]["call_count"] += 1

        if e.cost_usd > 0:
            by_step.append(StepCost(
                event_id=e.id,
                event_name=e.event_name,
                model=e.model or "",
                cost=e.cost_usd,
                tokens=e.tokens_input + e.tokens_output,
                percentage=0.0,  # will fill in below
            ))

        timeline.append(CostTimelinePoint(
            timestamp=e.timestamp.isoformat(),
            cumulative_cost=cumulative,
            event_name=e.event_name,
        ))

    # Fill in percentages
    if total_usd > 0:
        for step in by_step:
            step.percentage = (step.cost / total_usd) * 100

    # Sort by_step descending
    by_step.sort(key=lambda s: s.cost, reverse=True)

    return CostBreakdown(
        total_usd=total_usd,
        by_model={k: ModelCostDetail(**v) for k, v in by_model.items()},
        by_step=by_step,
        timeline=timeline,
    )


async def get_cost_hotspots(db: AsyncSession, session_id: str) -> CostHotspotsResponse:
    """Return the most expensive steps in a session."""
    breakdown = await get_cost_breakdown(db, session_id)
    total = breakdown.total_usd

    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .where(TraceEvent.cost_usd > 0)
        .order_by(TraceEvent.cost_usd.desc())
        .limit(20)
    )
    events = result.scalars().all()

    hotspots = [
        CostHotspot(
            event_id=e.id,
            event_name=e.event_name,
            model=e.model or "",
            tokens_input=e.tokens_input,
            tokens_output=e.tokens_output,
            cost_usd=e.cost_usd,
            percentage_of_total=(e.cost_usd / total * 100) if total > 0 else 0.0,
        )
        for e in events
    ]
    return CostHotspotsResponse(hotspots=hotspots)


async def get_cost_suggestions(db: AsyncSession, session_id: str) -> CostSuggestionsResponse:
    """Generate cost optimization suggestions for a session."""
    result = await db.execute(
        select(TraceEvent)
        .where(TraceEvent.session_id == session_id)
        .where(TraceEvent.event_type == "llm_call")
    )
    events = result.scalars().all()

    suggestions = []
    seen_hashes = set()

    for e in events:
        if not e.model:
            continue
        # Suggestion: expensive model for small output
        if e.model in ["gpt-4o", "gpt-4", "claude-opus-4-6"] and e.tokens_output < 200:
            alt = get_cheaper_alternative(e.model)
            if alt != e.model:
                savings = estimate_savings(e.model, e.tokens_input, e.tokens_output)
                pct = estimate_savings_pct(e.model, e.tokens_input, e.tokens_output)
                suggestions.append(CostSuggestion(
                    event_id=e.id,
                    current_model=e.model,
                    suggested_model=alt,
                    current_cost=e.cost_usd,
                    estimated_savings=savings,
                    reason=(
                        f"This step produced only {e.tokens_output} output tokens. "
                        f"A smaller model could handle this at ~{pct}% less cost."
                    ),
                ))

        # Suggestion: detect repeated identical inputs (suggest caching)
        input_hash = hash(e.input_data or "")
        if input_hash in seen_hashes and e.cost_usd > 0:
            suggestions.append(CostSuggestion(
                event_id=e.id,
                current_model=e.model,
                suggested_model=e.model,
                current_cost=e.cost_usd,
                estimated_savings=e.cost_usd,
                reason="This LLM call appears identical to a previous call. Consider caching the result.",
            ))
        seen_hashes.add(input_hash)

    return CostSuggestionsResponse(suggestions=suggestions)
