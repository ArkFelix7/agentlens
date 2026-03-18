"""Reliability score endpoints — JSON score and embeddable SVG badge."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from agentlens_server.database import get_db
from agentlens_server.schemas.score import ScoreResponse
from agentlens_server.services.score_service import compute_score

router = APIRouter(tags=["score"])


@router.get("/score/{session_id}", response_model=ScoreResponse)
async def get_score(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the reliability score for a session."""
    result = await compute_score(session_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return ScoreResponse(
        session_id=result.session_id,
        score=result.score,
        grade=result.grade,
        color=result.color,
        hallucination_count=result.hallucination_count,
        error_count=result.error_count,
        mean_step_ms=result.mean_step_ms,
        cost_usd=result.cost_usd,
        penalty_breakdown=result.penalty_breakdown,
    )


@router.get("/score/{session_id}/badge.svg")
async def get_score_badge(session_id: str, db: AsyncSession = Depends(get_db)):
    """Returns an embeddable SVG badge showing the reliability score."""
    result = await compute_score(session_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")

    score = result.score
    grade = result.grade
    color = result.color
    label = "AgentLens"
    value = f"{score}/100  {grade}"

    # Approximate text widths (monospace 11px ~ 6.5px per char)
    label_w = max(len(label) * 7 + 16, 90)
    value_w = max(len(value) * 7 + 16, 80)
    total_w = label_w + value_w

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20">
  <defs>
    <linearGradient id="s" x2="0" y2="100%">
      <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
      <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="r">
      <rect width="{total_w}" height="20" rx="3" fill="#fff"/>
    </clipPath>
  </defs>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="20" fill="#1e1e2e"/>
    <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="'JetBrains Mono',monospace,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_w // 2}" y="14" fill="#000" fill-opacity=".3">{label}</text>
    <text x="{label_w // 2}" y="13">{label}</text>
    <text x="{label_w + value_w // 2}" y="14" fill="#000" fill-opacity=".3">{value}</text>
    <text x="{label_w + value_w // 2}" y="13">{value}</text>
  </g>
</svg>"""

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "max-age=60, s-maxage=60",
            "Content-Type": "image/svg+xml",
        },
    )
