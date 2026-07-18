"""Computer-vision wardrobe scanner.

Given a clothing photo, :class:`WardrobeScanner` detects every attribute the
scanner UI needs — category, primary/secondary color, pattern, material,
texture, season, sleeve length, fit, formality, occasion, and brand — with a
confidence score.

Two signal sources are combined:

* **Pixels (always on).** Dominant-color extraction via Pillow (see
  :mod:`app.services.ai.color_theory`) yields the primary/secondary colors
  deterministically, so color detection works with no AI key.
* **Vision model (when keyed).** The configured :class:`AIProvider` is asked for
  the semantic attributes as JSON. Its color hints are ignored in favor of the
  pixel-derived colors, which are more reliable.

When the model is unavailable the scanner still returns a complete, usable
detection built from the pixel colors plus safe heuristic defaults, tagged with
``source="cv_fallback"`` so callers/UX can show how it was produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.enums import (
    Fit,
    Formality,
    Occasion,
    Pattern,
    Season,
    SleeveLength,
    Texture,
)
from app.services.ai.color_theory import dominant_colors, rgb_to_hex
from app.services.ai.provider import AIProvider

# Category slugs the scanner maps into. Kept aligned with the seeded categories
# so detection results resolve to real rows; unknown values fall back to "tops".
KNOWN_CATEGORIES = [
    "tops",
    "bottoms",
    "dresses",
    "outerwear",
    "footwear",
    "accessories",
]

# Typical warmth (0-10) per category, used as a heuristic default.
_CATEGORY_WARMTH = {
    "tops": 4,
    "bottoms": 4,
    "dresses": 3,
    "outerwear": 8,
    "footwear": 3,
    "accessories": 1,
}


@dataclass
class DetectedColor:
    """A single detected color with its pixel share (0-1)."""

    rgb: tuple[int, int, int]
    hex: str
    weight: float


@dataclass
class ScanDetection:
    """Normalized result of scanning one clothing image."""

    suggested_name: str
    category: str
    colors: list[DetectedColor]
    pattern: str
    material: str | None
    texture: str
    season: Season
    sleeve_length: str
    fit: str
    formality: Formality
    occasion: Occasion
    brand: str | None
    warmth: int
    confidence: float
    source: str  # "ai_vision" | "cv_fallback"
    raw: dict[str, Any] = field(default_factory=dict)


def _coerce_enum(enum_cls, value: object, default):
    """Best-effort map a free-form string to an enum member, else ``default``."""
    if value is None:
        return default
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    for member in enum_cls:
        if member.value == text:
            return member
    return default


def _clamp_confidence(value: object) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.5
    if conf > 1.0:  # model may return a percentage
        conf = conf / 100.0
    return max(0.0, min(1.0, conf))


class WardrobeScanner:
    """Detects clothing attributes from an image."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def detect(self, image_bytes: bytes) -> ScanDetection:
        """Analyze ``image_bytes`` and return a complete attribute detection."""
        colors = self._detect_colors(image_bytes)

        vision: dict[str, Any] | None = None
        if self.provider.enabled:
            vision = await self.provider.describe_image(image_bytes, _VISION_PROMPT)

        if vision:
            return self._from_vision(vision, colors)
        return self._from_cv(colors)

    # --- color detection --------------------------------------------------
    def _detect_colors(self, image_bytes: bytes) -> list[DetectedColor]:
        dominants = dominant_colors(image_bytes, k=3)
        detected: list[DetectedColor] = []
        for rgb, weight in dominants:
            detected.append(DetectedColor(rgb=rgb, hex=rgb_to_hex(rgb), weight=weight))
        return detected

    # --- result builders --------------------------------------------------
    def _from_vision(
        self, vision: dict[str, Any], colors: list[DetectedColor]
    ) -> ScanDetection:
        category = str(vision.get("category", "")).strip().lower()
        if category not in KNOWN_CATEGORIES:
            category = "tops"

        season = _coerce_enum(Season, vision.get("season"), Season.ALL_SEASON)
        formality = _coerce_enum(Formality, vision.get("formality"), Formality.CASUAL)
        occasion = _coerce_enum(Occasion, vision.get("occasion"), Occasion.EVERYDAY)
        pattern = _coerce_enum(Pattern, vision.get("pattern"), Pattern.SOLID)
        texture = _coerce_enum(Texture, vision.get("texture"), Texture.SMOOTH)
        sleeve = _coerce_enum(
            SleeveLength, vision.get("sleeve_length"), SleeveLength.NOT_APPLICABLE
        )
        fit = _coerce_enum(Fit, vision.get("fit"), Fit.REGULAR)

        material = vision.get("material")
        material = str(material).strip()[:80] if material else None
        brand = vision.get("brand")
        brand = str(brand).strip()[:80] if brand and str(brand).strip().lower() not in (
            "none",
            "unknown",
            "n/a",
            "",
        ) else None

        name = vision.get("suggested_name") or self._fallback_name(category, colors)

        return ScanDetection(
            suggested_name=str(name).strip()[:120],
            category=category,
            colors=colors,
            pattern=pattern.value,
            material=material,
            texture=texture.value,
            season=season,
            sleeve_length=sleeve.value,
            fit=fit.value,
            formality=formality,
            occasion=occasion,
            brand=brand,
            warmth=_CATEGORY_WARMTH.get(category, 5),
            confidence=_clamp_confidence(vision.get("confidence", 0.8)),
            source="ai_vision",
            raw=vision,
        )

    def _from_cv(self, colors: list[DetectedColor]) -> ScanDetection:
        """Complete detection from pixels only (no vision model available)."""
        category = "tops"  # safe default; user can reassign later
        return ScanDetection(
            suggested_name=self._fallback_name(category, colors),
            category=category,
            colors=colors,
            pattern=Pattern.SOLID.value,
            material=None,
            texture=Texture.SMOOTH.value,
            season=Season.ALL_SEASON,
            sleeve_length=SleeveLength.NOT_APPLICABLE.value,
            fit=Fit.REGULAR.value,
            formality=Formality.CASUAL,
            occasion=Occasion.EVERYDAY,
            brand=None,
            warmth=_CATEGORY_WARMTH.get(category, 5),
            # Colors are reliable; semantic fields are guesses, so keep it modest.
            confidence=0.4 if colors else 0.2,
            source="cv_fallback",
            raw={},
        )

    @staticmethod
    def _fallback_name(category: str, colors: list[DetectedColor]) -> str:
        """A readable default name like "Navy Tops" when the model gives none."""
        label = category.rstrip("s").capitalize() if category else "Item"
        return f"Scanned {label}"


