from __future__ import annotations

from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy import select

from app.core.enums import InterpretiveTheme, RuleStatus, RuleType, SubjectType
from app.models.astro_reference import Body
from app.models.chart import Chart, ChartAspect, ChartHouseCusp, ChartPosition
from app.models.editorial import InterpretationBlock, InterpretationRule
from app.services.prioritization import InterpretivePrioritizationService


SIGN_SEQUENCE = [
    "ARIES",
    "TAURUS",
    "GEMINI",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "SCORPIO",
    "SAGITTARIUS",
    "CAPRICORN",
    "AQUARIUS",
    "PISCES",
]


async def _body_ids_by_code(db_session) -> dict[str, object]:
    result = await db_session.execute(select(Body))
    return {body.code: body.id for body in result.scalars().all()}


def _house_cusps(start_sign_code: str = "ARIES") -> list[ChartHouseCusp]:
    start_index = SIGN_SEQUENCE.index(start_sign_code)
    cusps: list[ChartHouseCusp] = []
    for house_number in range(1, 13):
        sign_code = SIGN_SEQUENCE[(start_index + house_number - 1) % len(SIGN_SEQUENCE)]
        cusps.append(
            ChartHouseCusp(
                house_number=house_number,
                longitude_deg=float((house_number - 1) * 30),
                sign_code=sign_code,
            )
        )
    return cusps


async def _create_chart(
    db_session,
    *,
    positions: list[dict[str, object]],
    aspects: list[dict[str, object]] | None = None,
    asc_sign_code: str = "ARIES",
) -> Chart:
    body_ids = await _body_ids_by_code(db_session)
    chart = Chart(
        chart_type="natal",
        provider="test-provider",
        house_system="placidus",
        birth_date_local=date(1990, 1, 1),
        birth_time_local=time(12, 0, 0),
        birth_datetime_utc=datetime(1990, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        timezone_offset_minutes=-180,
        location_name="Test City",
        latitude=0.0,
        longitude=0.0,
        positions=[
            ChartPosition(
                body_id=body_ids[item["body_code"]],
                body_code=str(item["body_code"]),
                longitude_deg=float(item.get("longitude_deg", 0.0)),
                latitude_deg=0.0,
                speed_deg_per_day=1.0,
                is_retrograde=False,
                sign_code=str(item["sign_code"]),
                house_number=int(item["house_number"]),
                rulerships_json=list(item.get("rulerships_json", [])),
            )
            for item in positions
        ],
        aspects=[
            ChartAspect(
                body_a_code=str(item["body_a_code"]),
                body_b_code=str(item["body_b_code"]),
                aspect_code=str(item["aspect_code"]),
                exact_angle_deg=float(item.get("exact_angle_deg", 90.0)),
                orb_deg=float(item["orb_deg"]),
                applying=bool(item.get("applying", True)),
            )
            for item in (aspects or [])
        ],
        house_cusps=_house_cusps(asc_sign_code),
    )
    db_session.add(chart)
    await db_session.flush()
    await db_session.refresh(chart)
    return chart


async def _create_rule(
    db_session,
    *,
    school_id,
    canonical_code: str,
    rule_type: str,
    theme: str,
    weight: float = 5.0,
    subject_a_type: str | None = None,
    subject_a_id: str | None = None,
    subject_b_type: str | None = None,
    subject_b_id: str | None = None,
    subject_c_type: str | None = None,
    subject_c_id: str | None = None,
) -> InterpretationRule:
    rule = InterpretationRule(
        canonical_code=canonical_code,
        rule_type=rule_type,
        subject_a_type=subject_a_type,
        subject_a_id=subject_a_id,
        subject_b_type=subject_b_type,
        subject_b_id=subject_b_id,
        subject_c_type=subject_c_type,
        subject_c_id=subject_c_id,
        school_id=school_id,
        interpretive_weight=weight,
        status=RuleStatus.PUBLISHED.value,
        version=1,
        blocks=[
            InterpretationBlock(
                theme=theme,
                potency_central=f"Core meaning for {canonical_code}",
                interpretive_weight=weight,
                editorial_confidence=0.9,
            )
        ],
    )
    db_session.add(rule)
    await db_session.flush()
    return rule


@pytest.mark.asyncio
async def test_prioritization_prefers_angular_positions(db_session, seeded_catalog):
    school = seeded_catalog["default_school"]
    chart = await _create_chart(
        db_session,
        positions=[
            {"body_code": "MERCURY", "sign_code": "ARIES", "house_number": 10},
            {"body_code": "VENUS", "sign_code": "TAURUS", "house_number": 3},
            {"body_code": "MARS", "sign_code": "LIBRA", "house_number": 6, "rulerships_json": [1]},
        ],
    )

    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="MERCURY__PLANET_IN_HOUSE__10",
        rule_type=RuleType.PLANET_IN_HOUSE.value,
        theme=InterpretiveTheme.MENTAL.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="MERCURY",
        subject_b_type=SubjectType.HOUSE.value,
        subject_b_id="10",
    )
    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="VENUS__PLANET_IN_HOUSE__3",
        rule_type=RuleType.PLANET_IN_HOUSE.value,
        theme=InterpretiveTheme.RELATIONAL.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="VENUS",
        subject_b_type=SubjectType.HOUSE.value,
        subject_b_id="3",
    )

    snapshot = await InterpretivePrioritizationService(db_session).calculate_snapshot(chart.id)

    assert [item.rule.canonical_code for item in snapshot.priorities] == [
        "MERCURY__PLANET_IN_HOUSE__10",
        "VENUS__PLANET_IN_HOUSE__3",
    ]
    assert snapshot.priorities[0].total_score > snapshot.priorities[1].total_score


