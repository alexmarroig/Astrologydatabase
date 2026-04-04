"""
Editorial domain models.

These tables manage the knowledge base of the astrological system:
the interpretive rules, their sources, and thematic blocks.

Tables:
  - schools              : Astrological schools / traditions
  - sources              : Reference works (books, courses, materials)
  - interpretation_rules : One rule per astrological factor+school combination
  - interpretation_blocks: Semantic content fields for each rule
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    JSON,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    InterpretiveTheme,
    RuleStatus,
    RuleType,
    SchoolType,
    SourceTrustLevel,
    SubjectType,
)
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class School(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Astrological school / interpretive tradition.

    Each interpretation rule belongs to exactly one school.
    The school namespace prevents conflicts between different
    methodological approaches to the same astrological factor.

    The default school for this system is luz_e_sombra.
    """
    __tablename__ = "schools"

    code: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    name_pt: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Primary representative author(s) of this school
    primary_authors: Mapped[list | None] = mapped_column(JSON)  # ["Claudia Lisboa"]
    origin_country: Mapped[str | None] = mapped_column(String(60))
    origin_decade: Mapped[int | None] = mapped_column(SmallInteger)

    # ── Relationships ─────────────────────────────────────────────────────
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="school", lazy="select"
    )
    rules: Mapped[list["InterpretationRule"]] = relationship(
        "InterpretationRule", back_populates="school", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<School {self.code}>"


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Reference source: a book, course, lecture series, or other material.

    Every interpretation rule must eventually be traceable to a source.
    This enables editorial accountability and conflict resolution between
    different takes on the same astrological factor.
    """
    __tablename__ = "sources"

    # ── Bibliographic Data ────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(150), nullable=False)
    publication_year: Mapped[int | None] = mapped_column(SmallInteger)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True)
    language: Mapped[str] = mapped_column(String(10), default="pt", nullable=False)

    # ── Classification ────────────────────────────────────────────────────
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trust_level: Mapped[str] = mapped_column(
        String(20), default=SourceTrustLevel.SECONDARY.value, nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(30), default="book", nullable=False
    )  # book | course | lecture | article | notes

    # ── Editorial Notes ───────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    # ── Relationships ─────────────────────────────────────────────────────
    school: Mapped["School | None"] = relationship(
        "School", back_populates="sources", lazy="joined"
    )
    rules: Mapped[list["InterpretationRule"]] = relationship(
        "InterpretationRule", back_populates="source", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Source '{self.title}' by {self.author}>"


class InterpretationRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Core editorial entity. One rule per astrological factor + school.

    A rule describes the symbolic potential of a specific astrological
    configuration (e.g., Sun in Scorpio, Moon in House 4, Sun square Saturn).

    The subject_a/b/c pattern allows representing any factor type
    without separate tables per factor type — a deliberate trade-off
    for flexibility over strict relational purity.

    subject_a_type / subject_a_id identify the first entity:
      - type="body", id="<body.code>" → a planet
      - type="sign", id="<sign.code>" → a zodiac sign
      - type="house", id="4"          → house number 4

    This pattern avoids a union-type FK problem while keeping
    the schema flat and easy to query.

    Design note: canonical_code is the lookup key for the synthesis
    engine. Format: SUBJECT_A__RULE_TYPE__SUBJECT_B
    Examples:
      SUN__PLANET_IN_SIGN__SCORPIO
      MOON__PLANET_IN_HOUSE__4
      SUN__ASPECT_PLANET_PLANET__SATURN__SQUARE
    """
    __tablename__ = "interpretation_rules"
    __table_args__ = (
        UniqueConstraint("canonical_code", "school_id", name="uq_rule_code_school"),
        CheckConstraint("version >= 1", name="ck_rule_version_positive"),
        CheckConstraint(
            "interpretive_weight >= 0 AND interpretive_weight <= 10",
            name="ck_rule_weight_range",
        ),
    )

    # ── Canonical Identity ────────────────────────────────────────────────
    canonical_code: Mapped[str] = mapped_column(
        String(150), nullable=False, index=True
    )
    rule_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )  # RuleType enum value

    # ── Subjects (Generic FK pattern) ─────────────────────────────────────
    # subject_a: primary entity (usually a planet/body)
    subject_a_type: Mapped[str | None] = mapped_column(String(20))   # SubjectType
    subject_a_id: Mapped[str | None] = mapped_column(String(50))     # code or number

    # subject_b: secondary entity (sign, house, second planet)
    subject_b_type: Mapped[str | None] = mapped_column(String(20))
    subject_b_id: Mapped[str | None] = mapped_column(String(50))

    # subject_c: tertiary entity (aspect type, modifier)
    subject_c_type: Mapped[str | None] = mapped_column(String(20))
    subject_c_id: Mapped[str | None] = mapped_column(String(50))

    # ── School & Source ───────────────────────────────────────────────────
    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_chapter: Mapped[str | None] = mapped_column(String(150))
    source_page: Mapped[str | None] = mapped_column(String(20))

    # ── Interpretive Weight ───────────────────────────────────────────────
    # Base weight used by synthesis engine before orbital/angular modifiers.
    # Range 0.0–10.0. Default 5.0.
    interpretive_weight: Mapped[float] = mapped_column(
        Float, default=5.0, nullable=False
    )

    # ── Editorial Workflow ────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default=RuleStatus.DRAFT.value, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ── Notes ─────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    # ── Relationships ─────────────────────────────────────────────────────
    school: Mapped["School"] = relationship(
        "School", back_populates="rules", lazy="joined"
    )
    source: Mapped["Source | None"] = relationship(
        "Source", back_populates="rules", lazy="joined"
    )
    blocks: Mapped[list["InterpretationBlock"]] = relationship(
        "InterpretationBlock",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="InterpretationBlock.theme",
    )

    def __repr__(self) -> str:
        return f"<InterpretationRule {self.canonical_code} [{self.status}]>"


class InterpretationBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Semantic content block for an interpretation rule.

    A rule may have multiple blocks covering different themes
    (identity, emotional, vocational, etc.). This allows the
    synthesis engine to retrieve only the blocks relevant to
    the requested output scope.

    The Luz e Sombra method fields:
      - potency_central    : The core symbolic potential
      - well_expressed     : Conscious / integrated manifestation
      - poorly_expressed   : Unconscious / unintegrated manifestation
      - complementary_axis : The opposite sign/house/planet dynamic
      - challenges         : Primary tensions and difficulties
      - integration_path   : Path toward integration and growth

    Design note: keywords_json is a JSON array rather than a
    PostgreSQL TEXT[] to maintain SQLite compatibility in dev.
    """
    __tablename__ = "interpretation_blocks"
    __table_args__ = (
        CheckConstraint(
            "editorial_confidence >= 0 AND editorial_confidence <= 1",
            name="ck_block_confidence_range",
        ),
        CheckConstraint(
            "interpretive_weight >= 0 AND interpretive_weight <= 10",
            name="ck_block_weight_range",
        ),
    )

    # ── Parent Rule ───────────────────────────────────────────────────────
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interpretation_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Thematic Classification ───────────────────────────────────────────
    theme: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # InterpretiveTheme enum value

    # ── Luz e Sombra Core Fields ──────────────────────────────────────────
    potency_central: Mapped[str | None] = mapped_column(Text)
    # The essential symbolic power of this configuration
    # "A força de penetrar nas camadas ocultas da realidade..."

    well_expressed: Mapped[str | None] = mapped_column(Text)
    # Conscious / integrated manifestation
    # "Profundidade emocional genuína, poder de regeneração..."

    poorly_expressed: Mapped[str | None] = mapped_column(Text)
    # Unconscious / unintegrated manifestation
    # "Obsessão, ciúme destrutivo, manipulação velada..."

    complementary_axis: Mapped[str | None] = mapped_column(Text)
    # The opposite sign/house/body and its integrative role
    # "O eixo Touro-Escorpião convoca a integração entre..."

    challenges: Mapped[str | None] = mapped_column(Text)
    # Primary tensions and psychological difficulties
    # "Medo do abandono e da vulnerabilidade..."

    integration_path: Mapped[str | None] = mapped_column(Text)
    # Paths toward growth and psychological integration
    # "Aprender a ser intenso sem se fechar..."

    # ── Synthesis Metadata ────────────────────────────────────────────────
    keywords_json: Mapped[list | None] = mapped_column(JSON)
    # ["transformação","poder","profundidade","regeneração"]

    interpretive_weight: Mapped[float] = mapped_column(
        Float, default=5.0, nullable=False
    )
    # Block-level weight (can differ from rule-level weight)

    editorial_confidence: Mapped[float] = mapped_column(
        Float, default=0.8, nullable=False
    )
    # Editorial confidence 0.0–1.0

    # ── Editorial Notes ───────────────────────────────────────────────────
    editorial_notes: Mapped[str | None] = mapped_column(Text)
    # Internal notes for editors — not shown to end users

    # ── Relationships ─────────────────────────────────────────────────────
    rule: Mapped["InterpretationRule"] = relationship(
        "InterpretationRule", back_populates="blocks", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<InterpretationBlock rule_id={self.rule_id} theme={self.theme}>"
