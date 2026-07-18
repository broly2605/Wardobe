"""Repository for clothing items, including filtered/paginated queries."""

from __future__ import annotations

from sqlalchemy import Select, func, select

from app.models.clothing import ClothingItem
from app.models.enums import Formality, Season
from app.repositories.base import BaseRepository


class ClothingItemRepository(BaseRepository[ClothingItem]):
    model = ClothingItem

    async def get(self, obj_id: int) -> ClothingItem | None:
        """Fetch by id via a SELECT so ``selectin`` relationships (category,
        colors, tags) are eager-loaded.

        ``session.get`` would return a freshly-added instance straight from the
        identity map with its relationships unloaded, which then blows up when
        accessed during async serialization. ``populate_existing`` forces the
        loaders to run even for an instance already tracked by the session.
        """
        result = await self.session.execute(
            select(ClothingItem)
            .where(ClothingItem.id == obj_id)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        stmt: Select,
        *,
        category_id: int | None,
        season: Season | None,
        formality: Formality | None,
        search: str | None,
        include_archived: bool,
    ) -> Select:
        """Apply shared filter predicates to a select statement."""
        if not include_archived:
            stmt = stmt.where(ClothingItem.is_archived.is_(False))
        if category_id is not None:
            stmt = stmt.where(ClothingItem.category_id == category_id)
        if season is not None:
            stmt = stmt.where(ClothingItem.season == season)
        if formality is not None:
            stmt = stmt.where(ClothingItem.formality == formality)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(ClothingItem.name).like(like))
        return stmt

    async def list_filtered(
        self,
        *,
        category_id: int | None = None,
        season: Season | None = None,
        formality: Formality | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ClothingItem], int]:
        """Return a filtered page of items plus the total match count."""
        base = self._apply_filters(
            select(ClothingItem),
            category_id=category_id,
            season=season,
            formality=formality,
            search=search,
            include_archived=include_archived,
        )
        rows = await self.session.execute(
            base.order_by(ClothingItem.created_at.desc()).limit(limit).offset(offset)
        )
        count_stmt = self._apply_filters(
            select(func.count()).select_from(ClothingItem),
            category_id=category_id,
            season=season,
            formality=formality,
            search=search,
            include_archived=include_archived,
        )
        total = await self.session.execute(count_stmt)
        return list(rows.scalars().all()), int(total.scalar_one())

    async def get_many(self, ids: list[int]) -> list[ClothingItem]:
        """Fetch multiple items by id (order not guaranteed)."""
        if not ids:
            return []
        result = await self.session.execute(
            select(ClothingItem).where(ClothingItem.id.in_(ids))
        )
        return list(result.scalars().all())

    async def active_items(self) -> list[ClothingItem]:
        """All non-archived items — used by the recommender."""
        result = await self.session.execute(
            select(ClothingItem).where(ClothingItem.is_archived.is_(False))
        )
        return list(result.scalars().all())