@pytest.mark.asyncio
async def test_prioritization_prefers_exact_aspects(db_session, seeded_catalog):
    school = seeded_catalog["default_school"]
    chart = await _create_chart(
        db_session,
        positions=[
            {"body_code": "SUN", "sign_code": "ARIES", "house_number": 3},
            {"body_code": "MOON", "sign_code": "CANCER", "house_number": 9},
            {"body_code": "MARS", "sign_code": "LEO", "house_number": 6},
            {"body_code": "SATURN", "sign_code": "SCORPIO", "house_number": 12},
        ],
        aspects=[
            {"body_a_code": "SUN", "body_b_code": "MOON", "aspect_code": "SQUARE", "orb_deg": 0.2},
            {"body_a_code": "MARS", "body_b_code": "SATURN", "aspect_code": "SQUARE", "orb_deg": 3.6},
        ],
    )

    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="SUN__ASPECT_PLANET_PLANET__MOON__SQUARE",
        rule_type=RuleType.ASPECT_PLANET_PLANET.value,
        theme=InterpretiveTheme.IDENTITY.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="SUN",
        subject_b_type=SubjectType.BODY.value,
        subject_b_id="MOON",
        subject_c_type=SubjectType.ASPECT.value,
        subject_c_id="SQUARE",
    )
    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="MARS__ASPECT_PLANET_PLANET__SATURN__SQUARE",
        rule_type=RuleType.ASPECT_PLANET_PLANET.value,
        theme=InterpretiveTheme.SHADOW.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="MARS",
        subject_b_type=SubjectType.BODY.value,
        subject_b_id="SATURN",
        subject_c_type=SubjectType.ASPECT.value,
        subject_c_id="SQUARE",
    )

    snapshot = await InterpretivePrioritizationService(db_session).calculate_snapshot(chart.id)

    assert snapshot.priorities[0].rule.canonical_code == "SUN__ASPECT_PLANET_PLANET__MOON__SQUARE"
    assert snapshot.priorities[0].summary_json["factor_key"] == "aspect:SUN:MOON:SQUARE"
    assert snapshot.priorities[0].total_score > snapshot.priorities[1].total_score


