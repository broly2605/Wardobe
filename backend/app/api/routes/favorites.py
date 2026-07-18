"""Favorites endpoints — star items or outfits."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import FavoriteRepoDep
from app.models.favorite import Favorite
from app.schemas.common import Message
from app.schemas.favorite import FavoriteCreate, FavoriteRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteRead])
async def list_favorites(repo: FavoriteRepoDep) -> list[FavoriteRead]:
    return [FavoriteRead.model_validate(f) for f in await repo.list_all()]


@router.post("", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED)
async def add_favorite(payload: FavoriteCreate, repo: FavoriteRepoDep) -> FavoriteRead:
    """Add a favorite; idempotent — returns the existing one if already set."""
    existing = await repo.find(payload.target_type, payload.target_id)
    if existing is not None:
        return FavoriteRead.model_validate(existing)
    favorite = await repo.add(
        Favorite(target_type=payload.target_type, target_id=payload.target_id)
    )
    return FavoriteRead.model_validate(favorite)


@router.delete("/{favorite_id}", response_model=Message)
async def remove_favorite(favorite_id: int, repo: FavoriteRepoDep) -> Message:
    favorite = await repo.get(favorite_id)
    if favorite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorite not found.")
    await repo.delete(favorite)
    return Message(detail="Favorite removed.")
