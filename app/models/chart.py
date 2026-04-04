"""Natal chart calculation snapshot models."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Chart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted snapshot of a calculated natal chart."""

    __tablename__ = "charts"

    chart_type: Mapped[str] = mapped_column(String(20), default="natal", nullable=False)
    name: Mapped[str | None] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    house_system: Mapped[str] = mapped_column(String(30), default="placidus", nullable=False)
    birth_date_local: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time_local: Mapped[time] = mapped_column(Time, nullable=False)
    birth_datetime_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    location_name: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    positions: Mapped[list["ChartPosition"]] = relationship(
        "ChartPosition",
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by="ChartPosition.body_code",
        lazy="selectin",
    )
    aspects: Mapped[list["ChartAspect"]] = relationship(
        "ChartAspect",
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by=lambda: (ChartAspect.body_a_code, ChartAspect.body_b_code),
        lazy="selectin",
    )
    angles: Mapped[list["ChartAngle"]] = relationship(
        "ChartAngle",
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by="ChartAngle.angle_code",
        lazy="selectin",
    )
    house_cusps: Mapped[list["ChartHouseCusp"]] = relationship(
        "ChartHouseCusp",
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by="ChartHouseCusp.house_number",
        lazy="selectin",
    )


class ChartPosition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Calculated planetary/body position persisted for a chart."""

    __tablename__ = "chart_positions"
    __table_args__ = (
        UniqueConstraint("chart_id", "body_code", name="uq_chart_position_body"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bodies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    body_code: Mapped[str] = mapped_column(String(30), nullable=False)
    longitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    latitude_deg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    speed_deg_per_day: Mapped[float | None] = mapped_column(Float)
    is_retrograde: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sign_code: Mapped[str] = mapped_column(String(20), nullable=False)
    house_number: Mapped[int | None] = mapped_column(SmallInteger)
    rulerships_json: Mapped[list | None] = mapped_column(JSON)

    chart: Mapped["Chart"] = relationship("Chart", back_populates="positions")


class ChartAspect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Calculated aspect between two positions in a chart."""

    __tablename__ = "chart_aspects"
    __table_args__ = (
        UniqueConstraint(
            "chart_id",
            "body_a_code",
            "body_b_code",
            "aspect_code",
            name="uq_chart_aspect_pair",
        ),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aspect_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("aspects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    body_a_code: Mapped[str] = mapped_column(String(30), nullable=False)
    body_b_code: Mapped[str] = mapped_column(String(30), nullable=False)
    aspect_code: Mapped[str] = mapped_column(String(30), nullable=False)
    exact_angle_deg: Mapped[float] = mapped_column(Float, nullable=False)
    orb_deg: Mapped[float] = mapped_column(Float, nullable=False)
    applying: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    chart: Mapped["Chart"] = relationship("Chart", back_populates="aspects")


class ChartAngle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Calculated chart angles (ASC, MC, DSC, IC)."""

    __tablename__ = "chart_angles"
    __table_args__ = (
        UniqueConstraint("chart_id", "angle_code", name="uq_chart_angle_code"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    angle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("angles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    angle_code: Mapped[str] = mapped_column(String(10), nullable=False)
    longitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    sign_code: Mapped[str] = mapped_column(String(20), nullable=False)

    chart: Mapped["Chart"] = relationship("Chart", back_populates="angles")


class ChartHouseCusp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Calculated house cusps for a chart."""

    __tablename__ = "chart_house_cusps"
    __table_args__ = (
        UniqueConstraint("chart_id", "house_number", name="uq_chart_house_cusp"),
    )

    chart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("charts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    house_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    longitude_deg: Mapped[float] = mapped_column(Float, nullable=False)
    sign_code: Mapped[str] = mapped_column(String(20), nullable=False)

    chart: Mapped["Chart"] = relationship("Chart", back_populates="house_cusps")