@pytest.mark.asyncio
async def test_prioritization_boosts_repeated_themes(db_session, seeded_catalog):
    school = seeded_catalog["default_school"]
    chart = await _create_chart(
        db_session,
        positions=[
            {"body_code": "SUN", "sign_code": "ARIES", "house_number": 2},
            {"body_code": "MOON", "sign_code": "TAURUS", "house_number": 5},
            {"body_code": "VENUS", "sign_code": "LIBRA", "house_number": 8},
            {"body_code": "MARS", "sign_code": "SCORPIO", "house_number": 6, "rulerships_json": [1]},
        ],
    )

    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="SUN__PLANET_IN_SIGN__ARIES",
        rule_type=RuleType.PLANET_IN_SIGN.value,
        theme=InterpretiveTheme.IDENTITY.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="SUN",
        subject_b_type=SubjectType.SIGN.value,
        subject_b_id="ARIES",
    )
    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="MOON__PLANET_IN_HOUSE__5",
        rule_type=RuleType.PLANET_IN_HOUSE.value,
        theme=InterpretiveTheme.IDENTITY.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="MOON",
        subject_b_type=SubjectType.HOUSE.value,
        subject_b_id="5",
    )
    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="VENUS__PLANET_IN_HOUSE__8",
        rule_type=RuleType.PLANET_IN_HOUSE.value,
        theme=InterpretiveTheme.RELATIONAL.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="VENUS",
        subject_b_type=SubjectType.HOUSE.value,
        subject_b_id="8",
    )

    snapshot = await InterpretivePrioritizationService(db_session).calculate_snapshot(chart.id)
    theme_bonus_by_rule = {item.rule.canonical_code: item.thematic_repetition_score for item in snapshot.priorities}

    assert theme_bonus_by_rule["SUN__PLANET_IN_SIGN__ARIES"] > 0
    assert theme_bonus_by_rule["MOON__PLANET_IN_HOUSE__5"] > 0
    assert theme_bonus_by_rule["VENUS__PLANET_IN_HOUSE__8"] == 0
    assert snapshot.priorities[0].rule.canonical_code in {
        "SUN__PLANET_IN_SIGN__ARIES",
        "MOON__PLANET_IN_HOUSE__5",
    }


@pytest.mark.asyncio
async def test_prioritization_boosts_ascendant_ruler(db_session, seeded_catalog):
    school = seeded_catalog["default_school"]
    chart = await _create_chart(
        db_session,
        positions=[
            {"body_code": "MERCURY", "sign_code": "VIRGO", "house_number": 9, "rulerships_json": [1, 4]},
            {"body_code": "VENUS", "sign_code": "LIBRA", "house_number": 9},
        ],
        asc_sign_code="GEMINI",
    )

    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="MERCURY__PLANET_IN_SIGN__VIRGO",
        rule_type=RuleType.PLANET_IN_SIGN.value,
        theme=InterpretiveTheme.MENTAL.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="MERCURY",
        subject_b_type=SubjectType.SIGN.value,
        subject_b_id="VIRGO",
    )
    await _create_rule(
        db_session,
        school_id=school.id,
        canonical_code="VENUS__PLANET_IN_SIGN__LIBRA",
        rule_type=RuleType.PLANET_IN_SIGN.value,
        theme=InterpretiveTheme.RELATIONAL.value,
        subject_a_type=SubjectType.BODY.value,
        subject_a_id="VENUS",
        subject_b_type=SubjectType.SIGN.value,
        subject_b_id="LIBRA",
    )

    snapshot = await InterpretivePrioritizationService(db_session).calculate_snapshot(chart.id)
    score_by_rule = {item.rule.canonical_code: item.total_score for item in snapshot.priorities}

    assert snapshot.priorities[0].rule.canonical_code == "MERCURY__PLANET_IN_SIGN__VIRGO"
    assert score_by_rule["MERCURY__PLANET_IN_SIGN__VIRGO"] > score_by_rule["VENUS__PLANET_IN_SIGN__LIBRA"]
