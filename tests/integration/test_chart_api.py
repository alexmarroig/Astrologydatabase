from __future__ import annotations

import pytest

from app.core.enums import InterpretiveTheme, RuleStatus, RuleType, SubjectType
from app.models.editorial import InterpretationBlock, InterpretationRule


@pytest.mark.asyncio
async def test_create_and_fetch_natal_chart_snapshot(client, seeded_catalog):
    payload = {
        "name": "Mapa de Teste",
        "birth_date_local": "1990-01-15",
        "birth_time_local": "08:30:00",
        "timezone_offset_minutes": -180,
        "location_name": "Sao Paulo, BR",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "house_system": "placidus",
        "metadata": {"source": "integration-test"},
    }

    response = await client.post("/api/v1/charts/natal", json=payload)
    assert response.status_code == 201

    chart = response.json()
    assert chart["chart_type"] == "natal"
    assert chart["provider"] == "analytical"
    assert chart["location_name"] == "Sao Paulo, BR"
    assert len(chart["positions"]) == 7
    assert len(chart["house_cusps"]) == 12
    assert len(chart["angles"]) == 4

    get_response = await client.get(f"/api/v1/charts/{chart['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == chart["id"]
    assert {item["body_code"] for item in fetched["positions"]} == {
        "SUN",
        "MOON",
        "MERCURY",
        "VENUS",
        "MARS",
        "JUPITER",
        "SATURN",
    }


@pytest.mark.asyncio
async def test_list_calculated_chart_factors(client, seeded_catalog):
    payload = {
        "birth_date_local": "1988-09-01",
        "birth_time_local": "14:45:00",
        "timezone_offset_minutes": 0,
        "location_name": "Lisbon, PT",
        "latitude": 38.7223,
        "longitude": -9.1393,
    }

    create_response = await client.post("/api/v1/charts/natal", json=payload)
    assert create_response.status_code == 201
    chart_id = create_response.json()["id"]

    factors_response = await client.get(f"/api/v1/charts/{chart_id}/factors")
    assert factors_response.status_code == 200
    factors = factors_response.json()

    assert factors["chart_id"] == chart_id
    assert len(factors["positions"]) == 7
    assert len(factors["house_cusps"]) == 12
    assert len(factors["angles"]) == 4
    assert isinstance(factors["rulerships"], dict)
    assert "SUN" in factors["rulerships"]
    assert all(1 <= item["house_number"] <= 12 for item in factors["house_cusps"])


@pytest.mark.asyncio
async def test_calculate_and_fetch_interpretive_priority_snapshot(
    client,
    db_session,
    seeded_catalog,
):
    payload = {
        "birth_date_local": "1992-06-20",
        "birth_time_local": "06:15:00",
        "timezone_offset_minutes": -180,
        "location_name": "Rio de Janeiro, BR",
        "latitude": -22.9068,
        "longitude": -43.1729,
    }

    create_response = await client.post("/api/v1/charts/natal", json=payload)
    assert create_response.status_code == 201
    chart = create_response.json()

    matching_position = chart["positions"][0]
    school = seeded_catalog["default_school"]
    rule = InterpretationRule(
        canonical_code=(
            f"{matching_position['body_code']}__PLANET_IN_SIGN__{matching_position['sign_code']}"
        ),
        rule_type=RuleType.PLANET_IN_SIGN.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id=matching_position["body_code"],
        subject_b_type=SubjectType.SIGN.value,
        subject_b_id=matching_position["sign_code"],
        school_id=school.id,
        interpretive_weight=5.0,
        status=RuleStatus.PUBLISHED.value,
        version=1,
        blocks=[
            InterpretationBlock(
                theme=InterpretiveTheme.IDENTITY.value,
                potency_central="Snapshot API test",
                interpretive_weight=5.0,
                editorial_confidence=0.9,
            )
        ],
    )
    db_session.add(rule)
    await db_session.flush()

    priority_response = await client.post(
        f"/api/v1/charts/{chart['id']}/interpretive-priority"
    )
    assert priority_response.status_code == 201
    snapshot = priority_response.json()

    assert snapshot["chart_id"] == chart["id"]
    assert snapshot["school_code"] == "luz_e_sombra"
    assert len(snapshot["matches"]) == 1
    assert snapshot["priorities"][0]["rule"]["canonical_code"] == rule.canonical_code

    get_response = await client.get(f"/api/v1/charts/{chart['id']}/interpretive-priority")
    assert get_response.status_code == 200
    assert get_response.json()["priorities"][0]["rule"]["canonical_code"] == rule.canonical_code
