"""Repositories for AI memory and recommendations."""

from __future__ import annotations

from sqlalchemy import select

from app.models.ai import AIMemory, Recommendation
from app.repositories.base import BaseRepository


class AIMemoryRepository(BaseRepository[AIMemory]):
    model = AIMemory

    async def list_all(self) -> list[AIMemory]:
        result = await self.session.execute(
            select(AIMemory).order_by(AIMemory.weight.desc(), AIMemory.key)
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> AIMemory | None:
        result = await self.session.execute(
            select(AIMemory).where(AIMemory.key == key)
        )
        return result.scalar_one_or_none()


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    async def recent(self, limit: int = 20) -> list[Recommendation]:
        result = await self.session.execute(
            select(Recommendation)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
