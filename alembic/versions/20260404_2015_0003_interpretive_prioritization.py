"""interpretive prioritization

Revision ID: 0003_interpretive_prioritization
Revises: 0002_natal_charting
Create Date: 2026-04-04 20:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models.mixins import GUID


revision = "0003_interpretive_prioritization"
down_revision = "0002_natal_charting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interpretive_matches",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("rule_id", GUID(), nullable=False),
        sa.Column("factor_type", sa.String(length=40), nullable=False),
        sa.Column("factor_key", sa.String(length=200), nullable=False),
        sa.Column("base_weight", sa.Float(), nullable=False),
        sa.Column("angularity_score", sa.Float(), nullable=False),
        sa.Column("exactness_score", sa.Float(), nullable=False),
        sa.Column("asc_ruler_score", sa.Float(), nullable=False),
        sa.Column("raw_score", sa.Float(), nullable=False),
        sa.Column("theme_codes_json", sa.JSON(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["interpretation_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "rule_id", "factor_key", name="uq_interpretive_match_factor"),
    )
    op.create_index(op.f("ix_interpretive_matches_chart_id"), "interpretive_matches", ["chart_id"], unique=False)
    op.create_index(op.f("ix_interpretive_matches_rule_id"), "interpretive_matches", ["rule_id"], unique=False)

    op.create_table(
        "interpretive_priority",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("rule_id", GUID(), nullable=False),
        sa.Column("primary_match_id", GUID(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("redundancy_group", sa.String(length=200), nullable=False),
        sa.Column("thematic_repetition_score", sa.Float(), nullable=False),
        sa.Column("match_count", sa.Integer(), nullable=False),
        sa.Column("matched_themes_json", sa.JSON(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_match_id"], ["interpretive_matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["interpretation_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "rule_id", name="uq_interpretive_priority_rule"),
    )
    op.create_index(op.f("ix_interpretive_priority_chart_id"), "interpretive_priority", ["chart_id"], unique=False)
    op.create_index(op.f("ix_interpretive_priority_primary_match_id"), "interpretive_priority", ["primary_match_id"], unique=False)
    op.create_index(op.f("ix_interpretive_priority_rule_id"), "interpretive_priority", ["rule_id"], unique=False)

    op.create_table(
        "thematic_clusters",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("theme_code", sa.String(length=30), nullable=False),
        sa.Column("cluster_score", sa.Float(), nullable=False),
        sa.Column("priority_count", sa.Integer(), nullable=False),
        sa.Column("top_priority_ids_json", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "theme_code", name="uq_thematic_cluster_theme"),
    )
    op.create_index(op.f("ix_thematic_clusters_chart_id"), "thematic_clusters", ["chart_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_thematic_clusters_chart_id"), table_name="thematic_clusters")
    op.drop_table("thematic_clusters")

    op.drop_index(op.f("ix_interpretive_priority_rule_id"), table_name="interpretive_priority")
    op.drop_index(op.f("ix_interpretive_priority_primary_match_id"), table_name="interpretive_priority")
    op.drop_index(op.f("ix_interpretive_priority_chart_id"), table_name="interpretive_priority")
    op.drop_table("interpretive_priority")

    op.drop_index(op.f("ix_interpretive_matches_rule_id"), table_name="interpretive_matches")
    op.drop_index(op.f("ix_interpretive_matches_chart_id"), table_name="interpretive_matches")
    op.drop_table("interpretive_matches")
