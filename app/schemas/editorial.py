"""
Pydantic schemas for the editorial domain.

CRUD schemas follow the pattern:
  - XxxCreate  : Fields required to create a resource
  - XxxUpdate  : Fields allowed in a PATCH (all optional)
  - XxxRead    : Full response schema (includes id, timestamps, relations)
  - XxxList    : Slim response schema for list endpoints

Editorial workflow transitions are validated in the service layer,
not in schemas. Schemas only validate data shape and types.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator

from app.core.enums import (
    InterpretiveTheme,
    RuleStatus,
    RuleType,
    SchoolType,
    SourceTrustLevel,
    SubjectType,
)
from app.schemas.base import AstroBaseSchema, IDSchema, TimestampedSchema


# ── School ────────────────────────────────────────────────────────────────────

class SchoolCreate(AstroBaseSchema):
    code: str = Field(..., min_length=2, max_length=40, pattern=r"^[a-z_]+$")
    name_pt: str = Field(..., min_length=2, max_length=120)
    name_en: str = Field(..., min_length=2, max_length=120)
    description: str | None = None
    primary_authors: list[str] | None = None
    origin_country: str | None = None
    origin_decade: int | None = Field(None, ge=1800, le=2100)


class SchoolUpdate(AstroBaseSchema):
    name_pt: str | None = Field(None, min_length=2, max_length=120)
    name_en: str | None = Field(None, min_length=2, max_length=120)
    description: str | None = None
    primary_authors: list[str] | None = None
    is_active: bool | None = None


class SchoolRead(IDSchema, TimestampedSchema):
    code: str
    name_pt: str
    name_en: str
    description: str | None = None
    primary_authors: list[str] | None = None
    origin_country: str | None = None
    origin_decade: int | None = None
    is_active: bool


class SchoolList(IDSchema):
    code: str
    name_pt: str
    name_en: str
    is_active: bool


# ── Source ────────────────────────────────────────────────────────────────────

class SourceCreate(AstroBaseSchema):
    title: str = Field(..., min_length=2, max_length=255)
    author: str = Field(..., min_length=2, max_length=150)
    publication_year: int | None = Field(None, ge=1800, le=2100)
    isbn: str | None = Field(None, max_length=20)
    language: str = Field(default="pt", max_length=10)
    school_id: uuid.UUID | None = None
    trust_level: str = Field(default=SourceTrustLevel.SECONDARY.value)
    source_type: str = Field(default="book", max_length=30)
    notes: str | None = None
    metadata_json: dict[str, Any] | None = Field(
        None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

    @field_validator("trust_level")
    @classmethod
    def validate_trust_level(cls, v: str) -> str:
        allowed = {e.value for e in SourceTrustLevel}
        if v not in allowed:
            raise ValueError(f"trust_level must be one of {allowed}")
        return v


class SourceUpdate(AstroBaseSchema):
    title: str | None = Field(None, min_length=2, max_length=255)
    author: str | None = Field(None, min_length=2, max_length=150)
    publication_year: int | None = Field(None, ge=1800, le=2100)
    isbn: str | None = None
    language: str | None = None
    school_id: uuid.UUID | None = None
    trust_level: str | None = None
    source_type: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = Field(
        None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )
    is_active: bool | None = None


class SourceRead(IDSchema, TimestampedSchema):
    title: str
    author: str
    publication_year: int | None = None
    isbn: str | None = None
    language: str
    school_id: uuid.UUID | None = None
    trust_level: str
    source_type: str
    notes: str | None = None
    is_active: bool
    metadata_json: dict[str, Any] | None = Field(
        None,
        serialization_alias="metadata",
    )
    # Nested school (joined)
    school: SchoolList | None = None


class SourceList(IDSchema):
    title: str
    author: str
    publication_year: int | None = None
    language: str
    trust_level: str
    source_type: str
    is_active: bool


# ── InterpretationRule ────────────────────────────────────────────────────────

class InterpretationRuleCreate(AstroBaseSchema):
    """
    Create a new interpretation rule.

    canonical_code must be unique within a school.
    Convention: SUBJECT_A__RULE_TYPE__SUBJECT_B[__SUBJECT_C]
    Example:    SUN__PLANET_IN_SIGN__SCORPIO
    """
    canonical_code: str = Field(
        ..., min_length=3, max_length=150,
        description="Unique canonical identifier. Example: SUN__PLANET_IN_SIGN__SCORPIO"
    )
    rule_type: str = Field(..., description="RuleType enum value")

    subject_a_type: str | None = Field(None, description="SubjectType of subject A")
    subject_a_id: str | None = Field(None, max_length=50)
    subject_b_type: str | None = None
    subject_b_id: str | None = Field(None, max_length=50)
    subject_c_type: str | None = None
    subject_c_id: str | None = Field(None, max_length=50)

    school_id: uuid.UUID
    source_id: uuid.UUID | None = None
    source_chapter: str | None = Field(None, max_length=150)
    source_page: str | None = Field(None, max_length=20)

    interpretive_weight: float = Field(default=5.0, ge=0, le=10)
    notes: str | None = None
    metadata_json: dict[str, Any] | None = Field(
        None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        allowed = {e.value for e in RuleType}
        if v not in allowed:
            raise ValueError(f"rule_type must be one of {allowed}")
        return v

    @field_validator("subject_a_type", "subject_b_type", "subject_c_type")
    @classmethod
    def validate_subject_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {e.value for e in SubjectType}
        if v not in allowed:
            raise ValueError(f"subject type must be one of {allowed}")
        return v


class InterpretationRuleUpdate(AstroBaseSchema):
    """
    Update an interpretation rule.
    All fields optional — PATCH semantics.
    Status transitions are validated in the service layer.
    """
    canonical_code: str | None = Field(None, min_length=3, max_length=150)
    rule_type: str | None = None
    subject_a_type: str | None = None
    subject_a_id: str | None = None
    subject_b_type: str | None = None
    subject_b_id: str | None = None
    subject_c_type: str | None = None
    subject_c_id: str | None = None
    school_id: uuid.UUID | None = None
    source_id: uuid.UUID | None = None
    source_chapter: str | None = None
    source_page: str | None = None
    interpretive_weight: float | None = Field(None, ge=0, le=10)
    status: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = Field(
        None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class InterpretationRuleRead(IDSchema, TimestampedSchema):
    canonical_code: str
    rule_type: str
    subject_a_type: str | None = None
    subject_a_id: str | None = None
    subject_b_type: str | None = None
    subject_b_id: str | None = None
    subject_c_type: str | None = None
    subject_c_id: str | None = None
    school_id: uuid.UUID
    source_id: uuid.UUID | None = None
    source_chapter: str | None = None
    source_page: str | None = None
    interpretive_weight: float
    status: str
    version: int
    notes: str | None = None
    metadata_json: dict[str, Any] | None = Field(
        None,
        serialization_alias="metadata",
    )
    # Nested relations
    school: SchoolList | None = None
    source: SourceList | None = None
    blocks: list["InterpretationBlockRead"] = []


class InterpretationRuleList(IDSchema):
    canonical_code: str
    rule_type: str
    subject_a_id: str | None = None
    subject_b_id: str | None = None
    subject_c_id: str | None = None
    interpretive_weight: float
    status: str
    version: int


# ── InterpretationBlock ───────────────────────────────────────────────────────

class InterpretationBlockCreate(AstroBaseSchema):
    rule_id: uuid.UUID
    theme: str = Field(..., description="InterpretiveTheme enum value")

    potency_central: str | None = None
    well_expressed: str | None = None
    poorly_expressed: str | None = None
    complementary_axis: str | None = None
    challenges: str | None = None
    integration_path: str | None = None

    keywords_json: list[str] | None = None
    interpretive_weight: float = Field(default=5.0, ge=0, le=10)
    editorial_confidence: float = Field(default=0.8, ge=0, le=1)
    editorial_notes: str | None = None

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        allowed = {e.value for e in InterpretiveTheme}
        if v not in allowed:
            raise ValueError(f"theme must be one of {allowed}")
        return v


class InterpretationBlockUpdate(AstroBaseSchema):
    theme: str | None = None
    potency_central: str | None = None
    well_expressed: str | None = None
    poorly_expressed: str | None = None
    complementary_axis: str | None = None
    challenges: str | None = None
    integration_path: str | None = None
    keywords_json: list[str] | None = None
    interpretive_weight: float | None = Field(None, ge=0, le=10)
    editorial_confidence: float | None = Field(None, ge=0, le=1)
    editorial_notes: str | None = None


class InterpretationBlockRead(IDSchema, TimestampedSchema):
    rule_id: uuid.UUID
    theme: str
    potency_central: str | None = None
    well_expressed: str | None = None
    poorly_expressed: str | None = None
    complementary_axis: str | None = None
    challenges: str | None = None
    integration_path: str | None = None
    keywords_json: list[str] | None = None
    interpretive_weight: float
    editorial_confidence: float
    editorial_notes: str | None = None


class InterpretationBlockList(IDSchema):
    rule_id: uuid.UUID
    theme: str
    interpretive_weight: float
    editorial_confidence: float
    keywords_json: list[str] | None = None


# ── Resolve forward references ────────────────────────────────────────────────
InterpretationRuleRead.model_rebuild()
