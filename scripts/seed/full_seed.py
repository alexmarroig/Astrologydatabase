from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.enums import RuleStatus, RuleType, SubjectType
from app.models.editorial import InterpretationBlock, InterpretationRule, School
from scripts.seed.contracts import validate_planet_in_sign_dataset
from scripts.seed.minimal_seed import seed_minimal_data
from data.hellenistic.planet_in_sign import PLANET_IN_SIGN_BATCH


SYSTEM_TO_SCHOOL_CODE = {
    "hellenistic": "hellenistic",
}
PLANET_CODE_MAP = {
    "sun": "SUN",
    "moon": "MOON",
    "mercury": "MERCURY",
    "venus": "VENUS",
    "mars": "MARS",
    "jupiter": "JUPITER",
    "saturn": "SATURN",
}
SIGN_CODE_MAP = {
    "aries": "ARIES",
    "taurus": "TAURUS",
    "gemini": "GEMINI",
    "cancer": "CANCER",
    "leo": "LEO",
    "virgo": "VIRGO",
    "libra": "LIBRA",
    "scorpio": "SCORPIO",
    "sagittarius": "SAGITTARIUS",
    "capricorn": "CAPRICORN",
    "aquarius": "AQUARIUS",
    "pisces": "PISCES",
}


def _upsert_by_field(session: Session, model, field_name: str, payload: dict):
    field = getattr(model, field_name)
    instance = session.scalar(select(model).where(field == payload[field_name]))
    if instance is None:
        instance = model(**payload)
        session.add(instance)
        session.flush()
        return instance

    for key, value in payload.items():
        setattr(instance, key, value)
    session.flush()
    return instance


def _resolve_school(session: Session, system_code: str) -> School:
    school_code = SYSTEM_TO_SCHOOL_CODE.get(system_code)
    if school_code is None:
        raise ValueError(f"Unsupported system mapping: {system_code}")

    school = session.scalar(select(School).where(School.code == school_code))
    if school is None:
        school = _upsert_by_field(
            session,
            School,
            "code",
            {
                "code": school_code,
                "name_pt": "Astrologia Helenistica",
                "name_en": "Hellenistic Astrology",
                "description": "Sistema editorial tecnico para interpretacoes modulares em astrologia helenistica.",
                "primary_authors": ["Valens", "Dorotheus", "Rhetorius"],
                "origin_country": "EG",
                "origin_decade": 100,
                "is_active": True,
            },
        )
    return school


def _subject_type_to_db(value: str) -> str:
    mapping = {
        "planet": SubjectType.BODY.value,
        "sign": SubjectType.SIGN.value,
    }
    return mapping[value]


def _to_db_rule_payload(seed_rule: dict[str, Any], school_id) -> dict[str, Any]:
    return {
        "canonical_code": seed_rule["canonical_code"],
        "rule_type": RuleType.PLANET_IN_SIGN.value,
        "subject_a_type": _subject_type_to_db(seed_rule["subject_1_type"]),
        "subject_a_id": PLANET_CODE_MAP[seed_rule["subject_1_id"]],
        "subject_b_type": _subject_type_to_db(seed_rule["subject_2_type"]),
        "subject_b_id": SIGN_CODE_MAP[seed_rule["subject_2_id"]],
        "school_id": school_id,
        "interpretive_weight": round(float(seed_rule["base_weight"]) * 10, 4),
        "status": RuleStatus.PUBLISHED.value if seed_rule["status"] == "validated" else RuleStatus.DRAFT.value,
        "version": seed_rule["version"],
        "metadata_json": {
            "engine_contract": {
                "subject_1_type": seed_rule["subject_1_type"],
                "subject_1_id": seed_rule["subject_1_id"],
                "subject_2_type": seed_rule["subject_2_type"],
                "subject_2_id": seed_rule["subject_2_id"],
                "system": seed_rule["system"],
            }
        },
    }


def _to_db_block_payload(seed_block: dict[str, Any]) -> dict[str, Any]:
    return {
        "theme": seed_block["theme"],
        "potency_central": seed_block["core_statement"],
        "well_expressed": seed_block["manifestation"],
        "poorly_expressed": seed_block["risk_expression"],
        "keywords_json": [],
        "interpretive_weight": round(float(seed_block["interpretive_weight"]) * 10, 4),
        "editorial_confidence": 1.0,
        "editorial_notes": None,
    }


