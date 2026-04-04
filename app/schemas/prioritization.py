"""Intermediate schemas for interpretive prioritization snapshots."""

from __future__ import annotations

from datetime import datetime
import uuid

from pydantic import Field

from app.schemas.base import AstroBaseSchema, IDSchema, TimestampedSchema


class RuleSummaryRead(AstroBaseSchema):
    id: uuid.UUID
    canonical_code: str
    rule_type: str
    subject_a_type: str | None = None
    subject_a_id: str | None = None
    subject_b_type: str | None = None
    subject_b_id: str | None = None
    subject_c_type: str | None = None
    subject_c_id: str | None = None


class InterpretiveMatchRead(IDSchema, TimestampedSchema):
    chart_id: uuid.UUID
    rule_id: uuid.UUID
    factor_type: str
    factor_key: str
    base_weight: float
    angularity_score: float
    exactness_score: float
    asc_ruler_score: float
    raw_score: float
    theme_codes_json: list[str] = Field(default_factory=list, serialization_alias="themes")
    details_json: dict | None = Field(
        None,
        serialization_alias="details",
    )
    rule: RuleSummaryRead


class InterpretivePriorityRead(IDSchema, TimestampedSchema):
    chart_id: uuid.UUID
    rule_id: uuid.UUID
    primary_match_id: uuid.UUID
    rank: int
    total_score: float
    redundancy_group: str
    thematic_repetition_score: float
    match_count: int
    matched_themes_json: list[str] = Field(
        default_factory=list,
        serialization_alias="themes",
    )
    summary_json: dict | None = Field(
        None,
        serialization_alias="summary",
    )
    rule: RuleSummaryRead


class ThematicClusterRead(IDSchema, TimestampedSchema):
    chart_id: uuid.UUID
    theme_code: str
    cluster_score: float
    priority_count: int
    top_priority_ids_json: list[uuid.UUID] = Field(
        default_factory=list,
        serialization_alias="top_priority_ids",
    )
    summary: str | None = None
    metadata_json: dict | None = Field(
        None,
        serialization_alias="metadata",
    )


class InterpretiveSnapshotRead(AstroBaseSchema):
    chart_id: uuid.UUID
    school_code: str
    generated_at: datetime
    matches: list[InterpretiveMatchRead]
    priorities: list[InterpretivePriorityRead]
    clusters: list[ThematicClusterRead]
