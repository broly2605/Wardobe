"""Repository for outfits."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.outfit import Outfit
from app.repositories.base import BaseRepository


class OutfitRepository(BaseRepository[Outfit]):
    model = Outfit

    async def get(self, obj_id: int) -> Outfit | None:
        """Fetch by id via a SELECT so the ``selectin`` relationship chain
        (items -> item -> category/colors/tags) is eagerly loaded.

        ``session.get`` returns a just-added instance from the identity map with
        its relationships unloaded, which then raises ``MissingGreenlet`` when
        touched during async serialization. ``populate_existing`` forces the
        loaders to run for an already-tracked instance.
        """
        result = await self.session.execute(
            select(Outfit)
            .where(Outfit.id == obj_id)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, *, limit: int = 100, offset: int = 0
    ) -> tuple[list[Outfit], int]:
        rows = await self.session.execute(
            select(Outfit)
            .order_by(Outfit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        total = await self.session.execute(select(func.count()).select_from(Outfit))
        return list(rows.scalars().all()), int(total.scalar_one())
