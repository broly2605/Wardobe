"""Serialization helpers shared by routes.

The DB stores only the relative image path; the frontend needs a fully-usable
URL. These helpers convert ORM objects to read schemas while injecting the
public ``image_url`` derived from the storage service.
"""

from __future__ import annotations

from app.models.clothing import ClothingItem
from app.models.outfit import Outfit
from app.schemas.clothing import ClothingItemRead
from app.schemas.outfit import OutfitItemRead, OutfitRead
from app.services.storage import storage_service


def serialize_item(item: ClothingItem) -> ClothingItemRead:
    """ORM item -> read schema with a resolved public image URL."""
    read = ClothingItemRead.model_validate(item)
    read.image_url = storage_service.public_url(item.image_path)
    return read


def serialize_outfit(outfit: Outfit) -> OutfitRead:
    """ORM outfit -> read schema, enriching each member item's image URL."""
    members = [
        OutfitItemRead(
            id=member.id,
            position=member.position,
            item=serialize_item(member.item),
        )
        for member in outfit.items
    ]
    read = OutfitRead.model_validate(outfit)
    read.items = members
    return read