def seed_planet_in_sign_batch(session: Session, dataset: list[dict[str, Any]]) -> None:
    validate_planet_in_sign_dataset(dataset)

    for item in dataset:
        seed_rule = item["interpretation_rule"]
        seed_block = item["interpretation_block"]
        school = _resolve_school(session, seed_rule["system"])
        db_rule_payload = _to_db_rule_payload(seed_rule, school.id)
        db_block_payload = _to_db_block_payload(seed_block)

        rule = session.scalar(
            select(InterpretationRule).where(
                InterpretationRule.canonical_code == db_rule_payload["canonical_code"],
                InterpretationRule.school_id == school.id,
            )
        )
        if rule is None:
            rule = InterpretationRule(**db_rule_payload)
            session.add(rule)
            session.flush()
        else:
            for key, value in db_rule_payload.items():
                setattr(rule, key, value)
            session.flush()

        block = session.scalar(
            select(InterpretationBlock).where(
                InterpretationBlock.rule_id == rule.id,
                InterpretationBlock.theme == db_block_payload["theme"],
            )
        )
        engine_block = {
            "core_statement": seed_block["core_statement"],
            "manifestation": seed_block["manifestation"],
            "risk_expression": seed_block["risk_expression"],
            "modifiers_json": seed_block["modifiers_json"],
            "priority": seed_block["priority"],
        }
        metadata_json = {
            "engine_block": {
                **engine_block,
            }
        }
        if block is None:
            block = InterpretationBlock(
                rule_id=rule.id,
                **db_block_payload,
            )
            session.add(block)
        else:
            for key, value in db_block_payload.items():
                setattr(block, key, value)
        block.editorial_notes = str(engine_block)
        session.flush()

    session.commit()


async def seed_planet_in_sign_batch_async(session: AsyncSession, dataset: list[dict[str, Any]]) -> None:
    validate_planet_in_sign_dataset(dataset)

    for item in dataset:
        seed_rule = item["interpretation_rule"]
        seed_block = item["interpretation_block"]

        school_code = SYSTEM_TO_SCHOOL_CODE[seed_rule["system"]]
        school = await session.scalar(select(School).where(School.code == school_code))
        if school is None:
            school = School(
                code=school_code,
                name_pt="Astrologia Helenistica",
                name_en="Hellenistic Astrology",
                description="Sistema editorial tecnico para interpretacoes modulares em astrologia helenistica.",
                primary_authors=["Valens", "Dorotheus", "Rhetorius"],
                origin_country="EG",
                origin_decade=100,
                is_active=True,
            )
            session.add(school)
            await session.flush()

        db_rule_payload = _to_db_rule_payload(seed_rule, school.id)
        db_block_payload = _to_db_block_payload(seed_block)

        rule = await session.scalar(
            select(InterpretationRule).where(
                InterpretationRule.canonical_code == db_rule_payload["canonical_code"],
                InterpretationRule.school_id == school.id,
            )
        )
        if rule is None:
            rule = InterpretationRule(**db_rule_payload)
            session.add(rule)
            await session.flush()
        else:
            for key, value in db_rule_payload.items():
                setattr(rule, key, value)
            await session.flush()

        block = await session.scalar(
            select(InterpretationBlock).where(
                InterpretationBlock.rule_id == rule.id,
                InterpretationBlock.theme == db_block_payload["theme"],
            )
        )
        engine_block = {
            "core_statement": seed_block["core_statement"],
            "manifestation": seed_block["manifestation"],
            "risk_expression": seed_block["risk_expression"],
            "modifiers_json": seed_block["modifiers_json"],
            "priority": seed_block["priority"],
        }
        if block is None:
            block = InterpretationBlock(
                rule_id=rule.id,
                **db_block_payload,
            )
            session.add(block)
        else:
            for key, value in db_block_payload.items():
                setattr(block, key, value)
        block.editorial_notes = str(engine_block)
        await session.flush()

    await session.commit()


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)

    with Session(engine) as session:
        seed_minimal_data(session)
        seed_planet_in_sign_batch(session, PLANET_IN_SIGN_BATCH)

    print(f"Full seed completed with {len(PLANET_IN_SIGN_BATCH)} planet_in_sign rules.")


if __name__ == "__main__":
    main()
