"""SQLAlchemy declarative base and shared column mixins.

Every ORM model inherits from :class:`Base`. The mixins provide consistent
primary keys and audit timestamps across all tables, keeping the schema uniform
and easy to reason about.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class PrimaryKeyMixin:
    """Adds a surrogate ``BIGINT`` primary key (scales well, cloud-friendly)."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` audit columns managed by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
