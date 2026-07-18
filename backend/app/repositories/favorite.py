"""Repository for favorites."""

from __future__ import annotations

from sqlalchemy import select

from app.models.enums import FavoriteTargetType
from app.models.favorite import Favorite
from app.repositories.base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    model = Favorite

    async def list_all(self) -> list[Favorite]:
        result = await self.session.execute(
            select(Favorite).order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def find(
        self, target_type: FavoriteTargetType, target_id: int
    ) -> Favorite | None:
        result = await self.session.execute(
            select(Favorite).where(
                Favorite.target_type == target_type,
                Favorite.target_id == target_id,
            )
        )
        return result.scalar_one_or_none()
