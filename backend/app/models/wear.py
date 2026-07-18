"""Wear history — the source of truth for usage analytics.

Each row records that an item and/or outfit was worn on a given date. Wear
counters on ``ClothingItem`` / ``Outfit`` are denormalized caches maintained by
the service layer for fast reads; this log is the authoritative history.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.clothing import ClothingItem
    from app.models.outfit import Outfit


class WearLog(Base, PrimaryKeyMixin, TimestampMixin):
    """A single record of something being worn on a date."""

    __tablename__ = "wear_log"

    worn_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Either or both may be set: logging a full outfit, a single item, or both.
    outfit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("outfits.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("clothing_items.id", ondelete="CASCADE"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    outfit: Mapped["Outfit | None"] = relationship(back_populates="wear_logs")
    item: Mapped["ClothingItem | None"] = relationship(back_populates="wear_logs")
