"""
Repositories for astrological reference data.

These repositories are mostly read-only from the API perspective.
Writes happen via seed scripts and migrations.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.astro_reference import Angle, Aspect, Body, House, Sign
from app.repositories.base import BaseRepository


class SignRepository(BaseRepository[Sign]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Sign, session)

    async def get_by_code(self, code: str) -> Sign | None:
        stmt = select(Sign).where(Sign.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_ordered(self) -> list[Sign]:
        stmt = select(Sign).order_by(Sign.order_num)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_element(self, element: str) -> list[Sign]:
        stmt = select(Sign).where(Sign.element == element.lower()).order_by(Sign.order_num)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class BodyRepository(BaseRepository[Body]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Body, session)

    async def get_by_code(self, code: str) -> Body | None:
        stmt = select(Body).where(Body.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[Body]:
        stmt = select(Body).where(Body.category == category.lower())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_personal_bodies(self) -> list[Body]:
        stmt = select(Body).where(Body.is_personal == True).order_by(Body.code)  # noqa: E712
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class HouseRepository(BaseRepository[House]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(House, session)

    async def get_by_number(self, number: int) -> House | None:
        stmt = select(House).where(House.number == number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_ordered(self) -> list[House]:
        stmt = select(House).order_by(House.number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_angular_houses(self) -> list[House]:
        stmt = select(House).where(House.position_type == "angular").order_by(House.number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AspectRepository(BaseRepository[Aspect]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Aspect, session)

    async def get_by_code(self, code: str) -> Aspect | None:
        stmt = select(Aspect).where(Aspect.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_major_aspects(self) -> list[Aspect]:
        stmt = select(Aspect).where(Aspect.quality == "major").order_by(Aspect.angle_degrees)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AngleRepository(BaseRepository[Angle]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Angle, session)

    async def get_by_code(self, code: str) -> Angle | None:
        stmt = select(Angle).where(Angle.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_ordered(self) -> list[Angle]:
        stmt = select(Angle).order_by(Angle.code)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
