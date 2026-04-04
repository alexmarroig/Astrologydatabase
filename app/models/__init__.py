"""
Models package. Import all models here so Alembic can autodiscover them.

Alembic's env.py imports Base from app.db.base and expects all models
to be registered on Base.metadata before migrations are generated.
Importing them here guarantees that.
"""

from app.models.astro_reference import Angle, Aspect, Body, House, Sign
from app.models.editorial import (
    InterpretationBlock,
    InterpretationRule,
    School,
    Source,
)
from app.models.chart import Chart, ChartAngle, ChartAspect, ChartHouseCusp, ChartPosition
from app.models.prioritization import (
    InterpretiveMatch,
    InterpretivePriority,
    ThematicCluster,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

__all__ = [
    # Reference
    "Sign",
    "Body",
    "House",
    "Aspect",
    "Angle",
    # Editorial
    "School",
    "Source",
    "InterpretationRule",
    "InterpretationBlock",
    # Charts
    "Chart",
    "ChartPosition",
    "ChartAspect",
    "ChartAngle",
    "ChartHouseCusp",
    # Prioritization
    "InterpretiveMatch",
    "InterpretivePriority",
    "ThematicCluster",
    # Mixins (exported for type checking convenience)
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
]
