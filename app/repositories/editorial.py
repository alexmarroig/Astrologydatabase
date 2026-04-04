"""
Repositories for the editorial domain.

These handle the writable editorial entities:
  - School, Source, InterpretationRule, InterpretationBlock
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.editorial import (
    InterpretationBlock,
    InterpretationRule,
    School,
    Source,
)
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(School, session)

    async def get_by_code(self, code: str) -> School | None:
        stmt = select(School).where(School.code == code.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self) -> list[School]:
        stmt = select(School).where(School.is_active == True).order_by(School.code)  # noqa: E712
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def code_exists(self, code: str) -> bool:
        stmt = select(School.id).where(School.code == code.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class SourceRepository(BaseRepository[Source]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Source, session)

    async def get_by_id_with_school(self, id: uuid.UUID) -> Source | None:
        stmt = (
            select(Source)
            .options(joinedload(Source.school))
            .where(Source.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_school(
        self, *, offset: int = 0, limit: int = 100, active_only: bool = True
    ) -> list[Source]:
        stmt = select(Source).options(joinedload(Source.school))
        if active_only:
            stmt = stmt.where(Source.is_active == True)  # noqa: E712
        stmt = stmt.order_by(Source.author, Source.title).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_school(self, school_id: uuid.UUID) -> list[Source]:
        stmt = (
            select(Source)
            .options(joinedload(Source.school))
            .where(Source.school_id == school_id, Source.is_active == True)  # noqa: E712
            .order_by(Source.author)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def isbn_exists(self, isbn: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Source.id).where(Source.isbn == isbn)
        if exclude_id:
            stmt = stmt.where(Source.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class InterpretationRuleRepository(BaseRepository[InterpretationRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InterpretationRule, session)

    async def get_by_id_full(self, id: uuid.UUID) -> InterpretationRule | None:
        """Fetch rule with all relations loaded (blocks, school, source)."""
        stmt = (
            select(InterpretationRule)
            .options(
                joinedload(InterpretationRule.school),
                joinedload(InterpretationRule.source),
                selectinload(InterpretationRule.blocks),
            )
            .where(InterpretationRule.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_canonical_code(
        self, canonical_code: str, school_id: uuid.UUID
    ) -> InterpretationRule | None:
        """Primary lookup used by the synthesis engine."""
        stmt = select(InterpretationRule).where(
            and_(
                InterpretationRule.canonical_code == canonical_code,
                InterpretationRule.school_id == school_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_published_by_code(
        self, canonical_code: str, school_id: uuid.UUID
    ) -> InterpretationRule | None:
        """Fetch only published rules — used by synthesis engine."""
        stmt = (
            select(InterpretationRule)
            .options(
                selectinload(InterpretationRule.blocks),
                joinedload(InterpretationRule.school),
            )
            .where(
                and_(
                    InterpretationRule.canonical_code == canonical_code,
                    InterpretationRule.school_id == school_id,
                    InterpretationRule.status == "published",
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_published_for_school(
        self,
        school_id: uuid.UUID,
        *,
        rule_types: Sequence[str] | None = None,
    ) -> list[InterpretationRule]:
        stmt = (
            select(InterpretationRule)
            .options(
                joinedload(InterpretationRule.school),
                joinedload(InterpretationRule.source),
                selectinload(InterpretationRule.blocks),
            )
            .where(
                and_(
                    InterpretationRule.school_id == school_id,
                    InterpretationRule.status == "published",
                )
            )
        )
        if rule_types:
            stmt = stmt.where(InterpretationRule.rule_type.in_(rule_types))
        stmt = stmt.order_by(InterpretationRule.canonical_code)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_status(
        self,
        status: str,
        school_id: uuid.UUID | None = None,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[InterpretationRule]:
        stmt = (
            select(InterpretationRule)
            .options(
                joinedload(InterpretationRule.school),
                joinedload(InterpretationRule.source),
            )
            .where(InterpretationRule.status == status)
        )
        if school_id:
            stmt = stmt.where(InterpretationRule.school_id == school_id)
        stmt = stmt.order_by(InterpretationRule.canonical_code).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_rule_type(
        self, rule_type: str, *, offset: int = 0, limit: int = 100
    ) -> list[InterpretationRule]:
        stmt = (
            select(InterpretationRule)
            .options(joinedload(InterpretationRule.school))
            .where(InterpretationRule.rule_type == rule_type)
            .order_by(InterpretationRule.canonical_code)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def canonical_code_exists(
        self,
        canonical_code: str,
        school_id: uuid.UUID,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = select(InterpretationRule.id).where(
            and_(
                InterpretationRule.canonical_code == canonical_code,
                InterpretationRule.school_id == school_id,
            )
        )
        if exclude_id:
            stmt = stmt.where(InterpretationRule.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_all_paginated(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        school_id: uuid.UUID | None = None,
        status: str | None = None,
        rule_type: str | None = None,
    ) -> list[InterpretationRule]:
        stmt = (
            select(InterpretationRule)
            .options(
                joinedload(InterpretationRule.school),
                joinedload(InterpretationRule.source),
            )
        )
        if school_id:
            stmt = stmt.where(InterpretationRule.school_id == school_id)
        if status:
            stmt = stmt.where(InterpretationRule.status == status)
        if rule_type:
            stmt = stmt.where(InterpretationRule.rule_type == rule_type)
        stmt = stmt.order_by(InterpretationRule.canonical_code).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())


class InterpretationBlockRepository(BaseRepository[InterpretationBlock]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InterpretationBlock, session)

    async def get_by_rule(self, rule_id: uuid.UUID) -> list[InterpretationBlock]:
        stmt = (
            select(InterpretationBlock)
            .where(InterpretationBlock.rule_id == rule_id)
            .order_by(InterpretationBlock.theme)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_rule_and_theme(
        self, rule_id: uuid.UUID, theme: str
    ) -> InterpretationBlock | None:
        stmt = select(InterpretationBlock).where(
            and_(
                InterpretationBlock.rule_id == rule_id,
                InterpretationBlock.theme == theme,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_theme(
        self, theme: str, *, offset: int = 0, limit: int = 100
    ) -> list[InterpretationBlock]:
        stmt = (
            select(InterpretationBlock)
            .where(InterpretationBlock.theme == theme)
            .order_by(InterpretationBlock.interpretive_weight.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
