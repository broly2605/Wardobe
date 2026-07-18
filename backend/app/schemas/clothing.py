"""Schemas for clothing items."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import Formality, Season
from app.schemas.common import ORMModel
from app.schemas.reference import CategoryRead, ColorRead, TagRead


class ClothingItemBase(BaseModel):
    """Fields shared by create/update. Only ``name`` + ``category_id`` matter;
    everything else is optional to keep item entry friction-free."""

    name: str = Field(max_length=120)
    category_id: int
    brand: str | None = Field(default=None, max_length=80)
    size: str | None = Field(default=None, max_length=32)
    material: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    season: Season = Season.ALL_SEASON
    formality: Formality = Formality.CASUAL
    warmth: int = Field(default=5, ge=0, le=10)
    purchase_date: date | None = None


class ClothingItemCreate(ClothingItemBase):
    """Payload for creating an item. Colors/tags referenced by id."""

    color_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)


class ClothingItemUpdate(BaseModel):
    """Partial update — every field optional."""

    name: str | None = Field(default=None, max_length=120)
    category_id: int | None = None
    brand: str | None = Field(default=None, max_length=80)
    size: str | None = Field(default=None, max_length=32)
    material: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    season: Season | None = None
    formality: Formality | None = None
    warmth: int | None = Field(default=None, ge=0, le=10)
    purchase_date: date | None = None
    is_archived: bool | None = None
    color_ids: list[int] | None = None
    tag_ids: list[int] | None = None


class ClothingItemRead(ORMModel):
    id: int
    name: str
    category: CategoryRead
    brand: str | None
    size: str | None
    material: str | None
    notes: str | None
    image_path: str | None
    image_url: str | None = None  # populated by the service layer
    season: Season
    formality: Formality
    warmth: int
    is_archived: bool
    wear_count: int
    last_worn_at: date | None
    purchase_date: date | None
    ai_metadata: dict | None
    colors: list[ColorRead]
    tags: list[TagRead]
    created_at: datetime
    updated_at: datetime
