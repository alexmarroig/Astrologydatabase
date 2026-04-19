from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.enums import RuleStatus, RuleType, SubjectType
from app.models.editorial import InterpretationBlock, InterpretationRule, School
from scripts.seed.contracts import (
    validate_planet_in_sign_dataset,
    validate_planet_in_house_dataset,
    validate_aspects_dataset,
    validate_ruler_in_house_dataset,
)
from scripts.seed.minimal_seed import seed_minimal_data

# Import datasets
try:
    from data.luz_e_sombra.planet_in_sign import PLANET_IN_SIGN_LUZ_SOMBRA
    from data.luz_e_sombra.planet_in_house import PLANET_IN_HOUSE_LUZ_SOMBRA
    from data.luz_e_sombra.aspects import ASPECTS_LUZ_SOMBRA
    from data.luz_e_sombra.ruler_in_house import RULER_IN_HOUSE_LUZ_SOMBRA
    from data.hellenistic.planet_in_sign import PLANET_IN_SIGN_BATCH as PLANET_IN_SIGN_HELLENISTIC
except ImportError:
    PLANET_IN_SIGN_LUZ_SOMBRA = []
    PLANET_IN_HOUSE_LUZ_SOMBRA = []
    ASPECTS_LUZ_SOMBRA = []
    RULER_IN_HOUSE_LUZ_SOMBRA = []
    PLANET_IN_SIGN_HELLENISTIC = []

PLANET_CODE_MAP = {
    "sun": "SUN", "moon": "MOON", "mercury": "MERCURY", "venus": "VENUS",
    "mars": "MARS", "jupiter": "JUPITER", "saturn": "SATURN",
    "uranus": "URANUS", "neptune": "NEPTUNE", "pluto": "PLUTO",
    "chiron": "CHIRON", "north_node": "NORTH_NODE", "south_node": "SOUTH_NODE",
}

SIGN_CODE_MAP = {
    "aries": "ARIES", "taurus": "TAURUS", "gemini": "GEMINI", "cancer": "CANCER",
    "leo": "LEO", "virgo": "VIRGO", "libra": "LIBRA", "scorpio": "SCORPIO",
    "sagittarius": "SAGITTARIUS", "capricorn": "CAPRICORN", "aquarius": "AQUARIUS",
    "pisces": "PISCES",
}

ASPECT_CODE_MAP = {
    "conjunction": "CONJUNCTION", "sextile": "SEXTILE", "square": "SQUARE",
    "trine": "TRINE", "opposition": "OPPOSITION",
}

def _resolve_school(session: Session, school_code: str) -> School:
    school = session.scalar(select(School).where(School.code == school_code))
    if school is None:
        # Auto-create if not exists (fallback)
        school = School(
            code=school_code,
            name_pt=school_code.replace("_", " ").title(),
            name_en=school_code.replace("_", " ").title(),
            is_active=True
        )
        session.add(school)
        session.flush()
    return school

def _subject_type_to_db(value: str) -> str:
    mapping = {
        "planet": SubjectType.BODY.value,
        "sign": SubjectType.SIGN.value,
        "house": SubjectType.HOUSE.value,
        "aspect": SubjectType.ASPECT.value,
    }
    return mapping.get(value, SubjectType.NONE.value)

def _resolve_subject_id(subject_type: str, subject_id: str) -> str:
    if not subject_id: return None
    if subject_type == "planet":
        return PLANET_CODE_MAP.get(subject_id.lower(), subject_id.upper())
    if subject_type == "sign":
        return SIGN_CODE_MAP.get(subject_id.lower(), subject_id.upper())
    if subject_type == "aspect":
        return ASPECT_CODE_MAP.get(subject_id.lower(), subject_id.upper())
    return str(subject_id) # For house numbers

def _seed_batch(session: Session, dataset: list[dict[str, Any]], validator_func) -> None:
    if not dataset:
        return

    validator_func(dataset)

    for item in dataset:
        seed_rule = item["interpretation_rule"]
        seed_block = item["interpretation_block"]
        school = _resolve_school(session, seed_rule["system"])

        db_rule_payload = {
            "canonical_code": seed_rule["canonical_code"],
            "rule_type": seed_rule["rule_type"],
            "subject_a_type": _subject_type_to_db(seed_rule.get("subject_1_type")),
            "subject_a_id": _resolve_subject_id(seed_rule.get("subject_1_type"), seed_rule.get("subject_1_id")),
            "subject_b_type": _subject_type_to_db(seed_rule.get("subject_2_type")),
            "subject_b_id": _resolve_subject_id(seed_rule.get("subject_2_type"), seed_rule.get("subject_2_id")),
            "subject_c_type": _subject_type_to_db(seed_rule.get("subject_3_type")) if "subject_3_type" in seed_rule else None,
            "subject_c_id": _resolve_subject_id(seed_rule.get("subject_3_type"), seed_rule.get("subject_3_id")) if "subject_3_id" in seed_rule else None,
            "school_id": school.id,
            "interpretive_weight": seed_rule.get("base_weight", 0.5) * 10,
            "status": RuleStatus.PUBLISHED.value,
            "version": seed_rule.get("version", 1),
        }

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

        db_block_payload = {
            "theme": seed_block["theme"],
            "potency_central": seed_block.get("core_statement") or seed_block.get("potency_central"),
            "well_expressed": seed_block.get("manifestation") or seed_block.get("well_expressed"),
            "poorly_expressed": seed_block.get("risk_expression") or seed_block.get("poorly_expressed"),
            "complementary_axis": seed_block.get("complementary_axis"),
            "integration_path": seed_block.get("integration_path"),
            "keywords_json": seed_block.get("keywords_json", []),
            "interpretive_weight": seed_block.get("interpretive_weight", 0.5) * 10,
            "editorial_confidence": 1.0,
        }

        block = session.scalar(
            select(InterpretationBlock).where(
                InterpretationBlock.rule_id == rule.id,
                InterpretationBlock.theme == db_block_payload["theme"],
            )
        )
        if block is None:
            block = InterpretationBlock(rule_id=rule.id, **db_block_payload)
            session.add(block)
        else:
            for key, value in db_block_payload.items():
                setattr(block, key, value)
        session.flush()

    session.commit()

def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)

    with Session(engine) as session:
        print("Seeding minimal reference data...")
        seed_minimal_data(session)

        print("Seeding Luz e Sombra: Planet in Sign...")
        _seed_batch(session, PLANET_IN_SIGN_LUZ_SOMBRA, validate_planet_in_sign_dataset)

        print("Seeding Luz e Sombra: Planet in House...")
        _seed_batch(session, PLANET_IN_HOUSE_LUZ_SOMBRA, validate_planet_in_house_dataset)

        print("Seeding Luz e Sombra: Aspects...")
        _seed_batch(session, ASPECTS_LUZ_SOMBRA, validate_aspects_dataset)

        print("Seeding Luz e Sombra: Ruler in House...")
        _seed_batch(session, RULER_IN_HOUSE_LUZ_SOMBRA, validate_ruler_in_house_dataset)

        print("Seeding Hellenistic: Planet in Sign...")
        _seed_batch(session, PLANET_IN_SIGN_HELLENISTIC, validate_planet_in_sign_dataset)

    print("Full seed completed successfully.")

if __name__ == "__main__":
    main()
