"""Prompt version control service."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select

from agentlens_server.models.prompt import Prompt
from agentlens_server.models.prompt_version import PromptVersion
from agentlens_server.schemas.prompt import (
    PromptCreate, PromptVersionCreate, PromptResponse, PromptVersionResponse
)
from agentlens_server.utils import new_ulid


def _version_to_response(v: PromptVersion) -> PromptVersionResponse:
    return PromptVersionResponse(
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


def _prompt_to_response(p: Prompt, versions: list[PromptVersion]) -> PromptResponse:
    return PromptResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        current_version=p.current_version,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
        versions=[_version_to_response(v) for v in versions],
    )


async def create_prompt(body: PromptCreate, db: DBSession) -> PromptResponse:
    prompt_id = new_ulid()
    prompt = Prompt(
        id=prompt_id,
        name=body.name,
        description=body.description,
        current_version=1,
    )
    db.add(prompt)

    version = PromptVersion(
        id=new_ulid(),
        prompt_id=prompt_id,
        version=1,
        content=body.initial_content,
        commit_message=body.initial_commit_message or "Initial version",
    )
    db.add(version)
    await db.commit()
    await db.refresh(prompt)
    return _prompt_to_response(prompt, [version])


async def get_prompt_by_name(name: str, db: DBSession) -> Optional[PromptResponse]:
    result = await db.execute(select(Prompt).where(Prompt.name == name))
    prompt = result.scalar_one_or_none()
    if not prompt:
        return None
    versions_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version)
    )
    versions = versions_result.scalars().all()
    return _prompt_to_response(prompt, versions)


async def add_version(
    name: str, body: PromptVersionCreate, db: DBSession
) -> Optional[PromptVersionResponse]:
    result = await db.execute(select(Prompt).where(Prompt.name == name))
    prompt = result.scalar_one_or_none()
    if not prompt:
        return None

    new_version_num = prompt.current_version + 1
    version = PromptVersion(
        id=new_ulid(),
        prompt_id=prompt.id,
        version=new_version_num,
        content=body.content,
        label=body.label,
        commit_message=body.commit_message,
    )
    db.add(version)
    prompt.current_version = new_version_num
    prompt.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(version)
    return _version_to_response(version)


async def promote_version(
    name: str, version_num: int, db: DBSession
) -> Optional[PromptResponse]:
    result = await db.execute(select(Prompt).where(Prompt.name == name))
    prompt = result.scalar_one_or_none()
    if not prompt:
        return None

    # Verify the version exists
    v_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == version_num,
        )
    )
    version = v_result.scalar_one_or_none()
    if not version:
        return None

    prompt.current_version = version_num
    prompt.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Re-fetch all versions
    versions_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version)
    )
    versions = versions_result.scalars().all()
    return _prompt_to_response(prompt, versions)
