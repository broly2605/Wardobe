"""Weather cache — persisted Open-Meteo lookups.

Weather is fetched from Open-Meteo and cached here keyed by rounded
latitude/longitude and date, so repeated requests on the same day for the same
location avoid redundant external calls. The raw provider payload is retained in
JSONB for debugging and future enrichment.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import WeatherCondition, string_enum


class WeatherCache(Base, PrimaryKeyMixin, TimestampMixin):
    """A cached daily weather snapshot for a coordinate."""

    __tablename__ = "weather_cache"
    __table_args__ = (
        UniqueConstraint("latitude", "longitude", "for_date", name="uq_weather_loc_date"),
    )

    # Coordinates are stored rounded (see the weather service) to maximize cache
    # hits for nearby requests. NUMERIC keeps the rounding exact.
    latitude: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    for_date: Mapped[date] = mapped_column(Date, nullable=False)

    label: Mapped[str | None] = mapped_column(String(120))  # e.g. resolved place name
    condition: Mapped[WeatherCondition] = mapped_column(
        string_enum(WeatherCondition, "weather_condition_enum"), nullable=False
    )
    temp_min_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_max_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_current_c: Mapped[float | None] = mapped_column(Float)
    feels_like_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    precipitation_prob: Mapped[float | None] = mapped_column(Float)
    wind_kph: Mapped[float | None] = mapped_column(Float)
    uv_index: Mapped[float | None] = mapped_column(Float)

    raw: Mapped[dict | None] = mapped_column(JSONB)
