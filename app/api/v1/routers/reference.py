"""
Read-only API endpoints for astrological reference data.

These endpoints serve the static ontological vocabulary:
signs, bodies, houses, aspects, angles.

Reference data is managed via seed scripts and migrations.
The API exposes it for client consumption and documentation.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.base import get_db
from app.repositories.astro_reference import (
    AngleRepository,
    AspectRepository,
    BodyRepository,
    HouseRepository,
    SignRepository,
)
from app.schemas.astro_reference import (
    AngleList,
    AngleRead,
    AspectList,
    AspectRead,
    BodyList,
    BodyRead,
    HouseList,
    HouseRead,
    SignList,
    SignRead,
)

router = APIRouter(tags=["Reference Data"])


# ── Signs ─────────────────────────────────────────────────────────────────────

@router.get(
    "/signs",
    response_model=list[SignList],
    summary="List all zodiac signs",
    description="Returns the 12 zodiac signs ordered by ecliptic position (Aries → Pisces).",
)
async def list_signs(
    db: Annotated[AsyncSession, Depends(get_db)],
    element: str | None = Query(None, description="Filter by element: fire, earth, air, water"),
) -> list[SignList]:
    repo = SignRepository(db)
    if element:
        signs = await repo.get_by_element(element)
    else:
        signs = await repo.get_all_ordered()
    return [SignList.model_validate(s) for s in signs]


@router.get(
    "/signs/{sign_id}",
    response_model=SignRead,
    summary="Get sign by ID",
)
async def get_sign(
    sign_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SignRead:
    repo = SignRepository(db)
    sign = await repo.get_by_id(sign_id)
    if not sign:
        raise HTTPException(status_code=404, detail=f"Sign {sign_id} not found")
    return SignRead.model_validate(sign)


@router.get(
    "/signs/code/{code}",
    response_model=SignRead,
    summary="Get sign by canonical code",
    description="Example: GET /signs/code/SCORPIO",
)
async def get_sign_by_code(
    code: Annotated[str, Path(description="Sign code, e.g. SCORPIO, ARIES")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SignRead:
    repo = SignRepository(db)
    sign = await repo.get_by_code(code.upper())
    if not sign:
        raise HTTPException(status_code=404, detail=f"Sign '{code}' not found")
    return SignRead.model_validate(sign)


# ── Bodies ────────────────────────────────────────────────────────────────────

@router.get(
    "/bodies",
    response_model=list[BodyList],
    summary="List celestial bodies",
    description="Returns planets, nodes, asteroids, and other astrological bodies.",
)
async def list_bodies(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(
        None,
        description="Filter by category: personal, social, transpersonal, node, asteroid, angle",
    ),
    personal_only: bool = Query(False, description="Return only personal bodies (Sun-Mars)"),
) -> list[BodyList]:
    repo = BodyRepository(db)
    if personal_only:
        bodies = await repo.get_personal_bodies()
    elif category:
        bodies = await repo.get_by_category(category)
    else:
        bodies = list(await repo.get_all())
    return [BodyList.model_validate(b) for b in bodies]


@router.get(
    "/bodies/{body_id}",
    response_model=BodyRead,
    summary="Get body by ID",
)
async def get_body(
    body_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BodyRead:
    repo = BodyRepository(db)
    body = await repo.get_by_id(body_id)
    if not body:
        raise HTTPException(status_code=404, detail=f"Body {body_id} not found")
    return BodyRead.model_validate(body)


@router.get(
    "/bodies/code/{code}",
    response_model=BodyRead,
    summary="Get body by canonical code",
    description="Example: GET /bodies/code/SUN",
)
async def get_body_by_code(
    code: Annotated[str, Path(description="Body code, e.g. SUN, MOON, SATURN")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BodyRead:
    repo = BodyRepository(db)
    body = await repo.get_by_code(code.upper())
    if not body:
        raise HTTPException(status_code=404, detail=f"Body '{code}' not found")
    return BodyRead.model_validate(body)


# ── Houses ────────────────────────────────────────────────────────────────────

@router.get(
    "/houses",
    response_model=list[HouseList],
    summary="List the 12 astrological houses",
)
async def list_houses(
    db: Annotated[AsyncSession, Depends(get_db)],
    position_type: str | None = Query(
        None, description="Filter by: angular, succedent, cadent"
    ),
) -> list[HouseList]:
    repo = HouseRepository(db)
    if position_type == "angular":
        houses = await repo.get_angular_houses()
    else:
        houses = await repo.get_all_ordered()
    return [HouseList.model_validate(h) for h in houses]


@router.get(
    "/houses/{house_id}",
    response_model=HouseRead,
    summary="Get house by ID",
)
async def get_house(
    house_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HouseRead:
    repo = HouseRepository(db)
    house = await repo.get_by_id(house_id)
    if not house:
        raise HTTPException(status_code=404, detail=f"House {house_id} not found")
    return HouseRead.model_validate(house)


@router.get(
    "/houses/number/{number}",
    response_model=HouseRead,
    summary="Get house by number (1-12)",
)
async def get_house_by_number(
    number: Annotated[int, Path(ge=1, le=12)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HouseRead:
    repo = HouseRepository(db)
    house = await repo.get_by_number(number)
    if not house:
        raise HTTPException(status_code=404, detail=f"House {number} not found")
    return HouseRead.model_validate(house)


# ── Aspects ───────────────────────────────────────────────────────────────────

@router.get(
    "/aspects",
    response_model=list[AspectList],
    summary="List astrological aspects",
)
async def list_aspects(
    db: Annotated[AsyncSession, Depends(get_db)],
    quality: str | None = Query(None, description="Filter by: major, minor, special"),
    nature: str | None = Query(None, description="Filter by: harmonic, tense, neutral, mixed"),
) -> list[AspectList]:
    repo = AspectRepository(db)
    if quality == "major":
        aspects = await repo.get_major_aspects()
    else:
        aspects = list(await repo.get_all())
    if nature:
        aspects = [a for a in aspects if a.nature == nature.lower()]
    return [AspectList.model_validate(a) for a in aspects]


@router.get(
    "/aspects/{aspect_id}",
    response_model=AspectRead,
    summary="Get aspect by ID",
)
async def get_aspect(
    aspect_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AspectRead:
    repo = AspectRepository(db)
    aspect = await repo.get_by_id(aspect_id)
    if not aspect:
        raise HTTPException(status_code=404, detail=f"Aspect {aspect_id} not found")
    return AspectRead.model_validate(aspect)


# ── Angles ────────────────────────────────────────────────────────────────────

@router.get(
    "/angles",
    response_model=list[AngleList],
    summary="List chart angles (ASC, MC, DSC, IC)",
)
async def list_angles(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AngleList]:
    repo = AngleRepository(db)
    angles = await repo.get_all_ordered()
    return [AngleList.model_validate(a) for a in angles]


@router.get(
    "/angles/{angle_id}",
    response_model=AngleRead,
    summary="Get angle by ID",
)
async def get_angle(
    angle_id: Annotated[uuid.UUID, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AngleRead:
    repo = AngleRepository(db)
    angle = await repo.get_by_id(angle_id)
    if not angle:
        raise HTTPException(status_code=404, detail=f"Angle {angle_id} not found")
    return AngleRead.model_validate(angle)
