"""Outfit models: an ``Outfit`` and its ordered ``OutfitItem`` members."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import Formality, Occasion, string_enum

if TYPE_CHECKING:
    from app.models.clothing import ClothingItem
    from app.models.wear import WearLog


class Outfit(Base, PrimaryKeyMixin, TimestampMixin):
    """A named combination of clothing items."""

    __tablename__ = "outfits"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    occasion: Mapped[Occasion] = mapped_column(
        string_enum(Occasion, "occasion_enum"),
        default=Occasion.EVERYDAY,
        nullable=False,
    )
    formality: Mapped[Formality] = mapped_column(
        string_enum(Formality, "formality_enum"),
        default=Formality.CASUAL,
        nullable=False,
    )
    # True when the outfit was produced by the AI recommender rather than the
    # user, so analytics can distinguish curated vs generated outfits.
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wear_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    items: Mapped[list["OutfitItem"]] = relationship(
        back_populates="outfit",
        cascade="all, delete-orphan",
        order_by="OutfitItem.position",
        lazy="selectin",
    )
    wear_logs: Mapped[list["WearLog"]] = relationship(
        back_populates="outfit", cascade="all, delete-orphan"
    )


class OutfitItem(Base, PrimaryKeyMixin):
    """Association object linking an outfit to a clothing item.

    Modeled as an explicit object (rather than a bare M2M table) so each
    membership can carry a ``position`` for deterministic display ordering.
    """

    __tablename__ = "outfit_items"
    __table_args__ = (
        UniqueConstraint("outfit_id", "item_id", name="uq_outfit_item"),
    )

    outfit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    outfit: Mapped["Outfit"] = relationship(back_populates="items")
    item: Mapped["ClothingItem"] = relationship(
        back_populates="outfit_links", lazy="selectin"
    )
