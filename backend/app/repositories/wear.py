"""Repository for wear logs and usage aggregations."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.wear import WearLog
from app.repositories.base import BaseRepository


class WearLogRepository(BaseRepository[WearLog]):
    model = WearLog

    async def total_wears(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(WearLog)
        )
        return int(result.scalar_one())

    async def recent(self, limit: int = 30) -> list[WearLog]:
        result = await self.session.execute(
            select(WearLog).order_by(WearLog.worn_on.desc()).limit(limit)
        )
        return list(result.scalars().all())
