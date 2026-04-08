from __future__ import annotations

import copy

import pytest
from sqlalchemy import select

from app.models.editorial import InterpretationBlock, InterpretationRule, School
from data.hellenistic.planet_in_sign import PLANET_IN_SIGN_BATCH
from scripts.seed.contracts import SeedContractError, validate_planet_in_sign_dataset
from scripts.seed.full_seed import seed_planet_in_sign_batch_async


def test_validate_planet_in_sign_dataset_accepts_engine_ready_batch():
    validate_planet_in_sign_dataset(PLANET_IN_SIGN_BATCH)


def test_validate_planet_in_sign_dataset_rejects_non_structured_house_condition():
    broken = copy.deepcopy(PLANET_IN_SIGN_BATCH)
    broken[0]["interpretation_block"]["modifiers_json"][0]["condition"]["value"] = "angular"

    with pytest.raises(SeedContractError):
        validate_planet_in_sign_dataset(broken)


@pytest.mark.asyncio
async def test_seed_planet_in_sign_batch_persists_rules_and_blocks(db_session, seeded_catalog):
    await seed_planet_in_sign_batch_async(db_session, PLANET_IN_SIGN_BATCH)

    school = await db_session.scalar(select(School).where(School.code == "hellenistic"))
    assert school is not None

    rules = (await db_session.execute(select(InterpretationRule))).scalars().all()
    blocks = (await db_session.execute(select(InterpretationBlock))).scalars().all()

    seeded_rule_codes = {item["interpretation_rule"]["canonical_code"] for item in PLANET_IN_SIGN_BATCH}
    persisted_rule_codes = {rule.canonical_code for rule in rules if rule.canonical_code in seeded_rule_codes}

    assert len(persisted_rule_codes) == len(PLANET_IN_SIGN_BATCH)
    assert len([block for block in blocks if block.theme == "identity"]) >= len(PLANET_IN_SIGN_BATCH)
    sample_rule = next(rule for rule in rules if rule.canonical_code == "sun_in_aries")
    assert sample_rule.metadata_json["engine_contract"]["system"] == "hellenistic"
