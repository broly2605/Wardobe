"""Schemas for the AI wardrobe scanner endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.clothing import ClothingItemRead


class ScannedItemResult(BaseModel):
    """Outcome of scanning a single uploaded image.

    ``ok`` reports whether an item was created. On failure (e.g. an invalid
    image) ``item`` is ``None`` and ``error`` explains why — this lets a batch
    surface per-file problems without failing the whole request.
    """

    filename: str
    ok: bool
    item: ClothingItemRead | None = None
    error: str | None = None


class BatchScanResponse(BaseModel):
    """Aggregate result of a multi-image scan."""

    scanned: int
    created: int
    results: list[ScannedItemResult]


class ScanStatus(BaseModel):
    """Capability probe for the scanner (used by the frontend)."""

    ai_enabled: bool
    background_removal_available: bool
    detected_attributes: list[str]
