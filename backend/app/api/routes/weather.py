"""Weather endpoint (Open-Meteo backed, DB cached)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import WeatherServiceDep
from app.schemas.weather import WeatherRead

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherRead)
async def get_weather(
    service: WeatherServiceDep,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> WeatherRead:
    """Return today's weather for a coordinate, using the DB cache when fresh."""
    weather = await service.get_weather(latitude, longitude)
    if weather is None:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Weather is currently unavailable. Please try again shortly.",
        )
    return WeatherRead.model_validate(weather)
