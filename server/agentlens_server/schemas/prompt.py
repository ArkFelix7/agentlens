"""Pydantic schemas for prompt version control API."""

from typing import Optional, List
from pydantic import BaseModel


class PromptVersionCreate(BaseModel):
    content: str
    label: Optional[str] = None
    commit_message: Optional[str] = None


class PromptVersionResponse(BaseModel):
    id: str
    prompt_id: str
    version: int
    content: str
    label: Optional[str]
    commit_message: Optional[str]
    created_at: str
    total_uses: int
    avg_cost_usd: Optional[float]
    avg_latency_ms: Optional[float]
    hallucination_rate: Optional[float]


class PromptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    initial_content: Optional[str] = None
    initial_commit_message: Optional[str] = "Initial version"


class PromptResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    current_version: int
    created_at: str
    updated_at: str
    versions: List[PromptVersionResponse] = []
