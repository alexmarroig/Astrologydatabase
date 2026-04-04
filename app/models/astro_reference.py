"""
Astrological reference data models.

These tables contain the formal ontological vocabulary of the system.
They are seeded once at setup and rarely mutated.

Tables:
  - signs      : The 12 zodiac signs
  - bodies     : Planets, nodes, angles, asteroids, hypothetical points
  - houses     : The 12 astrological houses
  - aspects    : Aspect types (conjunction, opposition, trine, etc.)
  - angles     : Chart angles (ASC, MC, DSC, IC)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    AspectNature,
    AspectQuality,
    BodyCategory,
    DignityType,
    ElementType,
    HousePosition,
    HouseSystemType,
    ModalityType,
    PolarityType,
)
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Sign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    The 12 zodiac signs.

    Note: opposite_sign_id creates a self-referential FK.
    The eixo (axis) is central to the Luz e Sombra method:
    every sign must be understood in relation to its opposite.
    """
    __tablename__ = "signs"

    # ── Identification ────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(60), nullable=False)
    name_en: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(5))  # Unicode glyph ♈ etc.

    # ── Taxonomy ──────────────────────────────────────────────────────────
    order_num: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-12
    element: Mapped[str] = mapped_column(String(10), nullable=False)      # ElementType
    modality: Mapped[str] = mapped_column(String(10), nullable=False)     # ModalityType
    polarity: Mapped[str] = mapped_column(String(10), nullable=False)     # PolarityType

    # ── Ecliptic Position ─────────────────────────────────────────────────
    start_degree: Mapped[float] = mapped_column(Float, nullable=False)   # 0° to 330°
    end_degree: Mapped[float] = mapped_column(Float, nullable=False)     # 30° to 360°

    # ── Complementary Axis (Luz e Sombra method) ──────────────────────────
    opposite_sign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("signs.id", use_alter=True, name="fk_sign_opposite"),
        nullable=True,
    )

    # ── Semantic Content ──────────────────────────────────────────────────
    keywords: Mapped[list | None] = mapped_column(JSON)      # ["energia","ação","impulso"]
    themes: Mapped[dict | None] = mapped_column(JSON)        # {love: [...], work: [...]}
    archetype_description: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ─────────────────────────────────────────────────────
    opposite_sign: Mapped["Sign | None"] = relationship(
        "Sign",
        primaryjoin="Sign.opposite_sign_id == Sign.id",
        foreign_keys=[opposite_sign_id],
        remote_side="Sign.id",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Sign {self.code}>"


class Body(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Celestial bodies and astrological points.

    Covers: classical planets, modern planets, nodes, asteroids,
    hypothetical points (Lilith), Arabic parts, angles.

    The term 'body' is preferred over 'planet' to avoid confusion
    and to cover the full scope of factors used in interpretation.
    """
    __tablename__ = "bodies"

    # ── Identification ────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(5))  # ☉ ☽ ♄ etc.

    # ── Classification ────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # BodyCategory
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_luminary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_retrograde_capable: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Swiss Ephemeris Integration ───────────────────────────────────────
    swisseph_id: Mapped[int | None] = mapped_column(Integer)  # SE constant
    swisseph_flag: Mapped[int | None] = mapped_column(Integer)  # Calculation flag

    # ── Orbital Data ──────────────────────────────────────────────────────
    orbital_period_days: Mapped[float | None] = mapped_column(Float)
    average_daily_motion: Mapped[float | None] = mapped_column(Float)  # degrees/day

    # ── Essential Dignities ───────────────────────────────────────────────
    # Stored as JSON arrays of sign codes for flexibility
    domicile_signs: Mapped[list | None] = mapped_column(JSON)    # ["ARIES", "SCORPIO"]
    exaltation_sign: Mapped[str | None] = mapped_column(String(20))
    exile_signs: Mapped[list | None] = mapped_column(JSON)
    fall_sign: Mapped[str | None] = mapped_column(String(20))

    # ── Traditional vs Modern Rulerships ─────────────────────────────────
    # Some bodies have different traditional and modern rulerships
    traditional_domicile_signs: Mapped[list | None] = mapped_column(JSON)

    # ── Semantic Content ──────────────────────────────────────────────────
    keywords: Mapped[list | None] = mapped_column(JSON)
    archetype_description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    def __repr__(self) -> str:
        return f"<Body {self.code}>"


class House(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    The 12 astrological houses.

    Houses represent life areas/departments.
    Each house has a natural sign ruler and a complementary opposite house
    (the axis system is fundamental to Luz e Sombra method).
    """
    __tablename__ = "houses"

    # ── Identification ────────────────────────────────────────────────────
    number: Mapped[int] = mapped_column(SmallInteger, unique=True, nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)

    # ── Angular Classification ────────────────────────────────────────────
    position_type: Mapped[str] = mapped_column(String(20), nullable=False)  # HousePosition

    # ── Natural Correspondences ───────────────────────────────────────────
    natural_sign_code: Mapped[str | None] = mapped_column(String(20))    # e.g., ARIES
    natural_body_code: Mapped[str | None] = mapped_column(String(30))    # e.g., MARS

    # ── Axis / Complementary House ────────────────────────────────────────
    opposite_house_number: Mapped[int | None] = mapped_column(SmallInteger)

    # ── Semantic Content ──────────────────────────────────────────────────
    themes: Mapped[dict | None] = mapped_column(JSON)    # {primary: "...", secondary: "..."}
    keywords: Mapped[list | None] = mapped_column(JSON)
    archetype_description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<House {self.number}>"


class Aspect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Astrological aspects — angular relationships between bodies.

    Orb configuration is stored in metadata JSON to allow
    per-planet-pair orb customization without schema changes.
    """
    __tablename__ = "aspects"

    # ── Identification ────────────────────────────────────────────────────
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(60), nullable=False)
    name_en: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(5))   # ☌ ☍ △ □ ✶

    # ── Angular Definition ────────────────────────────────────────────────
    angle_degrees: Mapped[float] = mapped_column(Float, nullable=False)
    max_orb_default: Mapped[float] = mapped_column(Float, nullable=False)  # degrees

    # ── Classification ────────────────────────────────────────────────────
    quality: Mapped[str] = mapped_column(String(20), nullable=False)   # AspectQuality
    nature: Mapped[str] = mapped_column(String(20), nullable=False)    # AspectNature

    # ── Per-pair Orb Overrides ────────────────────────────────────────────
    # {"SUN-MOON": 10.0, "SUN-SATURN": 8.0}
    orb_overrides: Mapped[dict | None] = mapped_column(JSON)

    # ── Semantic Content ──────────────────────────────────────────────────
    keywords: Mapped[list | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Aspect {self.code} {self.angle_degrees}°>"


class Angle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Chart angles: ASC, MC, DSC, IC.

    Angles are treated as a separate entity from bodies because:
    1. They are calculated differently (from houses, not ephemeris)
    2. They have distinct interpretive rules
    3. They need separate editorial coverage
    """
    __tablename__ = "angles"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(40), nullable=False)
    name_en: Mapped[str] = mapped_column(String(40), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(5), nullable=False)  # ASC, MC, etc.

    # Complementary angle (ASC↔DSC, MC↔IC)
    opposite_angle_code: Mapped[str | None] = mapped_column(String(10))

    associated_house_number: Mapped[int | None] = mapped_column(SmallInteger)

    keywords: Mapped[list | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Angle {self.code}>"
