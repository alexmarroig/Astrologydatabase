"""
Generic async CRUD repository.

Provides a typed base class with standard database operations.
Domain-specific repositories extend this and add custom queries.

Design rationale:
  - Keeps SQL out of routers and services
  - Single place to change query patterns (pagination, soft-delete, etc.)
  - Type-safe via generics
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository for SQLAlchemy ORM models."""

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelT | None:
        result = await self.session.get(self.model, id)
        return result

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> Sequence[ModelT]:
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()  # Get ID without committing
        await self.session.refresh(obj)
        return obj

    async def update_fields(self, id: uuid.UUID, data: dict[str, Any]) -> ModelT | None:
        obj = await self.get_by_id(id)
        if obj is None:
            return None
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: uuid.UUID) -> bool:
        obj = await self.get_by_id(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def exists(self, id: uuid.UUID) -> bool:
        result = await self.session.get(self.model, id)
        return result is not None
