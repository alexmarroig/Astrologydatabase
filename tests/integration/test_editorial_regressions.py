from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.editorial import School


@pytest.mark.asyncio
async def test_db_session_starts_empty_and_survives_commit(db_session, school_payload):
    initial_count = await db_session.scalar(select(func.count()).select_from(School))
    assert initial_count == 0

    school = School(**school_payload)
    db_session.add(school)

    await db_session.commit()

    persisted_count = await db_session.scalar(select(func.count()).select_from(School))
    assert persisted_count == 1


@pytest.mark.asyncio
async def test_create_school_uses_valid_fixture_code_and_isolation(client, db_session, school_payload):
    initial_count = await db_session.scalar(select(func.count()).select_from(School))
    assert initial_count == 0

    response = await client.post("/api/v1/editorial/schools", json=school_payload)

    assert response.status_code == 201
    assert response.json()["code"] == school_payload["code"]
