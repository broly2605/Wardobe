"""Repositories for reference data (categories, colors, tags)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.reference import Category, Color, Tag
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def list_ordered(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()


class ColorRepository(BaseRepository[Color]):
    model = Color

    async def list_ordered(self) -> list[Color]:
        result = await self.session.execute(select(Color).order_by(Color.name))
        return list(result.scalars().all())

    async def get_many(self, ids: list[int]) -> list[Color]:
        if not ids:
            return []
        result = await self.session.execute(select(Color).where(Color.id.in_(ids)))
        return list(result.scalars().all())


class TagRepository(BaseRepository[Tag]):
    model = Tag

    async def list_ordered(self) -> list[Tag]:
        result = await self.session.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def get_many(self, ids: list[int]) -> list[Tag]:
        if not ids:
            return []
        result = await self.session.execute(select(Tag).where(Tag.id.in_(ids)))
        return list(result.scalars().all())
