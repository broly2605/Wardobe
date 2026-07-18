"""Rule-based outfit recommender (fully offline).

This engine builds a sensible outfit from the wardrobe using deterministic
heuristics — occasion/formality fit, weather-appropriate warmth, color harmony,
and a freshness bias toward under-worn items. It is both the offline default and
the fallback whenever an AI call fails, guaranteeing the app always responds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.clothing import ClothingItem
from app.models.enums import Formality, Occasion, WeatherCondition
from app.models.weather import WeatherCache
from app.services.ai.color_theory import is_neutral, palette_cohesion

# Ordered formality scale for computing "distance" between an item and target.
_FORMALITY_ORDER = {
    Formality.LOUNGE: 0,
    Formality.CASUAL: 1,
    Formality.SMART_CASUAL: 2,
    Formality.BUSINESS: 3,
    Formality.FORMAL: 4,
}

# Default target formality per occasion.
_OCCASION_FORMALITY = {
    Occasion.EVERYDAY: Formality.CASUAL,
    Occasion.WORK: Formality.BUSINESS,
    Occasion.WORKOUT: Formality.LOUNGE,
    Occasion.DATE: Formality.SMART_CASUAL,
    Occasion.PARTY: Formality.SMART_CASUAL,
    Occasion.FORMAL_EVENT: Formality.FORMAL,
    Occasion.TRAVEL: Formality.CASUAL,
    Occasion.OUTDOOR: Formality.CASUAL,
}

# Category slugs grouped into the "slots" an outfit fills. The engine picks at
# most one item per slot (outerwear only when it's cold).
_SLOTS: dict[str, set[str]] = {
    "top": {"tops", "shirts", "t-shirts", "sweaters", "knitwear"},
    "bottom": {"bottoms", "trousers", "jeans", "shorts", "skirts"},
    "one_piece": {"dresses", "jumpsuits"},
    "footwear": {"footwear", "shoes", "sneakers", "boots"},
    "outerwear": {"outerwear", "jackets", "coats"},
    "accessory": {"accessories", "bags", "hats", "scarves"},
}


@dataclass
class ScoredItem:
    """An item paired with its computed suitability score."""

    item: ClothingItem
    score: float
    reasons: list[str] = field(default_factory=list)


def _effective_temp(weather: WeatherCache) -> float:
    """Best available "how it feels" temperature: feels-like > current > mean."""
    if weather.feels_like_c is not None:
        return weather.feels_like_c
    if weather.temp_current_c is not None:
        return weather.temp_current_c
    return (weather.temp_min_c + weather.temp_max_c) / 2


def _target_warmth(weather: WeatherCache | None) -> int:
    """Desired garment warmth (0-10) for the given weather."""
    if weather is None:
        return 5
    temp = _effective_temp(weather)
    # Warmer weather -> lower desired warmth. Tuned around typical comfort.
    if temp >= 28:
        return 1
    if temp >= 22:
        return 3
    if temp >= 15:
        return 5
    if temp >= 8:
        return 7
    if temp >= 0:
        return 9
    return 10


def _slot_for(item: ClothingItem) -> str | None:
    """Return the outfit slot an item belongs to, or ``None`` if unmapped."""
    slug = item.category.slug.lower() if item.category else ""
    for slot, slugs in _SLOTS.items():
        if slug in slugs:
            return slot
    return None


def _item_hexes(item: ClothingItem) -> list[str]:
    return [c.hex for c in item.colors] if item.colors else []


# Materials/textures that breathe well and suit hot weather.
_BREATHABLE_KEYWORDS = {
    "linen",
    "cotton",
    "chambray",
    "seersucker",
    "mesh",
    "bamboo",
    "rayon",
    "viscose",
    "modal",
    "silk",
    "poplin",
}
# Materials/textures that trap heat — penalized when it's hot.
_INSULATING_KEYWORDS = {
    "wool",
    "fleece",
    "cashmere",
    "down",
    "shearling",
    "flannel",
    "corduroy",
    "quilted",
    "knit",
}
# Materials/textures that fare badly in the rain.
_RAIN_SENSITIVE_KEYWORDS = {"suede", "canvas", "leather"}

# Wind speed (km/h) beyond which we treat conditions as breezy enough to layer.
_WINDY_KPH = 25.0
# Effective-temperature thresholds for fabric guidance.
_HOT_TEMP_C = 24.0
_COLD_TEMP_C = 10.0


def _fabric_text(item: ClothingItem) -> str:
    """Lowercased material + detected texture, for keyword matching."""
    parts: list[str] = []
    if item.material:
        parts.append(item.material.lower())
    scan = (item.ai_metadata or {}).get("scan") if item.ai_metadata else None
    if isinstance(scan, dict):
        texture = scan.get("texture")
        if isinstance(texture, str):
            parts.append(texture.lower())
    return " ".join(parts)


def _is_breathable(item: ClothingItem) -> bool:
    text = _fabric_text(item)
    return any(kw in text for kw in _BREATHABLE_KEYWORDS)


def _is_insulating(item: ClothingItem) -> bool:
    text = _fabric_text(item)
    return any(kw in text for kw in _INSULATING_KEYWORDS)


def _is_rain_sensitive(item: ClothingItem) -> bool:
    text = _fabric_text(item)
    return any(kw in text for kw in _RAIN_SENSITIVE_KEYWORDS)


def _is_umbrella(item: ClothingItem) -> bool:
    return "umbrella" in item.name.lower()


def _is_wet(weather: WeatherCache | None) -> bool:
    return weather is not None and weather.condition in {
        WeatherCondition.RAIN,
        WeatherCondition.SNOW,
        WeatherCondition.STORM,
    }


def _is_windy(weather: WeatherCache | None) -> bool:
    return (
        weather is not None
        and weather.wind_kph is not None
        and weather.wind_kph >= _WINDY_KPH
    )


class RuleBasedStylist:
    """Deterministic wardrobe recommender."""

    def recommend(
        self,
        items: list[ClothingItem],
        *,
        occasion: Occasion,
        weather: WeatherCache | None,
        disliked_item_ids: set[int] | None = None,
    ) -> tuple[list[ClothingItem], str]:
        """Return (chosen items, human-readable rationale)."""
        disliked = disliked_item_ids or set()
        target_formality = _OCCASION_FORMALITY.get(occasion, Formality.CASUAL)
        target_warmth = _target_warmth(weather)

        # Bucket candidate items by slot with a per-item score.
        buckets: dict[str, list[ScoredItem]] = {slot: [] for slot in _SLOTS}
        for item in items:
            if item.id in disliked:
                continue
            slot = _slot_for(item)
            if slot is None:
                continue
            scored = ScoredItem(
                item=item,
                score=self._score_item(
                    item, target_formality, target_warmth, weather
                ),
            )
            buckets[slot].append(scored)

        for scored in buckets.values():
            scored.sort(key=lambda s: s.score, reverse=True)

        chosen = self._assemble(buckets, weather, target_warmth)
        rationale = self._explain(
            chosen, occasion, weather, target_formality, target_warmth
        )
        return chosen, rationale

    def _score_item(
        self,
        item: ClothingItem,
        target_formality: Formality,
        target_warmth: int,
        weather: WeatherCache | None,
    ) -> float:
        """Score a single item's fit for the target context (higher better)."""
        # Formality closeness (0 distance -> 1.0).
        f_dist = abs(
            _FORMALITY_ORDER[item.formality] - _FORMALITY_ORDER[target_formality]
        )
        formality_score = max(0.0, 1.0 - f_dist * 0.25)

        # Warmth closeness.
        w_dist = abs(item.warmth - target_warmth)
        warmth_score = max(0.0, 1.0 - w_dist * 0.12)

        # Freshness: favor under-worn items to keep suggestions varied.
        freshness = 1.0 / (1.0 + item.wear_count)

        base = formality_score * 0.5 + warmth_score * 0.35 + freshness * 0.15
        return base + self._weather_fabric_bias(item, weather)

    @staticmethod
    def _weather_fabric_bias(
        item: ClothingItem, weather: WeatherCache | None
    ) -> float:
        """Fabric-level nudge based on live weather (breathable/insulating/rain).

        Returns a small +/- adjustment layered on the base score so weather
        shapes *which* items win their slot, not just whether a layer is added.
        """
        if weather is None:
            return 0.0

        bias = 0.0
        temp = _effective_temp(weather)

        if temp >= _HOT_TEMP_C:
            # Hot: reward breathable fabrics, penalize heat-trapping ones.
            if _is_breathable(item):
                bias += 0.15
            if _is_insulating(item):
                bias -= 0.20
        elif temp <= _COLD_TEMP_C:
            # Cold: insulating fabrics help; airy fabrics are a liability.
            if _is_insulating(item):
                bias += 0.12
            if _is_breathable(item):
                bias -= 0.08

        # Rain/snow: steer away from water-sensitive materials (e.g. suede).
        if _is_wet(weather) and _is_rain_sensitive(item):
            bias -= 0.30

        return bias

    def _assemble(
        self,
        buckets: dict[str, list[ScoredItem]],
        weather: WeatherCache | None,
        target_warmth: int,
    ) -> list[ClothingItem]:
        """Pick items across slots, aiming for color cohesion."""
        chosen: list[ClothingItem] = []

        # Prefer a one-piece if it clearly outscores the best top+bottom combo.
        one_piece = buckets["one_piece"][0] if buckets["one_piece"] else None
        top = buckets["top"][0] if buckets["top"] else None
        bottom = buckets["bottom"][0] if buckets["bottom"] else None

        if one_piece and (
            not (top and bottom)
            or one_piece.score >= (top.score + bottom.score) / 2 + 0.05
        ):
            chosen.append(one_piece.item)
        else:
            if top:
                chosen.append(top.item)
            if bottom:
                chosen.append(bottom.item)

        # Footwear whenever available. When it's wet, avoid rain-sensitive
        # pairs (e.g. suede) if a safer option exists.
        if buckets["footwear"]:
            footwear_pool = buckets["footwear"]
            if _is_wet(weather):
                safe = [s for s in footwear_pool if not _is_rain_sensitive(s.item)]
                if safe:
                    footwear_pool = safe
            chosen.append(self._pick_cohesive(footwear_pool, chosen))

        # Outerwear when it's cold, wet, or windy — layering / wind protection.
        needs_layer = (
            target_warmth >= 7 or _is_wet(weather) or _is_windy(weather)
        )
        if needs_layer and buckets["outerwear"]:
            chosen.append(self._pick_cohesive(buckets["outerwear"], chosen))

        # Bring an umbrella when rain is likely and one exists in the wardrobe.
        if _is_wet(weather) and buckets["accessory"]:
            umbrella = next(
                (s.item for s in buckets["accessory"] if _is_umbrella(s.item)),
                None,
            )
            if umbrella is not None and umbrella not in chosen:
                chosen.append(umbrella)

        # One accessory for a finishing touch (skip if we already added one).
        # Umbrellas are functional rain gear, not a styling accessory, so they
        # only appear via the rain branch above.
        has_accessory = any(_slot_for(it) == "accessory" for it in chosen)
        style_accessories = [
            s for s in buckets["accessory"] if not _is_umbrella(s.item)
        ]
        if style_accessories and not has_accessory:
            chosen.append(self._pick_cohesive(style_accessories, chosen))

        return chosen

    def _pick_cohesive(
        self, candidates: list[ScoredItem], current: list[ClothingItem]
    ) -> ClothingItem:
        """From the top candidates, choose the one best matching current colors.

        Considers only the strongest few by base score, then re-ranks them by
        how well they harmonize with the colors already chosen. Neutrals get a
        small boost since they pair with anything.
        """
        pool = candidates[:5]
        current_hexes = [h for it in current for h in _item_hexes(it)]
        if not current_hexes:
            return pool[0].item

        best = pool[0]
        best_value = -1.0
        for cand in pool:
            cand_hexes = _item_hexes(cand.item)
            cohesion = palette_cohesion(current_hexes + cand_hexes)
            neutral_boost = 0.1 if any(
                is_neutral(c.family) for c in cand.item.colors
            ) else 0.0
            value = cand.score * 0.6 + cohesion * 0.4 + neutral_boost
            if value > best_value:
                best_value, best = value, cand
        return best.item

    def _explain(
        self,
        chosen: list[ClothingItem],
        occasion: Occasion,
        weather: WeatherCache | None,
        target_formality: Formality,
        target_warmth: int,
    ) -> str:
        """Compose a friendly rationale for the chosen outfit."""
        if not chosen:
            return (
                "Your wardrobe doesn't have enough items yet to build a full "
                "outfit. Add a few tops, bottoms, and shoes to get tailored "
                "suggestions."
            )
        parts = [
            f"Styled for a {occasion.value.replace('_', ' ')} occasion at a "
            f"{target_formality.value.replace('_', ' ')} level."
        ]
        if weather is not None:
            temp = _effective_temp(weather)
            parts.append(
                f"It feels like {temp:.0f}°C and {weather.condition.value}, so I "
                f"leaned toward {'lighter' if target_warmth <= 4 else 'warmer'} "
                "pieces."
            )
            # Call out the specific weather adaptations we made.
            if temp >= _HOT_TEMP_C and any(_is_breathable(it) for it in chosen):
                parts.append("I favored breathable fabrics to keep you cool.")
            if temp <= _COLD_TEMP_C:
                parts.append("Added a layer to keep you warm.")
            if _is_wet(weather):
                notes = ["kept water-sensitive materials like suede out of the mix"]
                if any(_is_umbrella(it) for it in chosen):
                    notes.append("packed an umbrella")
                elif any(_slot_for(it) == "outerwear" for it in chosen):
                    notes.append("added a jacket for the rain")
                parts.append(f"Since rain is likely, I {' and '.join(notes)}.")
            elif _is_windy(weather) and any(
                _slot_for(it) == "outerwear" for it in chosen
            ):
                parts.append("It's breezy, so I added outerwear to cut the wind.")
            if weather.uv_index is not None and weather.uv_index >= 6:
                parts.append(
                    f"UV is high (index {weather.uv_index:.0f}) — sunglasses or a "
                    "hat wouldn't hurt."
                )
        hexes = [h for it in chosen for h in _item_hexes(it)]
        if len(hexes) >= 2 and palette_cohesion(hexes) >= 0.7:
            parts.append("The palette stays cohesive and easy to wear together.")
        parts.append("I also favored pieces you haven't worn as often lately.")
        return " ".join(parts)


rule_based_stylist = RuleBasedStylist()
