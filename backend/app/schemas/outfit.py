"""Schemas for outfits."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Formality, Occasion
from app.schemas.clothing import ClothingItemRead
from app.schemas.common import ORMModel


class OutfitItemRead(ORMModel):
    id: int
    position: int
    item: ClothingItemRead


class OutfitBase(BaseModel):
    name: str = Field(max_length=120)
    description: str | None = None
    occasion: Occasion = Occasion.EVERYDAY
    formality: Formality = Formality.CASUAL


class OutfitCreate(OutfitBase):
    # Ordered list of item ids composing the outfit.
    item_ids: list[int] = Field(default_factory=list)
    is_ai_generated: bool = False


class OutfitUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = None
    occasion: Occasion | None = None
    formality: Formality | None = None
    item_ids: list[int] | None = None


class OutfitRead(ORMModel):
    id: int
    name: str
    description: str | None
    occasion: Occasion
    formality: Formality
    is_ai_generated: bool
    wear_count: int
    items: list[OutfitItemRead]
    created_at: datetime
    updated_at: datetime
