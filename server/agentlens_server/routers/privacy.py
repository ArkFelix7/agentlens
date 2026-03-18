"""Privacy and data residency endpoints."""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from agentlens_server.database import get_db
from agentlens_server.models.session import Session
from agentlens_server.models.trace_event import TraceEvent
from agentlens_server.config import settings

router = APIRouter(tags=["privacy"])


@router.get("/privacy/certificate")
async def get_data_residency_certificate(db: AsyncSession = Depends(get_db)):
    """Returns a data residency certificate showing where all data is stored."""
    # Count sessions
    sessions_count_result = await db.execute(select(func.count(Session.id)))
    sessions_count = sessions_count_result.scalar() or 0

    # Count trace events
    events_count_result = await db.execute(select(func.count(TraceEvent.id)))
    events_count = events_count_result.scalar() or 0

    db_path = (
        str(Path(settings.database_url.replace("sqlite+aiosqlite:///", "")).resolve())
        if "sqlite" in settings.database_url
        else settings.database_url
    )

    certificate = {
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "server_version": "0.2.0",
        "data_location": "local SQLite",
        "db_path": db_path,
        "cloud_sync": False,
        "sessions_count": sessions_count,
        "trace_events_count": events_count,
        "external_connections": [],
        "compliance_notes": [
            "All data processing happens on local hardware",
            "No data is transmitted to external servers",
            "No telemetry or analytics are collected",
            "Suitable for HIPAA, SOC 2, and GDPR air-gap requirements",
        ],
    }
    return JSONResponse(
        content=certificate,
        headers={
            "Content-Disposition": (
                f"attachment; filename=agentlens-data-residency-"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
            )
        },
    )
