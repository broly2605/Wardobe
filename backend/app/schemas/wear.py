"""Schemas for wear logging."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, model_validator

from app.schemas.common import ORMModel


class WearLogCreate(BaseModel):
    worn_on: date
    outfit_id: int | None = None
    item_id: int | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _require_target(self) -> "WearLogCreate":
        if self.outfit_id is None and self.item_id is None:
            raise ValueError("A wear log must reference an outfit_id and/or item_id.")
        return self


class WearLogRead(ORMModel):
    id: int
    worn_on: date
    outfit_id: int | None
    item_id: int | None
    notes: str | None
    created_at: datetime
