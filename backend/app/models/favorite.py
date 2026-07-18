"""Favorites — user-starred items or outfits.

A single table with a polymorphic ``target_type`` keeps favorites uniform and
lets the UI render a mixed "favorites" view without querying multiple tables.
Application-level integrity is enforced in the service layer (the target row is
validated to exist before insert).
"""

from __future__ import annotations

from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import FavoriteTargetType, string_enum


class Favorite(Base, PrimaryKeyMixin, TimestampMixin):
    """A favorited item or outfit."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("target_type", "target_id", name="uq_favorite_target"),
    )

    target_type: Mapped[FavoriteTargetType] = mapped_column(
        string_enum(FavoriteTargetType, "favorite_target_enum"), nullable=False
    )
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
