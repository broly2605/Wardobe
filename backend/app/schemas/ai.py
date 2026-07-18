"""Schemas for AI recommendations and memory."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Occasion, RecommendationStatus
from app.schemas.clothing import ClothingItemRead
from app.schemas.common import ORMModel
from app.schemas.weather import WeatherRead


class RecommendationRequest(BaseModel):
    """Parameters for requesting an outfit recommendation."""

    occasion: Occasion = Occasion.EVERYDAY
    # Optional coordinates so the recommender can factor in weather.
    latitude: float | None = None
    longitude: float | None = None
    # Optional free-text steer, e.g. "something bold" or "keep it minimal".
    prompt: str | None = Field(default=None, max_length=500)


class RecommendedOutfit(BaseModel):
    """A single suggested outfit returned by the recommender."""

    items: list[ClothingItemRead]
    rationale: str
    used_ai: bool
    occasion: Occasion
    weather: WeatherRead | None = None


class RecommendationRead(ORMModel):
    id: int
    occasion: Occasion
    status: RecommendationStatus
    used_ai: bool
    rationale: str | None
    payload: dict
    outfit_id: int | None
    created_at: datetime


class RecommendationFeedback(BaseModel):
    """User's response to a recommendation, used to learn preferences."""

    status: RecommendationStatus


class AIMemoryBase(BaseModel):
    key: str = Field(max_length=80)
    value: dict
    description: str | None = None
    weight: float = 1.0


class AIMemoryCreate(AIMemoryBase):
    pass


class AIMemoryRead(ORMModel, AIMemoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
