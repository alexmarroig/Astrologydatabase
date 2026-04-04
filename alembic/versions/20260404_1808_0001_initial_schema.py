"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-04 18:08:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models.mixins import GUID


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signs",
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name_pt", sa.String(length=60), nullable=False),
        sa.Column("name_en", sa.String(length=60), nullable=False),
        sa.Column("symbol", sa.String(length=5), nullable=True),
        sa.Column("order_num", sa.SmallInteger(), nullable=False),
        sa.Column("element", sa.String(length=10), nullable=False),
        sa.Column("modality", sa.String(length=10), nullable=False),
        sa.Column("polarity", sa.String(length=10), nullable=False),
        sa.Column("start_degree", sa.Float(), nullable=False),
        sa.Column("end_degree", sa.Float(), nullable=False),
        sa.Column("opposite_sign_id", GUID(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("themes", sa.JSON(), nullable=True),
        sa.Column("archetype_description", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["opposite_sign_id"], ["signs.id"], name="fk_sign_opposite"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_signs_code"), "signs", ["code"], unique=False)
    op.create_index(op.f("ix_signs_order_num"), "signs", ["order_num"], unique=False)

    op.create_table(
        "bodies",
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name_pt", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80), nullable=False),
        sa.Column("symbol", sa.String(length=5), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("is_personal", sa.Boolean(), nullable=False),
        sa.Column("is_luminary", sa.Boolean(), nullable=False),
        sa.Column("is_retrograde_capable", sa.Boolean(), nullable=True),
        sa.Column("swisseph_id", sa.Integer(), nullable=True),
        sa.Column("swisseph_flag", sa.Integer(), nullable=True),
        sa.Column("orbital_period_days", sa.Float(), nullable=True),
        sa.Column("average_daily_motion", sa.Float(), nullable=True),
        sa.Column("domicile_signs", sa.JSON(), nullable=True),
        sa.Column("exaltation_sign", sa.String(length=20), nullable=True),
        sa.Column("exile_signs", sa.JSON(), nullable=True),
        sa.Column("fall_sign", sa.String(length=20), nullable=True),
        sa.Column("traditional_domicile_signs", sa.JSON(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("archetype_description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_bodies_code"), "bodies", ["code"], unique=False)

    op.create_table(
        "houses",
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("name_pt", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80), nullable=False),
        sa.Column("position_type", sa.String(length=20), nullable=False),
        sa.Column("natural_sign_code", sa.String(length=20), nullable=True),
        sa.Column("natural_body_code", sa.String(length=30), nullable=True),
        sa.Column("opposite_house_number", sa.SmallInteger(), nullable=True),
        sa.Column("themes", sa.JSON(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("archetype_description", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_index(op.f("ix_houses_number"), "houses", ["number"], unique=False)

    op.create_table(
        "aspects",
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name_pt", sa.String(length=60), nullable=False),
        sa.Column("name_en", sa.String(length=60), nullable=False),
        sa.Column("symbol", sa.String(length=5), nullable=True),
        sa.Column("angle_degrees", sa.Float(), nullable=False),
        sa.Column("max_orb_default", sa.Float(), nullable=False),
        sa.Column("quality", sa.String(length=20), nullable=False),
        sa.Column("nature", sa.String(length=20), nullable=False),
        sa.Column("orb_overrides", sa.JSON(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_aspects_code"), "aspects", ["code"], unique=False)

    op.create_table(
        "angles",
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name_pt", sa.String(length=40), nullable=False),
        sa.Column("name_en", sa.String(length=40), nullable=False),
        sa.Column("abbreviation", sa.String(length=5), nullable=False),
        sa.Column("opposite_angle_code", sa.String(length=10), nullable=True),
        sa.Column("associated_house_number", sa.SmallInteger(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_angles_code"), "angles", ["code"], unique=False)

    op.create_table(
        "schools",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name_pt", sa.String(length=120), nullable=False),
        sa.Column("name_en", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("primary_authors", sa.JSON(), nullable=True),
        sa.Column("origin_country", sa.String(length=60), nullable=True),
        sa.Column("origin_decade", sa.SmallInteger(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_schools_code"), "schools", ["code"], unique=False)

    op.create_table(
        "sources",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=150), nullable=False),
        sa.Column("publication_year", sa.SmallInteger(), nullable=True),
        sa.Column("isbn", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("school_id", GUID(), nullable=True),
        sa.Column("trust_level", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn"),
    )
    op.create_index(op.f("ix_sources_title"), "sources", ["title"], unique=False)
    op.create_index(op.f("ix_sources_school_id"), "sources", ["school_id"], unique=False)

    op.create_table(
        "interpretation_rules",
        sa.Column("canonical_code", sa.String(length=150), nullable=False),
        sa.Column("rule_type", sa.String(length=40), nullable=False),
        sa.Column("subject_a_type", sa.String(length=20), nullable=True),
        sa.Column("subject_a_id", sa.String(length=50), nullable=True),
        sa.Column("subject_b_type", sa.String(length=20), nullable=True),
        sa.Column("subject_b_id", sa.String(length=50), nullable=True),
        sa.Column("subject_c_type", sa.String(length=20), nullable=True),
        sa.Column("subject_c_id", sa.String(length=50), nullable=True),
        sa.Column("school_id", GUID(), nullable=False),
        sa.Column("source_id", GUID(), nullable=True),
        sa.Column("source_chapter", sa.String(length=150), nullable=True),
        sa.Column("source_page", sa.String(length=20), nullable=True),
        sa.Column("interpretive_weight", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("interpretive_weight >= 0 AND interpretive_weight <= 10", name="ck_rule_weight_range"),
        sa.CheckConstraint("version >= 1", name="ck_rule_version_positive"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_code", "school_id", name="uq_rule_code_school"),
    )
    op.create_index(op.f("ix_interpretation_rules_canonical_code"), "interpretation_rules", ["canonical_code"], unique=False)
    op.create_index(op.f("ix_interpretation_rules_rule_type"), "interpretation_rules", ["rule_type"], unique=False)
    op.create_index(op.f("ix_interpretation_rules_school_id"), "interpretation_rules", ["school_id"], unique=False)
    op.create_index(op.f("ix_interpretation_rules_source_id"), "interpretation_rules", ["source_id"], unique=False)
    op.create_index(op.f("ix_interpretation_rules_status"), "interpretation_rules", ["status"], unique=False)

    op.create_table(
        "interpretation_blocks",
        sa.Column("rule_id", GUID(), nullable=False),
        sa.Column("theme", sa.String(length=30), nullable=False),
        sa.Column("potency_central", sa.Text(), nullable=True),
        sa.Column("well_expressed", sa.Text(), nullable=True),
        sa.Column("poorly_expressed", sa.Text(), nullable=True),
        sa.Column("complementary_axis", sa.Text(), nullable=True),
        sa.Column("challenges", sa.Text(), nullable=True),
        sa.Column("integration_path", sa.Text(), nullable=True),
        sa.Column("keywords_json", sa.JSON(), nullable=True),
        sa.Column("interpretive_weight", sa.Float(), nullable=False),
        sa.Column("editorial_confidence", sa.Float(), nullable=False),
        sa.Column("editorial_notes", sa.Text(), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("editorial_confidence >= 0 AND editorial_confidence <= 1", name="ck_block_confidence_range"),
        sa.CheckConstraint("interpretive_weight >= 0 AND interpretive_weight <= 10", name="ck_block_weight_range"),
        sa.ForeignKeyConstraint(["rule_id"], ["interpretation_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interpretation_blocks_rule_id"), "interpretation_blocks", ["rule_id"], unique=False)
    op.create_index(op.f("ix_interpretation_blocks_theme"), "interpretation_blocks", ["theme"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interpretation_blocks_theme"), table_name="interpretation_blocks")
    op.drop_index(op.f("ix_interpretation_blocks_rule_id"), table_name="interpretation_blocks")
    op.drop_table("interpretation_blocks")

    op.drop_index(op.f("ix_interpretation_rules_status"), table_name="interpretation_rules")
    op.drop_index(op.f("ix_interpretation_rules_source_id"), table_name="interpretation_rules")
    op.drop_index(op.f("ix_interpretation_rules_school_id"), table_name="interpretation_rules")
    op.drop_index(op.f("ix_interpretation_rules_rule_type"), table_name="interpretation_rules")
    op.drop_index(op.f("ix_interpretation_rules_canonical_code"), table_name="interpretation_rules")
    op.drop_table("interpretation_rules")

    op.drop_index(op.f("ix_sources_school_id"), table_name="sources")
    op.drop_index(op.f("ix_sources_title"), table_name="sources")
    op.drop_table("sources")

    op.drop_index(op.f("ix_schools_code"), table_name="schools")
    op.drop_table("schools")

    op.drop_index(op.f("ix_angles_code"), table_name="angles")
    op.drop_table("angles")

    op.drop_index(op.f("ix_aspects_code"), table_name="aspects")
    op.drop_table("aspects")

    op.drop_index(op.f("ix_houses_number"), table_name="houses")
    op.drop_table("houses")

    op.drop_index(op.f("ix_bodies_code"), table_name="bodies")
    op.drop_table("bodies")

    op.drop_index(op.f("ix_signs_order_num"), table_name="signs")
    op.drop_index(op.f("ix_signs_code"), table_name="signs")
    op.drop_table("signs")
