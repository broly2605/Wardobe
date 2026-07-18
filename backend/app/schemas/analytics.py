"""Schemas for analytics responses."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.clothing import ClothingItemRead


class CountByLabel(BaseModel):
    """A generic label/count pair used by breakdown charts."""

    label: str
    count: int


class ColorSlice(BaseModel):
    """A color distribution slice, including the hex for chart rendering."""

    label: str
    hex: str
    count: int


class WardrobeStats(BaseModel):
    """Headline wardrobe metrics for the dashboard."""

    total_items: int
    total_outfits: int
    total_wears: int
    archived_items: int
    utilization_rate: float  # fraction of items worn at least once (0..1)
    never_worn_count: int


class AnalyticsOverview(BaseModel):
    """Aggregated analytics payload for the analytics page."""

    stats: WardrobeStats
    category_breakdown: list[CountByLabel]
    color_breakdown: list[ColorSlice]
    formality_breakdown: list[CountByLabel]
    most_worn: list[ClothingItemRead]
    least_worn: list[ClothingItemRead]
