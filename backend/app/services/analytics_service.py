"""Analytics service — aggregates wardrobe usage into dashboard metrics.

Queries are expressed with SQLAlchemy Core against the ORM tables so the heavy
lifting (grouping, counting) happens in Postgres rather than in Python.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.associations import item_colors
from app.models.clothing import ClothingItem
from app.models.enums import Formality
from app.models.outfit import Outfit
from app.models.reference import Category, Color
from app.models.wear import WearLog
from app.schemas.analytics import (
    AnalyticsOverview,
    ColorSlice,
    CountByLabel,
    WardrobeStats,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self, *, top_n: int = 5) -> AnalyticsOverview:
        stats = await self._stats()
        return AnalyticsOverview(
            stats=stats,
            category_breakdown=await self._category_breakdown(),
            color_breakdown=await self._color_breakdown(),
            formality_breakdown=await self._formality_breakdown(),
            most_worn=await self._items_by_wear(descending=True, limit=top_n),
            least_worn=await self._items_by_wear(descending=False, limit=top_n),
        )

    async def _stats(self) -> WardrobeStats:
        total_items = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(ClothingItem)
                )
            ).scalar_one()
        )
        archived = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(ClothingItem)
                    .where(ClothingItem.is_archived.is_(True))
                )
            ).scalar_one()
        )
        total_outfits = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(Outfit)
                )
            ).scalar_one()
        )
        total_wears = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(WearLog)
                )
            ).scalar_one()
        )
        never_worn = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(ClothingItem)
                    .where(ClothingItem.wear_count == 0)
                )
            ).scalar_one()
        )
        worn_at_least_once = total_items - never_worn
        utilization = (worn_at_least_once / total_items) if total_items else 0.0

        return WardrobeStats(
            total_items=total_items,
            total_outfits=total_outfits,
            total_wears=total_wears,
            archived_items=archived,
            utilization_rate=round(utilization, 4),
            never_worn_count=never_worn,
        )

    async def _category_breakdown(self) -> list[CountByLabel]:
        rows = await self.session.execute(
            select(Category.name, func.count(ClothingItem.id))
            .join(ClothingItem, ClothingItem.category_id == Category.id)
            .group_by(Category.name)
            .order_by(func.count(ClothingItem.id).desc())
        )
        return [CountByLabel(label=name, count=int(count)) for name, count in rows]

    async def _color_breakdown(self) -> list[ColorSlice]:
        rows = await self.session.execute(
            select(Color.name, Color.hex, func.count(item_colors.c.item_id))
            .join(item_colors, item_colors.c.color_id == Color.id)
            .group_by(Color.name, Color.hex)
            .order_by(func.count(item_colors.c.item_id).desc())
        )
        return [
            ColorSlice(label=name, hex=hex_, count=int(count))
            for name, hex_, count in rows
        ]

    async def _formality_breakdown(self) -> list[CountByLabel]:
        rows = await self.session.execute(
            select(ClothingItem.formality, func.count(ClothingItem.id))
            .group_by(ClothingItem.formality)
            .order_by(func.count(ClothingItem.id).desc())
        )
        return [
            CountByLabel(
                label=formality.value if isinstance(formality, Formality) else str(formality),
                count=int(count),
            )
            for formality, count in rows
        ]

    async def _items_by_wear(
        self, *, descending: bool, limit: int
    ) -> list[ClothingItem]:
        order = (
            ClothingItem.wear_count.desc()
            if descending
            else ClothingItem.wear_count.asc()
        )
        rows = await self.session.execute(
            select(ClothingItem)
            .where(ClothingItem.is_archived.is_(False))
            .order_by(order, ClothingItem.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())
