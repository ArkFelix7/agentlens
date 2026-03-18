"""Computes the AgentLens Reliability Score for a session (0-100)."""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select, func

from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.models.hallucination_alert import HallucinationAlert
from agentlens_server.models.session import Session


@dataclass
class ScoreResult:
    session_id: str
    score: int
    grade: str
    color: str
    hallucination_count: int
    error_count: int
    mean_step_ms: float
    cost_usd: float
    penalty_breakdown: dict = field(default_factory=dict)


_GRADE_COLORS = {
    "A": "#22c55e",
    "B": "#6366f1",
    "C": "#eab308",
    "D": "#ef4444",
}


def _grade(score: int) -> tuple[str, str]:
    if score >= 90:
        return "A", _GRADE_COLORS["A"]
    elif score >= 75:
        return "B", _GRADE_COLORS["B"]
    elif score >= 60:
        return "C", _GRADE_COLORS["C"]
    else:
        return "D", _GRADE_COLORS["D"]


async def compute_score(session_id: str, db: DBSession) -> Optional[ScoreResult]:
    """Compute reliability score for a session. Returns None if session not found."""

    # Fetch session for cost
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        return None

    # Count hallucinations
    halluc_result = await db.execute(
        select(func.count(HallucinationAlert.id)).where(
            HallucinationAlert.session_id == session_id
        )
    )
    hallucination_count = halluc_result.scalar() or 0

    # Count error events
    error_result = await db.execute(
        select(func.count(TraceEvent.id)).where(
            TraceEvent.session_id == session_id,
            TraceEvent.status == "error",
        )
    )
    error_count = error_result.scalar() or 0

    # Mean step duration
    duration_result = await db.execute(
        select(func.avg(TraceEvent.duration_ms)).where(
            TraceEvent.session_id == session_id
        )
    )
    mean_step_ms = float(duration_result.scalar() or 0.0)

    cost_usd = float(session.total_cost_usd or 0.0)

    # Scoring formula
    score = 100.0
    penalties: dict = {}

    halluc_penalty = min(hallucination_count * 15, 45)
    if halluc_penalty:
        penalties["hallucinations"] = -halluc_penalty
    score -= halluc_penalty

    error_penalty = min(error_count * 10, 30)
    if error_penalty:
        penalties["errors"] = -error_penalty
    score -= error_penalty

    if mean_step_ms > 10_000:
        penalties["high_latency"] = -5
        score -= 5

    bonus = 0
    if hallucination_count == 0 and error_count == 0:
        bonus = 5
        penalties["zero_issues_bonus"] = +5
    score += bonus

    final_score = max(0, min(100, round(score)))
    grade, color = _grade(final_score)

    return ScoreResult(
        session_id=session_id,
        score=final_score,
        grade=grade,
        color=color,
        hallucination_count=hallucination_count,
        error_count=error_count,
        mean_step_ms=mean_step_ms,
        cost_usd=cost_usd,
        penalty_breakdown=penalties,
    )
