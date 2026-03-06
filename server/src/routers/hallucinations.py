"""REST endpoints for hallucination detection."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.hallucination import (
    HallucinationListResponse,
    HallucinationCheckRequest,
)
from src.services import hallucination_service
from src.websocket.manager import manager

router = APIRouter(prefix="/hallucinations", tags=["hallucinations"])


@router.get("/{session_id}", response_model=HallucinationListResponse)
async def get_hallucinations(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all hallucination alerts for a session."""
    return await hallucination_service.get_hallucinations(db, session_id)


@router.post("/check", response_model=HallucinationListResponse)
async def check_hallucinations(
    request: HallucinationCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger hallucination check for a session."""
    alerts = await hallucination_service.run_hallucination_detection(db, request.session_id)

    # Broadcast any detected hallucinations
    for alert in alerts:
        await manager.broadcast_to_dashboards({
            "type": "hallucination_detected",
            "data": alert.model_dump(mode="json"),
        })

    return await hallucination_service.get_hallucinations(db, request.session_id)
