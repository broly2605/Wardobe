"""Stylist service — orchestrates AI, the rule engine, and learned memory.

This is the single entry point the API uses for recommendations and image
auto-tagging. It tries the configured AI provider first (when enabled) and
always falls back to the deterministic rule engine, so a recommendation is
guaranteed regardless of network or key state.
"""

from __future__ import annotations

from typing import Any

from app.models.clothing import ClothingItem
from app.models.enums import Occasion
from app.models.weather import WeatherCache
from app.services.ai.provider import AIProvider
from app.services.ai.rule_engine import RuleBasedStylist


def _item_summary(item: ClothingItem) -> dict[str, Any]:
    """Compact, prompt-friendly representation of a wardrobe item."""
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category.slug if item.category else None,
        "colors": [c.name for c in item.colors],
        "formality": item.formality.value,
        "season": item.season.value,
        "warmth": item.warmth,
        "wear_count": item.wear_count,
    }


class StylistService:
    """Produces outfit recommendations and image tags."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.rule_engine = RuleBasedStylist()

    async def recommend_outfit(
        self,
        items: list[ClothingItem],
        *,
        occasion: Occasion,
        weather: WeatherCache | None,
        memory: dict[str, Any] | None = None,
        user_prompt: str | None = None,
    ) -> tuple[list[ClothingItem], str, bool]:
        """Return (items, rationale, used_ai).

        When AI is enabled, the provider selects item ids from the supplied
        wardrobe; we resolve those back to ORM objects. If AI is disabled or its
        output is unusable, the rule engine takes over.
        """
        if self.provider.enabled and items:
            ai_result = await self._recommend_with_ai(
                items, occasion, weather, memory, user_prompt
            )
            if ai_result is not None:
                return ai_result[0], ai_result[1], True

        chosen, rationale = self.rule_engine.recommend(
            items, occasion=occasion, weather=weather
        )
        return chosen, rationale, False

    async def _recommend_with_ai(
        self,
        items: list[ClothingItem],
        occasion: Occasion,
        weather: WeatherCache | None,
        memory: dict[str, Any] | None,
        user_prompt: str | None,
    ) -> tuple[list[ClothingItem], str] | None:
        by_id = {item.id: item for item in items}
        wardrobe = [_item_summary(i) for i in items]

        weather_ctx = "no weather data"
        if weather is not None:
            weather_ctx = (
                f"{weather.condition.value}, "
                f"{weather.temp_min_c:.0f}-{weather.temp_max_c:.0f}°C"
            )

        system_prompt = (
            "You are an expert personal stylist. Given a wardrobe (as JSON), an "
            "occasion, weather, and learned preferences, select a cohesive outfit "
            "using ONLY the provided item ids. Respond as JSON with keys "
            '"item_ids" (array of integers from the wardrobe) and "rationale" '
            "(a short, warm explanation). Favor color harmony, weather-"
            "appropriateness, and variety."
        )
        user_prompt_full = (
            f"Occasion: {occasion.value}\n"
            f"Weather: {weather_ctx}\n"
            f"Learned preferences: {memory or {}}\n"
            f"Extra request: {user_prompt or 'none'}\n"
            f"Wardrobe: {wardrobe}"
        )

        result = await self.provider.complete_json(system_prompt, user_prompt_full)
        if not result:
            return None

        raw_ids = result.get("item_ids")
        if not isinstance(raw_ids, list):
            return None

        chosen = [by_id[i] for i in raw_ids if isinstance(i, int) and i in by_id]
        if not chosen:
            return None

        rationale = result.get("rationale") or "A stylist-curated look for you."
        return chosen, str(rationale)

    async def tag_image(self, image_bytes: bytes) -> dict[str, Any] | None:
        """Auto-tag a clothing photo via vision, or ``None`` when unavailable."""
        if not self.provider.enabled:
            return None
        prompt = (
            "Identify this clothing item. Respond as JSON with keys: "
            '"suggested_name" (string), "category" (one of: tops, bottoms, '
            'dresses, footwear, outerwear, accessories), "colors" (array of '
            'common color names), "formality" (lounge|casual|smart_casual|'
            'business|formal), and "description" (one sentence).'
        )
        return await self.provider.describe_image(image_bytes, prompt)
