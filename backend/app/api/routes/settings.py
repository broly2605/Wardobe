"""Settings & AI-memory endpoints.

Exposes non-sensitive runtime status (e.g. whether AI is enabled) and CRUD over
the learned style-memory the recommender uses. The OpenAI key itself is never
returned — only whether one is configured.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import MemoryRepoDep
from app.core.config import settings
from app.models.ai import AIMemory
from app.schemas.ai import AIMemoryCreate, AIMemoryRead
from app.schemas.common import Message

router = APIRouter(prefix="/settings", tags=["settings"])


class AppStatus(BaseModel):
    """Client-facing feature flags derived from configuration."""

    ai_enabled: bool
    ai_model: str | None
    weather_provider: str = "open-meteo"
    app_env: str


@router.get("/status", response_model=AppStatus)
async def get_status() -> AppStatus:
    """Report which optional features are active (no secrets exposed)."""
    return AppStatus(
        ai_enabled=settings.ai_enabled,
        ai_model=settings.openai_model if settings.ai_enabled else None,
        app_env=settings.app_env,
    )


@router.get("/memory", response_model=list[AIMemoryRead])
async def list_memory(repo: MemoryRepoDep) -> list[AIMemoryRead]:
    return [AIMemoryRead.model_validate(m) for m in await repo.list_all()]


@router.put("/memory", response_model=AIMemoryRead)
async def upsert_memory(payload: AIMemoryCreate, repo: MemoryRepoDep) -> AIMemoryRead:
    """Create or update a style-memory entry by its key."""
    existing = await repo.get_by_key(payload.key)
    if existing is not None:
        existing.value = payload.value
        existing.description = payload.description
        existing.weight = payload.weight
        await repo.session.flush()
        return AIMemoryRead.model_validate(existing)
    created = await repo.add(AIMemory(**payload.model_dump()))
    return AIMemoryRead.model_validate(created)


@router.delete("/memory/{key}", response_model=Message)
async def delete_memory(key: str, repo: MemoryRepoDep) -> Message:
    existing = await repo.get_by_key(key)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory entry not found.")
    await repo.delete(existing)
    return Message(detail="Memory entry deleted.")
