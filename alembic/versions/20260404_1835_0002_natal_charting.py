"""natal charting

Revision ID: 0002_natal_charting
Revises: 0001_initial_schema
Create Date: 2026-04-04 18:35:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models.mixins import GUID


revision = "0002_natal_charting"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "charts",
        sa.Column("chart_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("house_system", sa.String(length=30), nullable=False),
        sa.Column("birth_date_local", sa.Date(), nullable=False),
        sa.Column("birth_time_local", sa.Time(), nullable=False),
        sa.Column("birth_datetime_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone_offset_minutes", sa.Integer(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_charts_id"), "charts", ["id"], unique=False)

    op.create_table(
        "chart_positions",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("body_id", GUID(), nullable=True),
        sa.Column("body_code", sa.String(length=30), nullable=False),
        sa.Column("longitude_deg", sa.Float(), nullable=False),
        sa.Column("latitude_deg", sa.Float(), nullable=False),
        sa.Column("speed_deg_per_day", sa.Float(), nullable=True),
        sa.Column("is_retrograde", sa.Boolean(), nullable=False),
        sa.Column("sign_code", sa.String(length=20), nullable=False),
        sa.Column("house_number", sa.SmallInteger(), nullable=True),
        sa.Column("rulerships_json", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["body_id"], ["bodies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "body_code", name="uq_chart_position_body"),
    )
    op.create_index(op.f("ix_chart_positions_body_id"), "chart_positions", ["body_id"], unique=False)
    op.create_index(op.f("ix_chart_positions_chart_id"), "chart_positions", ["chart_id"], unique=False)
    op.create_index(op.f("ix_chart_positions_id"), "chart_positions", ["id"], unique=False)

    op.create_table(
        "chart_aspects",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("aspect_id", GUID(), nullable=True),
        sa.Column("body_a_code", sa.String(length=30), nullable=False),
        sa.Column("body_b_code", sa.String(length=30), nullable=False),
        sa.Column("aspect_code", sa.String(length=30), nullable=False),
        sa.Column("exact_angle_deg", sa.Float(), nullable=False),
        sa.Column("orb_deg", sa.Float(), nullable=False),
        sa.Column("applying", sa.Boolean(), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["aspect_id"], ["aspects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "body_a_code", "body_b_code", "aspect_code", name="uq_chart_aspect_pair"),
    )
    op.create_index(op.f("ix_chart_aspects_aspect_id"), "chart_aspects", ["aspect_id"], unique=False)
    op.create_index(op.f("ix_chart_aspects_chart_id"), "chart_aspects", ["chart_id"], unique=False)
    op.create_index(op.f("ix_chart_aspects_id"), "chart_aspects", ["id"], unique=False)

    op.create_table(
        "chart_angles",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("angle_id", GUID(), nullable=True),
        sa.Column("angle_code", sa.String(length=10), nullable=False),
        sa.Column("longitude_deg", sa.Float(), nullable=False),
        sa.Column("sign_code", sa.String(length=20), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["angle_id"], ["angles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "angle_code", name="uq_chart_angle_code"),
    )
    op.create_index(op.f("ix_chart_angles_angle_id"), "chart_angles", ["angle_id"], unique=False)
    op.create_index(op.f("ix_chart_angles_chart_id"), "chart_angles", ["chart_id"], unique=False)
    op.create_index(op.f("ix_chart_angles_id"), "chart_angles", ["id"], unique=False)

    op.create_table(
        "chart_house_cusps",
        sa.Column("chart_id", GUID(), nullable=False),
        sa.Column("house_number", sa.SmallInteger(), nullable=False),
        sa.Column("longitude_deg", sa.Float(), nullable=False),
        sa.Column("sign_code", sa.String(length=20), nullable=False),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chart_id"], ["charts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_id", "house_number", name="uq_chart_house_cusp"),
    )
    op.create_index(op.f("ix_chart_house_cusps_chart_id"), "chart_house_cusps", ["chart_id"], unique=False)
    op.create_index(op.f("ix_chart_house_cusps_id"), "chart_house_cusps", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chart_house_cusps_id"), table_name="chart_house_cusps")
    op.drop_index(op.f("ix_chart_house_cusps_chart_id"), table_name="chart_house_cusps")
    op.drop_table("chart_house_cusps")

    op.drop_index(op.f("ix_chart_angles_id"), table_name="chart_angles")
    op.drop_index(op.f("ix_chart_angles_chart_id"), table_name="chart_angles")
    op.drop_index(op.f("ix_chart_angles_angle_id"), table_name="chart_angles")
    op.drop_table("chart_angles")

    op.drop_index(op.f("ix_chart_aspects_id"), table_name="chart_aspects")
    op.drop_index(op.f("ix_chart_aspects_chart_id"), table_name="chart_aspects")
    op.drop_index(op.f("ix_chart_aspects_aspect_id"), table_name="chart_aspects")
    op.drop_table("chart_aspects")

    op.drop_index(op.f("ix_chart_positions_id"), table_name="chart_positions")
    op.drop_index(op.f("ix_chart_positions_chart_id"), table_name="chart_positions")
    op.drop_index(op.f("ix_chart_positions_body_id"), table_name="chart_positions")
    op.drop_table("chart_positions")

    op.drop_index(op.f("ix_charts_id"), table_name="charts")
    op.drop_table("charts")