_VISION_PROMPT = (
    "You are a fashion cataloguing assistant. Identify the single main clothing "
    "item in this image and respond ONLY as JSON with these keys:\n"
    '- "suggested_name": short human name (e.g. "Navy Wool Overcoat")\n'
    '- "category": one of tops, bottoms, dresses, outerwear, footwear, accessories\n'
    '- "pattern": one of solid, striped, checked, plaid, floral, polka_dot, '
    "graphic, animal, camouflage, geometric, abstract, printed, other\n"
    '- "material": primary fabric (e.g. cotton, denim, wool, leather) or null\n'
    '- "texture": one of smooth, ribbed, knit, fleece, denim, leather, suede, '
    "corduroy, satin, lace, quilted, textured, other\n"
    '- "season": one of spring, summer, autumn, winter, all_season\n'
    '- "sleeve_length": one of sleeveless, short, three_quarter, long, '
    "not_applicable\n"
    '- "fit": one of slim, regular, relaxed, oversized, tailored, loose, other\n'
    '- "formality": one of lounge, casual, smart_casual, business, formal\n'
    '- "occasion": one of everyday, work, workout, date, party, formal_event, '
    "travel, outdoor\n"
    '- "brand": visible brand name, or null if none is visible\n'
    '- "confidence": your overall confidence from 0 to 1\n'
    "Base every field on what is visually apparent. Use null only where allowed."
)
