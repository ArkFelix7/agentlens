"""Prompt version control endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentlens_server.database import get_db
from agentlens_server.models.prompt import Prompt
from agentlens_server.models.prompt_version import PromptVersion
from agentlens_server.schemas.prompt import (
    PromptCreate, PromptVersionCreate, PromptResponse, PromptVersionResponse
)
from agentlens_server.services.prompt_service import (
    create_prompt, get_prompt_by_name, add_version, promote_version
)

router = APIRouter(tags=["prompts"])


@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prompt).order_by(Prompt.created_at))
    prompts = result.scalars().all()
    responses = []
    for p in prompts:
        v_result = await db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == p.id)
            .order_by(PromptVersion.version)
        )
        versions = v_result.scalars().all()
        responses.append(
            PromptResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                current_version=p.current_version,
                created_at=p.created_at.isoformat() if p.created_at else "",
                updated_at=p.updated_at.isoformat() if p.updated_at else "",
                versions=[
                    PromptVersionResponse(
                        id=v.id,
                        prompt_id=v.prompt_id,
                        version=v.version,
                        content=v.content,
                        label=v.label,
                        commit_message=v.commit_message,
                        created_at=v.created_at.isoformat() if v.created_at else "",
                        total_uses=v.total_uses or 0,
                        avg_cost_usd=v.avg_cost_usd,
                        avg_latency_ms=v.avg_latency_ms,
                        hallucination_rate=v.hallucination_rate,
                    )
                    for v in versions
                ],
            )
        )
    return responses


@router.post("/prompts", response_model=PromptResponse, status_code=201)
async def create_prompt_endpoint(body: PromptCreate, db: AsyncSession = Depends(get_db)):
    # Check for duplicate name
    existing = await db.execute(select(Prompt).where(Prompt.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Prompt name already exists")
    return await create_prompt(body, db)


@router.get("/prompts/{name}", response_model=PromptResponse)
async def get_prompt(name: str, db: AsyncSession = Depends(get_db)):
    result = await get_prompt_by_name(name, db)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.get("/prompts/{name}/current")
async def get_current_version_text(name: str, db: AsyncSession = Depends(get_db)):
    """Returns the current version's content as plain text."""
    p_result = await db.execute(select(Prompt).where(Prompt.name == name))
    prompt = p_result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    v_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == prompt.current_version,
        )
    )
    version = v_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Current version not found")

    return PlainTextResponse(content=version.content)


@router.get("/prompts/{name_or_id}/versions", response_model=List[PromptVersionResponse])
async def list_prompt_versions(name_or_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prompt).where((Prompt.name == name_or_id) | (Prompt.id == name_or_id))
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    v_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version)
    )
    versions = v_result.scalars().all()
    return [
        PromptVersionResponse(
            id=v.id,
            prompt_id=v.prompt_id,
            version=v.version,
            content=v.content,
            label=v.label,
            commit_message=v.commit_message,
            created_at=v.created_at.isoformat() if v.created_at else "",
            total_uses=v.total_uses or 0,
            avg_cost_usd=v.avg_cost_usd,
            avg_latency_ms=v.avg_latency_ms,
            hallucination_rate=v.hallucination_rate,
        )
        for v in versions
    ]


@router.get("/prompts/{name_or_id}/active", response_model=PromptVersionResponse)
async def get_active_version(name_or_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prompt).where((Prompt.name == name_or_id) | (Prompt.id == name_or_id))
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    v_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == prompt.current_version,
        )
    )
    version = v_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="No active version found")
    return PromptVersionResponse(
        id=version.id,
        prompt_id=version.prompt_id,
        version=version.version,
        content=version.content,
        label=version.label,
        commit_message=version.commit_message,
        created_at=version.created_at.isoformat() if version.created_at else "",
        total_uses=version.total_uses or 0,
        avg_cost_usd=version.avg_cost_usd,
        avg_latency_ms=version.avg_latency_ms,
        hallucination_rate=version.hallucination_rate,
    )


@router.post("/prompts/{name_or_id}/versions", response_model=PromptVersionResponse, status_code=201)
async def add_prompt_version(
    name_or_id: str, body: PromptVersionCreate, db: AsyncSession = Depends(get_db)
):
    result = await add_version(name_or_id, body, db)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.patch("/prompts/{name}/versions/{version_num}/promote", response_model=PromptResponse)
async def promote_prompt_version(
    name: str, version_num: int, db: AsyncSession = Depends(get_db)
):
    result = await promote_version(name, version_num, db)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt or version not found")
    return result
