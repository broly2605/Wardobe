"""Repository for the weather cache."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models.weather import WeatherCache
from app.repositories.base import BaseRepository


class WeatherRepository(BaseRepository[WeatherCache]):
    model = WeatherCache

    async def find_cached(
        self, latitude: Decimal, longitude: Decimal, for_date: date
    ) -> WeatherCache | None:
        """Look up a cached snapshot for the rounded coordinate and date."""
        result = await self.session.execute(
            select(WeatherCache).where(
                WeatherCache.latitude == latitude,
                WeatherCache.longitude == longitude,
                WeatherCache.for_date == for_date,
            )
        )
        return result.scalar_one_or_none()
