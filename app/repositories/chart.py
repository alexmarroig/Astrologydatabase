"""Repositories for natal chart snapshots and factor retrieval."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chart import Chart
from app.repositories.base import BaseRepository


class ChartRepository(BaseRepository[Chart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Chart, session)

    async def get_by_id_full(self, id: uuid.UUID) -> Chart | None:
        stmt = (
            select(Chart)
            .options(
                selectinload(Chart.positions),
                selectinload(Chart.aspects),
                selectinload(Chart.angles),
                selectinload(Chart.house_cusps),
            )
            .where(Chart.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
