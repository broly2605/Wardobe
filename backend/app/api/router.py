"""Top-level API router aggregating every feature router under ``/api``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    analytics,
    favorites,
    items,
    outfits,
    recommendations,
    reference,
    scan,
    settings,
    weather,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(reference.router)
api_router.include_router(items.router)
api_router.include_router(scan.router)
api_router.include_router(outfits.router)
api_router.include_router(recommendations.router)
api_router.include_router(analytics.router)
api_router.include_router(weather.router)
api_router.include_router(favorites.router)
api_router.include_router(settings.router)
