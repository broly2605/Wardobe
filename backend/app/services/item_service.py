"""Business logic for clothing items.

Coordinates the item repository, reference repositories (colors/tags), and image
storage. Routes call this service and never touch repositories directly.
"""

from __future__ import annotations

from app.models.clothing import ClothingItem
from app.models.enums import Formality, Season
from app.repositories.clothing import ClothingItemRepository
from app.repositories.reference import ColorRepository, TagRepository
from app.schemas.clothing import ClothingItemCreate, ClothingItemUpdate
from app.services.storage import storage_service


class ItemNotFoundError(LookupError):
    """Raised when an item id does not resolve."""


class ItemService:
    def __init__(
        self,
        items: ClothingItemRepository,
        colors: ColorRepository,
        tags: TagRepository,
    ) -> None:
        self.items = items
        self.colors = colors
        self.tags = tags

    async def get(self, item_id: int) -> ClothingItem:
        item = await self.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Clothing item {item_id} not found.")
        return item

    async def list(
        self,
        *,
        category_id: int | None = None,
        season: Season | None = None,
        formality: Formality | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ClothingItem], int]:
        return await self.items.list_filtered(
            category_id=category_id,
            season=season,
            formality=formality,
            search=search,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )

    async def create(self, data: ClothingItemCreate) -> ClothingItem:
        item = ClothingItem(
            name=data.name,
            category_id=data.category_id,
            brand=data.brand,
            size=data.size,
            material=data.material,
            notes=data.notes,
            season=data.season,
            formality=data.formality,
            warmth=data.warmth,
            purchase_date=data.purchase_date,
        )
        item.colors = await self.colors.get_many(data.color_ids)
        item.tags = await self.tags.get_many(data.tag_ids)
        await self.items.add(item)
        # Re-fetch so category/colors/tags are eagerly loaded for serialization.
        return await self.get(item.id)

    async def update(self, item_id: int, data: ClothingItemUpdate) -> ClothingItem:
        item = await self.get(item_id)
        payload = data.model_dump(exclude_unset=True)

        # Relationship fields are handled separately from scalar columns.
        color_ids = payload.pop("color_ids", None)
        tag_ids = payload.pop("tag_ids", None)
        for field, value in payload.items():
            setattr(item, field, value)
        if color_ids is not None:
            item.colors = await self.colors.get_many(color_ids)
        if tag_ids is not None:
            item.tags = await self.tags.get_many(tag_ids)
        await self.items.session.flush()
        # Re-fetch so a changed category relationship is reloaded, not stale.
        return await self.get(item_id)

    async def set_image(self, item_id: int, relative_path: str) -> ClothingItem:
        """Attach a stored image path, removing any previous image file."""
        item = await self.get(item_id)
        if item.image_path and item.image_path != relative_path:
            storage_service.delete_image(item.image_path)
        item.image_path = relative_path
        await self.items.session.flush()
        # Re-fetch so relationships and the refreshed updated_at load eagerly.
        return await self.get(item_id)

    async def apply_ai_metadata(self, item_id: int, metadata: dict) -> ClothingItem:
        """Persist vision auto-tagging output on the item."""
        item = await self.get(item_id)
        item.ai_metadata = metadata
        await self.items.session.flush()
        # Re-fetch so relationships and the refreshed updated_at load eagerly.
        return await self.get(item_id)

    async def delete(self, item_id: int) -> None:
        item = await self.get(item_id)
        storage_service.delete_image(item.image_path)
        await self.items.delete(item)
