"""Clothing item endpoints: CRUD, image upload, and AI auto-tagging."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.api.deps import ItemServiceDep, StylistServiceDep
from app.api.serialization import serialize_item
from app.models.enums import Formality, Season
from app.schemas.clothing import (
    ClothingItemCreate,
    ClothingItemRead,
    ClothingItemUpdate,
)
from app.schemas.common import Message, Page
from app.services.item_service import ItemNotFoundError
from app.services.storage import ImageValidationError, storage_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=Page[ClothingItemRead])
async def list_items(
    service: ItemServiceDep,
    category_id: int | None = None,
    season: Season | None = None,
    formality: Formality | None = None,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = Query(default=60, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[ClothingItemRead]:
    """List wardrobe items with optional filtering and pagination."""
    items, total = await service.list(
        category_id=category_id,
        season=season,
        formality=formality,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return Page(
        items=[serialize_item(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ClothingItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ClothingItemCreate, service: ItemServiceDep
) -> ClothingItemRead:
    """Create a new clothing item (name + category required, rest optional)."""
    item = await service.create(payload)
    return serialize_item(item)


@router.get("/{item_id}", response_model=ClothingItemRead)
async def get_item(item_id: int, service: ItemServiceDep) -> ClothingItemRead:
    try:
        item = await service.get(item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_item(item)


@router.patch("/{item_id}", response_model=ClothingItemRead)
async def update_item(
    item_id: int, payload: ClothingItemUpdate, service: ItemServiceDep
) -> ClothingItemRead:
    try:
        item = await service.update(item_id, payload)
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_item(item)


@router.delete("/{item_id}", response_model=Message)
async def delete_item(item_id: int, service: ItemServiceDep) -> Message:
    try:
        await service.delete(item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return Message(detail="Item deleted.")


@router.post("/{item_id}/image", response_model=ClothingItemRead)
async def upload_item_image(
    item_id: int,
    service: ItemServiceDep,
    file: UploadFile = File(...),
) -> ClothingItemRead:
    """Upload (or replace) the item's image; stored on the local filesystem."""
    try:
        relative_path = await storage_service.save_image(file)
    except ImageValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    try:
        item = await service.set_image(item_id, relative_path)
    except ItemNotFoundError as exc:
        # Roll back the just-saved file so we don't leak an orphan.
        storage_service.delete_image(relative_path)
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_item(item)


@router.post("/{item_id}/auto-tag", response_model=ClothingItemRead)
async def auto_tag_item(
    item_id: int,
    service: ItemServiceDep,
    stylist: StylistServiceDep,
    file: UploadFile = File(...),
) -> ClothingItemRead:
    """Run vision auto-tagging on an image and store the result on the item.

    Requires an OpenAI key; without one the stylist returns no tags and a 503
    is raised so the client can fall back to manual entry.
    """
    raw = await file.read()
    metadata = await stylist.tag_image(raw)
    if metadata is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI auto-tagging is unavailable. Configure OPENAI_API_KEY to enable it.",
        )
    try:
        item = await service.apply_ai_metadata(item_id, metadata)
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_item(item)
