"""Business logic for outfits and wear logging."""

from __future__ import annotations

from datetime import date

from app.models.outfit import Outfit, OutfitItem
from app.models.wear import WearLog
from app.repositories.clothing import ClothingItemRepository
from app.repositories.outfit import OutfitRepository
from app.repositories.wear import WearLogRepository
from app.schemas.outfit import OutfitCreate, OutfitUpdate
from app.schemas.wear import WearLogCreate


class OutfitNotFoundError(LookupError):
    """Raised when an outfit id does not resolve."""


class OutfitService:
    def __init__(
        self,
        outfits: OutfitRepository,
        items: ClothingItemRepository,
        wear: WearLogRepository,
    ) -> None:
        self.outfits = outfits
        self.items = items
        self.wear = wear

    async def get(self, outfit_id: int) -> Outfit:
        outfit = await self.outfits.get(outfit_id)
        if outfit is None:
            raise OutfitNotFoundError(f"Outfit {outfit_id} not found.")
        return outfit

    async def list(
        self, *, limit: int = 100, offset: int = 0
    ) -> tuple[list[Outfit], int]:
        return await self.outfits.list_paginated(limit=limit, offset=offset)

    async def create(self, data: OutfitCreate) -> Outfit:
        outfit = Outfit(
            name=data.name,
            description=data.description,
            occasion=data.occasion,
            formality=data.formality,
            is_ai_generated=data.is_ai_generated,
        )
        outfit.items = self._build_members(data.item_ids)
        await self.outfits.add(outfit)
        # Re-fetch so the items -> item -> category chain is eagerly loaded.
        return await self.get(outfit.id)

    async def update(self, outfit_id: int, data: OutfitUpdate) -> Outfit:
        outfit = await self.get(outfit_id)
        payload = data.model_dump(exclude_unset=True)
        item_ids = payload.pop("item_ids", None)
        for field, value in payload.items():
            setattr(outfit, field, value)
        if item_ids is not None:
            # Replace membership wholesale; cascade removes orphaned rows.
            outfit.items = self._build_members(item_ids)
        await self.outfits.session.flush()
        # Re-fetch so replaced membership is reloaded with items eagerly loaded.
        return await self.get(outfit_id)

    @staticmethod
    def _build_members(item_ids: list[int]) -> list[OutfitItem]:
        """Create ordered OutfitItem rows preserving the given id order."""
        return [
            OutfitItem(item_id=item_id, position=index)
            for index, item_id in enumerate(item_ids)
        ]

    async def delete(self, outfit_id: int) -> None:
        outfit = await self.get(outfit_id)
        await self.outfits.delete(outfit)

    async def log_wear(self, data: WearLogCreate) -> WearLog:
        """Record a wear event and update denormalized wear counters."""
        log = WearLog(
            worn_on=data.worn_on,
            outfit_id=data.outfit_id,
            item_id=data.item_id,
            notes=data.notes,
        )
        await self.wear.add(log)

        # Update the outfit's counter and each of its items' counters.
        if data.outfit_id is not None:
            outfit = await self.outfits.get(data.outfit_id)
            if outfit is not None:
                outfit.wear_count += 1
                for member in outfit.items:
                    self._bump_item(member.item, data.worn_on)

        # A standalone item wear.
        if data.item_id is not None:
            item = await self.items.get(data.item_id)
            if item is not None:
                self._bump_item(item, data.worn_on)

        await self.wear.session.flush()
        return log

    @staticmethod
    def _bump_item(item, worn_on: date) -> None:
        item.wear_count += 1
        if item.last_worn_at is None or worn_on > item.last_worn_at:
            item.last_worn_at = worn_on
