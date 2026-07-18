"""Weather service backed by Open-Meteo with DB caching.

Open-Meteo is free and keyless. Results are cached per rounded coordinate and
date in ``weather_cache`` so repeated dashboard loads don't re-hit the API. The
service degrades gracefully: if the network call fails, a cached row (even a
stale one) is returned when available, otherwise ``None``.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import httpx

from app.models.enums import WeatherCondition
from app.models.weather import WeatherCache
from app.repositories.weather import WeatherRepository

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Map Open-Meteo WMO weather codes to our simplified condition buckets.
_WMO_MAP: dict[range, WeatherCondition] = {}


def _condition_from_code(code: int) -> WeatherCondition:
    """Translate a WMO weather code into a :class:`WeatherCondition`."""
    if code == 0:
        return WeatherCondition.CLEAR
    if code in (1, 2, 3):
        return WeatherCondition.CLOUDY
    if code in (45, 48):
        return WeatherCondition.FOG
    if code in (95, 96, 99):
        return WeatherCondition.STORM
    if 71 <= code <= 77 or code in (85, 86):
        return WeatherCondition.SNOW
    if (51 <= code <= 67) or (80 <= code <= 82):
        return WeatherCondition.RAIN
    return WeatherCondition.CLOUDY


def _round_coord(value: float) -> Decimal:
    """Round a coordinate to 2 decimals (~1km) to improve cache hit rate."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class WeatherService:
    """Fetches and caches daily weather for a coordinate."""

    def __init__(self, repo: WeatherRepository) -> None:
        self.repo = repo

    async def get_weather(
        self, latitude: float, longitude: float, for_date: date | None = None
    ) -> WeatherCache | None:
        """Return today's (or ``for_date``) weather, using cache when possible."""
        target = for_date or date.today()
        lat = _round_coord(latitude)
        lon = _round_coord(longitude)

        cached = await self.repo.find_cached(lat, lon, target)
        if cached is not None:
            return cached

        try:
            payload = await self._fetch(float(lat), float(lon))
        except (httpx.HTTPError, KeyError, ValueError):
            # Network/parse failure: nothing cached to fall back on.
            return None

        record = self._build_record(lat, lon, target, payload)
        return await self.repo.add(record)

    async def _fetch(self, latitude: float, longitude: float) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
            "weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,uv_index_max,weather_code",
            "timezone": "auto",
            "forecast_days": 1,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _build_record(
        lat: Decimal, lon: Decimal, target: date, payload: dict
    ) -> WeatherCache:
        daily = payload["daily"]
        current = payload.get("current", {})
        code = int(daily["weather_code"][0])
        return WeatherCache(
            latitude=lat,
            longitude=lon,
            for_date=target,
            label=payload.get("timezone"),
            condition=_condition_from_code(code),
            temp_min_c=float(daily["temperature_2m_min"][0]),
            temp_max_c=float(daily["temperature_2m_max"][0]),
            temp_current_c=(
                float(current["temperature_2m"])
                if "temperature_2m" in current
                else None
            ),
            feels_like_c=(
                float(current["apparent_temperature"])
                if current.get("apparent_temperature") is not None
                else None
            ),
            humidity_pct=(
                float(current["relative_humidity_2m"])
                if current.get("relative_humidity_2m") is not None
                else None
            ),
            precipitation_prob=(
                float(daily["precipitation_probability_max"][0])
                if daily.get("precipitation_probability_max")
                and daily["precipitation_probability_max"][0] is not None
                else None
            ),
            wind_kph=(
                float(current["wind_speed_10m"])
                if "wind_speed_10m" in current
                else None
            ),
            uv_index=(
                float(daily["uv_index_max"][0])
                if daily.get("uv_index_max")
                and daily["uv_index_max"][0] is not None
                else None
            ),
            raw=payload,
        )
