from __future__ import annotations

import pytest
from app.core.enums import RuleType
from scripts.seed.contracts import (
    validate_planet_in_sign_dataset,
    validate_planet_in_house_dataset,
    validate_aspects_dataset,
    validate_ruler_in_house_dataset,
    SeedContractError
)

def test_validate_planet_in_sign_dataset_success():
    dataset = [
        {
            "interpretation_rule": {
                "canonical_code": "sun_in_aries",
                "rule_type": "planet_in_sign",
                "subject_1_type": "planet",
                "subject_1_id": "sun",
                "subject_2_type": "sign",
                "subject_2_id": "aries",
                "system": "luz_e_sombra"
            },
            "interpretation_block": {
                "theme": "identity",
                "core_statement": "Test statement"
            }
        }
    ]
    validate_planet_in_sign_dataset(dataset)

def test_validate_planet_in_sign_dataset_fail():
    dataset = [
        {
            "interpretation_rule": {
                "canonical_code": "sun_in_aries",
                "rule_type": "invalid_type",
                "subject_1_type": "planet",
                "subject_1_id": "sun",
                "subject_2_type": "sign",
                "subject_2_id": "aries",
                "system": "luz_e_sombra"
            },
            "interpretation_block": {
                "theme": "identity",
                "core_statement": "Test statement"
            }
        }
    ]
    with pytest.raises(SeedContractError):
        validate_planet_in_sign_dataset(dataset)
