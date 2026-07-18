"""Orchestration for the AI wardrobe scanner.

Ties together image validation/storage, optional background removal, the CV/AI
:class:`WardrobeScanner`, and the reference data needed to turn a raw detection
into a fully-populated :class:`~app.models.clothing.ClothingItem` — with no
manual tagging required.

Detected attributes are stored on real columns where they exist (category,
colors, material, season, formality, brand, warmth) for first-class filtering
and analytics, and the richer signals (pattern, texture, sleeve length, fit,
occasion, confidence, source, background-removal flag, raw detection) go into
the existing ``ai_metadata`` JSONB column — so no schema migration is needed.
"""

from __future__ import annotations

from fastapi import UploadFile

from app.models.clothing import ClothingItem
from app.repositories.clothing import ClothingItemRepository
from app.repositories.reference import CategoryRepository, ColorRepository
from app.services.ai.color_theory import nearest_color_name
from app.services.ai.scanner import DetectedColor, ScanDetection, WardrobeScanner
from app.services.background import remove_background
from app.services.storage import ImageValidationError, storage_service


class ScanService:
    """Scans images and creates auto-tagged wardrobe items."""

    def __init__(
        self,
        items: ClothingItemRepository,
        colors: ColorRepository,
        categories: CategoryRepository,
        scanner: WardrobeScanner,
    ) -> None:
        self.items = items
        self.colors = colors
        self.categories = categories
        self.scanner = scanner

    async def scan_one(self, file: UploadFile) -> ClothingItem:
        """Validate, detect, and persist a single scanned item.

        Raises :class:`ImageValidationError` for an unusable upload; the caller
        maps that to a 400 (single) or a per-file error (batch).
        """
        raw = await storage_service.read_valid_image(file)

        # Remove the background when the shot looks busy; otherwise re-encode.
        processed, bg_removed = remove_background(raw)

        detection = await self.scanner.detect(processed)

        category_id = await self._resolve_category_id(detection.category)
        color_rows = await self._resolve_colors(detection.colors)

        relative_path = storage_service.save_processed_image(processed)

        item = ClothingItem(
            name=detection.suggested_name,
            category_id=category_id,
            brand=detection.brand,
            material=detection.material,
            season=detection.season,
            formality=detection.formality,
            warmth=detection.warmth,
            image_path=relative_path,
            colors=color_rows,
            ai_metadata=self._build_metadata(detection, bg_removed),
        )
        await self.items.add(item)
        # Re-fetch so category/colors are eagerly loaded for serialization
        # (avoids async lazy-load during Pydantic validation).
        created = await self.items.get(item.id)
        assert created is not None  # just inserted
        return created

    async def scan_many(
        self, files: list[UploadFile]
    ) -> list[tuple[str, ClothingItem | None, str | None]]:
        """Scan multiple images, isolating per-file failures.

        Returns a list of ``(filename, item_or_None, error_or_None)`` so one bad
        image never fails the whole batch.
        """
        results: list[tuple[str, ClothingItem | None, str | None]] = []
        for file in files:
            filename = file.filename or "image"
            try:
                item = await self.scan_one(file)
                results.append((filename, item, None))
            except ImageValidationError as exc:
                results.append((filename, None, str(exc)))
            except Exception as exc:  # noqa: BLE001 - isolate unexpected failures
                results.append((filename, None, f"Scan failed: {exc}"))
        return results

    # --- reference resolution --------------------------------------------
    async def _resolve_category_id(self, slug: str) -> int:
        """Map a detected category slug to a Category id (with fallbacks)."""
        category = await self.categories.get_by_slug(slug)
        if category is None:
            category = await self.categories.get_by_slug("tops")
        if category is None:
            # Wardrobe hasn't been seeded — use the first available category.
            ordered = await self.categories.list_ordered()
            if not ordered:
                raise ImageValidationError(
                    "No categories are configured. Seed reference data first."
                )
            category = ordered[0]
        return category.id

    async def _resolve_colors(self, detected: list[DetectedColor]):
        """Map detected RGB colors to the nearest seeded Color rows (deduped)."""
        if not detected:
            return []
        palette_rows = await self.colors.list_ordered()
        palette = [(c.name, c.hex) for c in palette_rows]
        by_name = {c.name: c for c in palette_rows}

        chosen = []
        seen: set[str] = set()
        for dc in detected:
            match = nearest_color_name(dc.rgb, palette)
            if match is None:
                continue
            name = match[0]
            if name in seen:
                continue
            seen.add(name)
            row = by_name.get(name)
            if row is not None:
                chosen.append(row)
        # Primary + secondary is enough; cap to avoid noise.
        return chosen[:2]

    # --- metadata ---------------------------------------------------------
    @staticmethod
    def _build_metadata(detection: ScanDetection, bg_removed: bool) -> dict:
        """Assemble the ``ai_metadata.scan`` payload from a detection."""
        return {
            "scan": {
                "pattern": detection.pattern,
                "texture": detection.texture,
                "sleeve_length": detection.sleeve_length,
                "fit": detection.fit,
                "occasion": detection.occasion.value,
                "material": detection.material,
                "season": detection.season.value,
                "formality": detection.formality.value,
                "brand": detection.brand,
                "confidence": detection.confidence,
                "source": detection.source,
                "background_removed": bg_removed,
                "detected_colors": [
                    {"hex": c.hex, "weight": round(c.weight, 3)}
                    for c in detection.colors
                ],
            }
        }
