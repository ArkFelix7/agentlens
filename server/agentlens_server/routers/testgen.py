"""Test generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from agentlens_server.database import get_db
from agentlens_server.services.testgen_service import generate_test_file

router = APIRouter(tags=["testgen"])


class TestGenResponse(BaseModel):
    session_id: str
    agent_name: str
    filename: str
    test_count: int
    content: str
    generated_at: str


@router.get("/testgen/{session_id}", response_model=TestGenResponse)
async def get_test_file(session_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return test file content as JSON."""
    result = await generate_test_file(session_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return TestGenResponse(**result)


@router.get("/testgen/{session_id}/download")
async def download_test_file(session_id: str, db: AsyncSession = Depends(get_db)):
    """Download generated test file as a .py file."""
    result = await generate_test_file(session_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(
        content=result["content"].encode("utf-8"),
        media_type="text/x-python",
        headers={
            "Content-Disposition": f'attachment; filename="{result["filename"]}"',
        },
    )
