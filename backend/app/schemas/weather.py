"""Schemas for weather."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.enums import WeatherCondition
from app.schemas.common import ORMModel


class WeatherRead(ORMModel):
    id: int
    latitude: float
    longitude: float
    for_date: date
    label: str | None
    condition: WeatherCondition
    temp_min_c: float
    temp_max_c: float
    temp_current_c: float | None
    feels_like_c: float | None
    humidity_pct: float | None
    precipitation_prob: float | None
    wind_kph: float | None
    uv_index: float | None
