"""Enumerations shared across ORM models and Pydantic schemas.

These are plain string enums (stored as ``VARCHAR`` via SQLAlchemy) rather than
native Postgres ``ENUM`` types. String columns are far easier to evolve — adding
a value never requires a migration on the enum type — while the Python-side enum
still gives us type safety and validation.
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum


def string_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """Return a VARCHAR-backed SQLAlchemy Enum for ``enum_cls``.

    ``native_enum=False`` stores the value as a plain string (so adding enum
    members never requires a DB migration), while ``values_callable`` ensures
    the stored value is the member *value* (e.g. ``"all_season"``) and reads are
    converted back into the Python enum — giving correct round-tripping.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        name=name,
        values_callable=lambda cls: [member.value for member in cls],
    )


class Season(str, Enum):
    """Season suitability for a clothing item."""

    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"


class Formality(str, Enum):
    """How formal an item or outfit is, on an ordered scale."""

    LOUNGE = "lounge"
    CASUAL = "casual"
    SMART_CASUAL = "smart_casual"
    BUSINESS = "business"
    FORMAL = "formal"


class Pattern(str, Enum):
    """Visual pattern detected on a garment."""

    SOLID = "solid"
    STRIPED = "striped"
    CHECKED = "checked"
    PLAID = "plaid"
    FLORAL = "floral"
    POLKA_DOT = "polka_dot"
    GRAPHIC = "graphic"
    ANIMAL = "animal"
    CAMOUFLAGE = "camouflage"
    GEOMETRIC = "geometric"
    ABSTRACT = "abstract"
    PRINTED = "printed"
    OTHER = "other"


class Texture(str, Enum):
    """Surface texture / knit feel of a garment."""

    SMOOTH = "smooth"
    RIBBED = "ribbed"
    KNIT = "knit"
    FLEECE = "fleece"
    DENIM = "denim"
    LEATHER = "leather"
    SUEDE = "suede"
    CORDUROY = "corduroy"
    SATIN = "satin"
    LACE = "lace"
    QUILTED = "quilted"
    TEXTURED = "textured"
    OTHER = "other"


class SleeveLength(str, Enum):
    """Sleeve length of a top/dress/outerwear item."""

    SLEEVELESS = "sleeveless"
    SHORT = "short"
    THREE_QUARTER = "three_quarter"
    LONG = "long"
    NOT_APPLICABLE = "not_applicable"


class Fit(str, Enum):
    """How the garment fits the body."""

    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    TAILORED = "tailored"
    LOOSE = "loose"
    OTHER = "other"


class Occasion(str, Enum):
    """Occasion an outfit is intended for."""

    EVERYDAY = "everyday"
    WORK = "work"
    WORKOUT = "workout"
    DATE = "date"
    PARTY = "party"
    FORMAL_EVENT = "formal_event"
    TRAVEL = "travel"
    OUTDOOR = "outdoor"


class WeatherCondition(str, Enum):
    """Simplified weather condition buckets derived from Open-Meteo codes."""

    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    STORM = "storm"
    FOG = "fog"


class RecommendationStatus(str, Enum):
    """Lifecycle of an AI recommendation, used to learn from feedback."""

    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    WORN = "worn"


class FavoriteTargetType(str, Enum):
    """What a favorite points at (polymorphic target)."""

    ITEM = "item"
    OUTFIT = "outfit"
