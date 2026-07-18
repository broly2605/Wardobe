"""AI persistence: learned style memory and recommendation history.

``AIMemory`` is a lightweight key/value store of durable style knowledge (learned
preferences, disliked pairings, notes) that gets fed back into future prompts —
this is the "AI remembers your taste" feature, all inside Postgres.

``Recommendation`` records every outfit the stylist proposes plus the user's
response, forming a feedback loop the recommender learns from over time.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import Occasion, RecommendationStatus, string_enum


class AIMemory(Base, PrimaryKeyMixin, TimestampMixin):
    """A single durable piece of learned style knowledge.

    ``key`` is a stable identifier (e.g. ``preferred_palette``); ``value`` holds
    structured JSON so anything from a scalar preference to a list of disliked
    combinations can be stored without schema changes. ``weight`` lets the
    recommender prioritize stronger signals.
    """

    __tablename__ = "ai_memory"
    __table_args__ = (UniqueConstraint("key", name="uq_ai_memory_key"),)

    key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class Recommendation(Base, PrimaryKeyMixin, TimestampMixin):
    """A recorded AI outfit suggestion and the user's response to it."""

    __tablename__ = "recommendations"

    occasion: Mapped[Occasion] = mapped_column(
        string_enum(Occasion, "occasion_enum"),
        default=Occasion.EVERYDAY,
        nullable=False,
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        string_enum(RecommendationStatus, "recommendation_status_enum"),
        default=RecommendationStatus.SUGGESTED,
        nullable=False,
        index=True,
    )
    # Whether GPT produced this suggestion (True) or the rule-based fallback.
    used_ai: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Human-readable styling rationale shown to the user.
    rationale: Mapped[str | None] = mapped_column(Text)
    # The proposed outfit as a structured payload (item ids, ordering, notes).
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Optional link to the weather snapshot that informed the suggestion.
    weather_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("weather_cache.id", ondelete="SET NULL")
    )
    # Optional link to an outfit if the suggestion was saved as one.
    outfit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("outfits.id", ondelete="SET NULL")
    )
