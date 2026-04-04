from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.domain.bootstrap_data import (
    ANGLES,
    ASPECTS,
    BODIES,
    HOUSES,
    SCHOOLS,
    SIGNS,
    SIGN_OPPOSITES,
)
from app.models.astro_reference import Angle, Aspect, Body, House, Sign
from app.models.editorial import School


@pytest.fixture
def school_payload() -> dict[str, object]:
    return {
        "code": "ls",
        "name_pt": "Luz e Sombra",
        "name_en": "Light and Shadow",
        "description": "Escola base usada nos testes de integracao.",
        "primary_authors": ["Claudia Lisboa"],
        "origin_country": "BR",
        "origin_decade": 1990,
    }


@pytest.fixture
def alternate_school_payload() -> dict[str, object]:
    return {
        "code": "md",
        "name_pt": "Astrologia Moderna",
        "name_en": "Modern Astrology",
        "description": "Payload alternativo para cenarios de teste.",
        "primary_authors": ["Dane Rudhyar"],
        "origin_country": "US",
        "origin_decade": 1930,
    }


async def _upsert_async_by_field(db_session, model, field_name: str, payload: dict):
    field = getattr(model, field_name)
    instance = await db_session.scalar(select(model).where(field == payload[field_name]))
    if instance is None:
        instance = model(**payload)
        db_session.add(instance)
        await db_session.flush()
        return instance

    for key, value in payload.items():
        setattr(instance, key, value)
    await db_session.flush()
    return instance


@pytest_asyncio.fixture
async def seeded_catalog(db_session):
    signs_by_code: dict[str, Sign] = {}
    for payload in SIGNS:
        sign = await _upsert_async_by_field(db_session, Sign, "code", payload)
        signs_by_code[sign.code] = sign

    for code, opposite_code in SIGN_OPPOSITES.items():
        signs_by_code[code].opposite_sign_id = signs_by_code[opposite_code].id
    await db_session.flush()

    for payload in BODIES:
        await _upsert_async_by_field(db_session, Body, "code", payload)

    for payload in HOUSES:
        await _upsert_async_by_field(db_session, House, "number", payload)

    for payload in ASPECTS:
        await _upsert_async_by_field(db_session, Aspect, "code", payload)

    for payload in ANGLES:
        await _upsert_async_by_field(db_session, Angle, "code", payload)

    schools: list[School] = []
    for payload in SCHOOLS:
        school = await _upsert_async_by_field(db_session, School, "code", payload)
        schools.append(school)

    await db_session.flush()
    return {
        "schools": schools,
        "default_school": schools[0],
    }
