"""Recommendation service — ties together wardrobe, weather, memory, and the
stylist, and persists suggestions + feedback for the learning loop.
"""

from __future__ import annotations

from typing import Any

from app.models.ai import Recommendation
from app.models.enums import RecommendationStatus
from app.repositories.ai import AIMemoryRepository, RecommendationRepository
from app.repositories.clothing import ClothingItemRepository
from app.schemas.ai import RecommendationRequest, RecommendedOutfit
from app.schemas.clothing import ClothingItemRead
from app.services.ai.stylist import StylistService
from app.services.weather import WeatherService


class RecommendationNotFoundError(LookupError):
    """Raised when a recommendation id does not resolve."""


class RecommendationService:
    def __init__(
        self,
        *,
        items: ClothingItemRepository,
        recs: RecommendationRepository,
        memory: AIMemoryRepository,
        stylist: StylistService,
        weather: WeatherService,
    ) -> None:
        self.items = items
        self.recs = recs
        self.memory = memory
        self.stylist = stylist
        self.weather = weather

    async def _load_memory(self) -> dict[str, Any]:
        """Collapse stored AI memory rows into a single prompt-ready dict."""
        rows = await self.memory.list_all()
        return {row.key: row.value for row in rows}

    async def generate(
        self, req: RecommendationRequest, *, enrich_url
    ) -> tuple[RecommendedOutfit, Recommendation]:
        """Generate, persist, and return an outfit recommendation.

        ``enrich_url`` maps an item's stored path to a public URL; it is injected
        so this service stays free of web-layer concerns.
        """
        items = await self.items.active_items()

        weather_record = None
        if req.latitude is not None and req.longitude is not None:
            weather_record = await self.weather.get_weather(
                req.latitude, req.longitude
            )

        memory = await self._load_memory()
        chosen, rationale, used_ai = await self.stylist.recommend_outfit(
            items,
            occasion=req.occasion,
            weather=weather_record,
            memory=memory,
            user_prompt=req.prompt,
        )

        # Persist the suggestion for the feedback/learning loop.
        record = Recommendation(
            occasion=req.occasion,
            status=RecommendationStatus.SUGGESTED,
            used_ai=used_ai,
            rationale=rationale,
            payload={"item_ids": [i.id for i in chosen]},
            weather_id=weather_record.id if weather_record else None,
        )
        await self.recs.add(record)

        item_reads = []
        for item in chosen:
            read = ClothingItemRead.model_validate(item)
            read.image_url = enrich_url(item.image_path)
            item_reads.append(read)

        outfit = RecommendedOutfit(
            items=item_reads,
            rationale=rationale,
            used_ai=used_ai,
            occasion=req.occasion,
            weather=weather_record,  # pydantic converts via from_attributes
        )
        return outfit, record

    async def record_feedback(
        self, rec_id: int, status: RecommendationStatus
    ) -> Recommendation:
        """Update a recommendation's status (accepted/dismissed/worn)."""
        record = await self.recs.get(rec_id)
        if record is None:
            raise RecommendationNotFoundError(f"Recommendation {rec_id} not found.")
        record.status = status
        await self.recs.session.flush()
        return record
