"""
Shared Pydantic schema utilities.

Conventions:
  - All schemas use model_config with from_attributes=True for ORM compatibility
  - UUIDs are serialized as strings in responses
  - Timestamps are serialized as ISO 8601 strings
  - Read schemas include id and timestamps; Create/Update do not
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AstroBaseSchema(BaseModel):
    """Base schema with ORM compatibility enabled."""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        populate_by_name=True,
    )


class TimestampedSchema(AstroBaseSchema):
    """Schema for models with created_at / updated_at."""
    created_at: datetime
    updated_at: datetime


class IDSchema(AstroBaseSchema):
    """Schema for models with UUID primary key."""
    id: uuid.UUID
