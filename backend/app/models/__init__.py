"""ORM models package.

Importing every model here ensures they are all registered on ``Base.metadata``
whenever ``app.models`` is imported — which is what Alembic's autogenerate and
the app's metadata reflection rely on.
"""

from app.models.ai import AIMemory, Recommendation
from app.models.associations import item_colors, item_tags
from app.models.clothing import ClothingItem
from app.models.enums import (
    FavoriteTargetType,
    Formality,
    Occasion,
    RecommendationStatus,
    Season,
    WeatherCondition,
)
from app.models.favorite import Favorite
from app.models.outfit import Outfit, OutfitItem
from app.models.reference import Category, Color, Tag
from app.models.weather import WeatherCache
from app.models.wear import WearLog

__all__ = [
    "AIMemory",
    "Recommendation",
    "item_colors",
    "item_tags",
    "ClothingItem",
    "FavoriteTargetType",
    "Formality",
    "Occasion",
    "RecommendationStatus",
    "Season",
    "WeatherCondition",
    "Favorite",
    "Outfit",
    "OutfitItem",
    "Category",
    "Color",
    "Tag",
    "WeatherCache",
    "WearLog",
]
