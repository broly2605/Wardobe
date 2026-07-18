"""FastAPI dependency providers.

Each request gets a fresh session (via :func:`get_db`) and freshly-constructed
repositories/services bound to it. Assembling the graph here keeps route
handlers thin and makes every dependency explicit and testable.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.ai import AIMemoryRepository, RecommendationRepository
from app.repositories.clothing import ClothingItemRepository
from app.repositories.favorite import FavoriteRepository
from app.repositories.outfit import OutfitRepository
from app.repositories.reference import (
    CategoryRepository,
    ColorRepository,
    TagRepository,
)
from app.repositories.wear import WearLogRepository
from app.repositories.weather import WeatherRepository
from app.services.ai.provider import get_ai_provider
from app.services.ai.scanner import WardrobeScanner
from app.services.ai.stylist import StylistService
from app.services.analytics_service import AnalyticsService
from app.services.item_service import ItemService
from app.services.outfit_service import OutfitService
from app.services.recommendation_service import RecommendationService
from app.services.scan_service import ScanService
from app.services.weather import WeatherService

DBSession = Annotated[AsyncSession, Depends(get_db)]


# --- Service providers ---------------------------------------------------
def get_item_service(session: DBSession) -> ItemService:
    return ItemService(
        ClothingItemRepository(session),
        ColorRepository(session),
        TagRepository(session),
    )


def get_outfit_service(session: DBSession) -> OutfitService:
    return OutfitService(
        OutfitRepository(session),
        ClothingItemRepository(session),
        WearLogRepository(session),
    )


def get_analytics_service(session: DBSession) -> AnalyticsService:
    return AnalyticsService(session)


def get_weather_service(session: DBSession) -> WeatherService:
    return WeatherService(WeatherRepository(session))


def get_stylist_service() -> StylistService:
    # The AI provider is chosen from config (OpenAI when keyed, else offline).
    return StylistService(get_ai_provider())


def get_scan_service(session: DBSession) -> ScanService:
    # Vision when keyed; the scanner degrades to pixel-based CV otherwise.
    return ScanService(
        ClothingItemRepository(session),
        ColorRepository(session),
        CategoryRepository(session),
        WardrobeScanner(get_ai_provider()),
    )


def get_recommendation_service(session: DBSession) -> RecommendationService:
    return RecommendationService(
        items=ClothingItemRepository(session),
        recs=RecommendationRepository(session),
        memory=AIMemoryRepository(session),
        stylist=StylistService(get_ai_provider()),
        weather=WeatherService(WeatherRepository(session)),
    )


def get_favorite_repo(session: DBSession) -> FavoriteRepository:
    return FavoriteRepository(session)


def get_category_repo(session: DBSession) -> CategoryRepository:
    return CategoryRepository(session)


def get_color_repo(session: DBSession) -> ColorRepository:
    return ColorRepository(session)


def get_tag_repo(session: DBSession) -> TagRepository:
    return TagRepository(session)


def get_memory_repo(session: DBSession) -> AIMemoryRepository:
    return AIMemoryRepository(session)


# --- Annotated aliases for clean route signatures ---
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
OutfitServiceDep = Annotated[OutfitService, Depends(get_outfit_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
WeatherServiceDep = Annotated[WeatherService, Depends(get_weather_service)]
StylistServiceDep = Annotated[StylistService, Depends(get_stylist_service)]
ScanServiceDep = Annotated[ScanService, Depends(get_scan_service)]
RecommendationServiceDep = Annotated[
    RecommendationService, Depends(get_recommendation_service)
]
FavoriteRepoDep = Annotated[FavoriteRepository, Depends(get_favorite_repo)]
CategoryRepoDep = Annotated[CategoryRepository, Depends(get_category_repo)]
ColorRepoDep = Annotated[ColorRepository, Depends(get_color_repo)]
TagRepoDep = Annotated[TagRepository, Depends(get_tag_repo)]
MemoryRepoDep = Annotated[AIMemoryRepository, Depends(get_memory_repo)]
