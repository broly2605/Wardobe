"""Generic async repository.

Repositories encapsulate all data-access logic so services and routes never
write raw queries. The generic base covers the common CRUD shape; concrete
repositories subclass it and add model-specific queries.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD helpers shared by all repositories."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, obj_id: int) -> ModelT | None:
        """Fetch a single row by primary key, or ``None``."""
        return await self.session.get(self.model, obj_id)

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """Return a page of rows ordered by primary key."""
        result = await self.session.execute(
            select(self.model).order_by(self.model.id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Total number of rows in the table."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return int(result.scalar_one())

    async def add(self, obj: ModelT) -> ModelT:
        """Persist a new object and flush so its id is populated."""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Delete an object."""
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_by_id(self, obj_id: int) -> None:
        """Delete by primary key without loading the row first."""
        await self.session.execute(
            delete(self.model).where(self.model.id == obj_id)
        )
