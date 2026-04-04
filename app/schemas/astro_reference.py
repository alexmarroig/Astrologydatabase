"""
Pydantic schemas for astrological reference data (read-only in the API).

Reference data (signs, bodies, houses, aspects, angles) is managed
via seed scripts and migrations, not via the API. The API exposes
read-only endpoints for this data.

For each entity we define:
  - A full Read schema (returned by GET endpoints)
  - A slim List schema (returned by list endpoints — less data)
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field, field_validator

from app.core.enums import (
    AspectNature,
    AspectQuality,
    BodyCategory,
    ElementType,
    HousePosition,
    ModalityType,
    PolarityType,
)
from app.schemas.base import AstroBaseSchema, IDSchema, TimestampedSchema


# ── Sign ──────────────────────────────────────────────────────────────────────

class SignRead(IDSchema, TimestampedSchema):
    """Full sign schema returned by GET /signs/{id}."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    order_num: int
    element: str
    modality: str
    polarity: str
    start_degree: float
    end_degree: float
    opposite_sign_id: uuid.UUID | None = None
    keywords: list[str] | None = None
    themes: dict[str, Any] | None = None
    archetype_description: str | None = None


class SignList(IDSchema):
    """Slim sign schema for list responses."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    order_num: int
    element: str
    modality: str
    polarity: str


# ── Body ──────────────────────────────────────────────────────────────────────

class BodyRead(IDSchema, TimestampedSchema):
    """Full body schema returned by GET /bodies/{id}."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    category: str
    is_personal: bool
    is_luminary: bool
    is_retrograde_capable: bool
    swisseph_id: int | None = None
    orbital_period_days: float | None = None
    average_daily_motion: float | None = None
    domicile_signs: list[str] | None = None
    exaltation_sign: str | None = None
    exile_signs: list[str] | None = None
    fall_sign: str | None = None
    traditional_domicile_signs: list[str] | None = None
    keywords: list[str] | None = None
    archetype_description: str | None = None


class BodyList(IDSchema):
    """Slim body schema for list responses."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    category: str
    is_personal: bool
    is_luminary: bool


# ── House ─────────────────────────────────────────────────────────────────────

class HouseRead(IDSchema, TimestampedSchema):
    """Full house schema returned by GET /houses/{id}."""
    number: int
    name_pt: str
    name_en: str
    position_type: str
    natural_sign_code: str | None = None
    natural_body_code: str | None = None
    opposite_house_number: int | None = None
    themes: dict[str, Any] | None = None
    keywords: list[str] | None = None
    archetype_description: str | None = None


class HouseList(IDSchema):
    """Slim house schema for list responses."""
    number: int
    name_pt: str
    name_en: str
    position_type: str
    natural_sign_code: str | None = None
    opposite_house_number: int | None = None


# ── Aspect ────────────────────────────────────────────────────────────────────

class AspectRead(IDSchema, TimestampedSchema):
    """Full aspect schema returned by GET /aspects/{id}."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    angle_degrees: float
    max_orb_default: float
    quality: str
    nature: str
    orb_overrides: dict[str, float] | None = None
    keywords: list[str] | None = None
    description: str | None = None


class AspectList(IDSchema):
    """Slim aspect schema for list responses."""
    code: str
    name_pt: str
    name_en: str
    symbol: str | None = None
    angle_degrees: float
    max_orb_default: float
    quality: str
    nature: str


# ── Angle ─────────────────────────────────────────────────────────────────────

class AngleRead(IDSchema, TimestampedSchema):
    """Full angle schema returned by GET /angles/{id}."""
    code: str
    name_pt: str
    name_en: str
    abbreviation: str
    opposite_angle_code: str | None = None
    associated_house_number: int | None = None
    keywords: list[str] | None = None
    description: str | None = None


class AngleList(IDSchema):
    code: str
    name_pt: str
    name_en: str
    abbreviation: str
    opposite_angle_code: str | None = None
