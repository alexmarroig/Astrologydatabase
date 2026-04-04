"""Intermediate persistence for interpretive prioritization results."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InterpretiveMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Raw rule match produced from chart factors before deduped prioritization."""

    __tablename__ = "interpretive_matches"
    __table_args__ = (
        UniqueConstraint("chart_id", "rule_id", "factor_key", name="uq_interpretive_match_factor"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interpretation_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    factor_key: Mapped[str] = mapped_column(String(200), nullable=False)
    base_weight: Mapped[float] = mapped_column(Float, nullable=False)
    angularity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    exactness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    asc_ruler_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    theme_codes_json: Mapped[list | None] = mapped_column(JSON)
    details_json: Mapped[dict | None] = mapped_column(JSON)

    chart = relationship("Chart")
    rule = relationship("InterpretationRule")
    priorities: Mapped[list["InterpretivePriority"]] = relationship(
        "InterpretivePriority",
        back_populates="primary_match",
        lazy="select",
    )


class InterpretivePriority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Deduped prioritized interpretation item ready for synthesis."""

    __tablename__ = "interpretive_priority"
    __table_args__ = (
        UniqueConstraint("chart_id", "rule_id", name="uq_interpretive_priority_rule"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interpretation_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interpretive_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    redundancy_group: Mapped[str] = mapped_column(String(200), nullable=False)
    thematic_repetition_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    matched_themes_json: Mapped[list | None] = mapped_column(JSON)
    summary_json: Mapped[dict | None] = mapped_column(JSON)

    chart = relationship("Chart")
    rule = relationship("InterpretationRule")
    primary_match: Mapped["InterpretiveMatch"] = relationship(
        "InterpretiveMatch",
        back_populates="priorities",
    )


class ThematicCluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Aggregated thematic grouping over prioritized interpretation items."""

    __tablename__ = "thematic_clusters"
    __table_args__ = (
        UniqueConstraint("chart_id", "theme_code", name="uq_thematic_cluster_theme"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    theme_code: Mapped[str] = mapped_column(String(30), nullable=False)
    cluster_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_count: Mapped[int] = mapped_column(Integer, nullable=False)
    top_priority_ids_json: Mapped[list | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    chart = relationship("Chart")
