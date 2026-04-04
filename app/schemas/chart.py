"""Pydantic schemas for natal chart creation and factor retrieval."""

from __future__ import annotations

from datetime import date, datetime, time
import uuid

from pydantic import AliasChoices, Field, field_validator

from app.schemas.base import AstroBaseSchema, IDSchema, TimestampedSchema


class NatalChartCreate(AstroBaseSchema):
    name: str | None = Field(None, max_length=120)
    birth_date_local: date
    birth_time_local: time
    timezone_offset_minutes: int = Field(..., ge=-720, le=840)
    location_name: str | None = Field(None, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    house_system: str = Field(default="placidus", max_length=30)
    notes: str | None = None
    metadata_json: dict | None = Field(
        None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

    @field_validator("house_system")
    @classmethod
    def normalize_house_system(cls, value: str) -> str:
        return value.lower()


class ChartPositionRead(IDSchema, TimestampedSchema):
    body_id: uuid.UUID | None = None
    body_code: str
    longitude_deg: float
    latitude_deg: float
    speed_deg_per_day: float | None = None
    is_retrograde: bool
    sign_code: str
    house_number: int | None = None
    rulerships_json: list[int] | None = None


class ChartAspectRead(IDSchema, TimestampedSchema):
    aspect_id: uuid.UUID | None = None
    body_a_code: str
    body_b_code: str
    aspect_code: str
    exact_angle_deg: float
    orb_deg: float
    applying: bool


class ChartAngleRead(IDSchema, TimestampedSchema):
    angle_id: uuid.UUID | None = None
    angle_code: str
    longitude_deg: float
    sign_code: str


class ChartHouseCuspRead(IDSchema, TimestampedSchema):
    house_number: int
    longitude_deg: float
    sign_code: str


class ChartRead(IDSchema, TimestampedSchema):
    chart_type: str
    name: str | None = None
    provider: str
    house_system: str
    birth_date_local: date
    birth_time_local: time
    birth_datetime_utc: datetime
    timezone_offset_minutes: int
    location_name: str | None = None
    latitude: float
    longitude: float
    notes: str | None = None
    metadata_json: dict | None = Field(
        None,
        serialization_alias="metadata",
    )
    positions: list[ChartPositionRead] = []
    aspects: list[ChartAspectRead] = []
    angles: list[ChartAngleRead] = []
    house_cusps: list[ChartHouseCuspRead] = []


class ChartFactorsRead(AstroBaseSchema):
    chart_id: uuid.UUID
    provider: str
    positions: list[ChartPositionRead]
    aspects: list[ChartAspectRead]
    angles: list[ChartAngleRead]
    house_cusps: list[ChartHouseCuspRead]
    rulerships: dict[str, list[int]]
