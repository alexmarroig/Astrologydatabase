"""Repositories for persisted interpretive prioritization snapshots."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.prioritization import (
    InterpretiveMatch,
    InterpretivePriority,
    ThematicCluster,
)
from app.repositories.base import BaseRepository


class InterpretiveMatchRepository(BaseRepository[InterpretiveMatch]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InterpretiveMatch, session)

    async def list_for_chart(self, chart_id: uuid.UUID) -> list[InterpretiveMatch]:
        stmt = (
            select(InterpretiveMatch)
            .options(joinedload(InterpretiveMatch.rule))
            .where(InterpretiveMatch.chart_id == chart_id)
            .order_by(InterpretiveMatch.raw_score.desc(), InterpretiveMatch.factor_key)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())


class InterpretivePriorityRepository(BaseRepository[InterpretivePriority]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InterpretivePriority, session)

    async def list_for_chart(self, chart_id: uuid.UUID) -> list[InterpretivePriority]:
        stmt = (
            select(InterpretivePriority)
            .options(
                joinedload(InterpretivePriority.rule),
                joinedload(InterpretivePriority.primary_match),
            )
            .where(InterpretivePriority.chart_id == chart_id)
            .order_by(InterpretivePriority.rank, InterpretivePriority.total_score.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())


class ThematicClusterRepository(BaseRepository[ThematicCluster]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ThematicCluster, session)

    async def list_for_chart(self, chart_id: uuid.UUID) -> list[ThematicCluster]:
        stmt = (
            select(ThematicCluster)
            .where(ThematicCluster.chart_id == chart_id)
            .order_by(ThematicCluster.cluster_score.desc(), ThematicCluster.theme_code)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PrioritizationSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_for_chart(self, chart_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(ThematicCluster).where(ThematicCluster.chart_id == chart_id)
        )
        await self.session.execute(
            delete(InterpretivePriority).where(InterpretivePriority.chart_id == chart_id)
        )
        await self.session.execute(
            delete(InterpretiveMatch).where(InterpretiveMatch.chart_id == chart_id)
        )
        await self.session.flush()
