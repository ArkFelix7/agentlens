"""REST endpoints for cost analysis."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.cost import CostBreakdown, CostHotspotsResponse, CostSuggestionsResponse
from src.services import cost_service

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/{session_id}", response_model=CostBreakdown)
async def get_cost_breakdown(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full cost breakdown for a session."""
    return await cost_service.get_cost_breakdown(db, session_id)


@router.get("/{session_id}/hotspots", response_model=CostHotspotsResponse)
async def get_cost_hotspots(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the most expensive steps in a session."""
    return await cost_service.get_cost_hotspots(db, session_id)


@router.get("/{session_id}/suggestions", response_model=CostSuggestionsResponse)
async def get_cost_suggestions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get cost optimization suggestions for a session."""
    return await cost_service.get_cost_suggestions(db, session_id)
