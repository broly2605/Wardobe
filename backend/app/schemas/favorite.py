"""Schemas for favorites."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import FavoriteTargetType
from app.schemas.common import ORMModel


class FavoriteCreate(BaseModel):
    target_type: FavoriteTargetType
    target_id: int


class FavoriteRead(ORMModel):
    id: int
    target_type: FavoriteTargetType
    target_id: int
    created_at: datetime
