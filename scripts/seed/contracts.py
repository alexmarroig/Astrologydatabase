from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.core.enums import DignityType, InterpretiveTheme, RuleType

ALLOWED_MODIFIER_TYPES = {"amplifier", "mitigator", "redirector"}
ALLOWED_CONDITION_TYPES = {"aspect", "house", "dignity", "rulership"}
LOWERCASE_FIELDS = {
    "canonical_code",
    "rule_type",
    "subject_1_type",
    "subject_1_id",
    "subject_2_type",
    "subject_2_id",
    "subject_3_type",
    "subject_3_id",
    "system",
    "status",
    "theme",
}


class SeedContractError(ValueError):
    """Raised when a dataset item violates the engine seed contract."""


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise SeedContractError(message)


def _ensure_lowercase(value: str, field_name: str) -> None:
    _ensure(value == value.lower(), f"{field_name} must be lowercase: {value!r}")


def validate_item_structure(item: dict[str, Any], required_rule_fields: set[str]) -> None:
    _ensure(set(item) == {"interpretation_rule", "interpretation_block"}, "dataset item must contain interpretation_rule and interpretation_block")
    rule = item["interpretation_rule"]
    block = item["interpretation_block"]
    _ensure(isinstance(rule, dict), "interpretation_rule must be an object")
    _ensure(isinstance(block, dict), "interpretation_block must be an object")

    required_block_fields = {
        "theme",
        "core_statement",
    }

    _ensure(required_rule_fields <= set(rule), f"{rule.get('canonical_code', '<unknown>')} missing required rule fields")
    _ensure(required_block_fields <= set(block), f"{rule.get('canonical_code', '<unknown>')} missing required block fields")

    for field_name in LOWERCASE_FIELDS & set(rule):
        value = rule[field_name]
        if isinstance(value, str):
            _ensure_lowercase(value, field_name)

def validate_planet_in_sign_dataset(dataset: Sequence[dict[str, Any]]) -> None:
    required_fields = {"canonical_code", "rule_type", "subject_1_type", "subject_1_id", "subject_2_type", "subject_2_id", "system"}
    for item in dataset:
        validate_item_structure(item, required_fields)
        rule = item["interpretation_rule"]
        _ensure(rule["rule_type"] == RuleType.PLANET_IN_SIGN.value, f"{rule['canonical_code']} must use planet_in_sign")

def validate_planet_in_house_dataset(dataset: Sequence[dict[str, Any]]) -> None:
    required_fields = {"canonical_code", "rule_type", "subject_1_type", "subject_1_id", "subject_2_type", "subject_2_id", "system"}
    for item in dataset:
        validate_item_structure(item, required_fields)
        rule = item["interpretation_rule"]
        _ensure(rule["rule_type"] == RuleType.PLANET_IN_HOUSE.value, f"{rule['canonical_code']} must use planet_in_house")

def validate_aspects_dataset(dataset: Sequence[dict[str, Any]]) -> None:
    required_fields = {"canonical_code", "rule_type", "subject_1_type", "subject_1_id", "subject_2_type", "subject_2_id", "subject_3_type", "subject_3_id", "system"}
    for item in dataset:
        validate_item_structure(item, required_fields)
        rule = item["interpretation_rule"]
        _ensure(rule["rule_type"] == RuleType.ASPECT_PLANET_PLANET.value, f"{rule['canonical_code']} must use aspect_planet_planet")

def validate_ruler_in_house_dataset(dataset: Sequence[dict[str, Any]]) -> None:
    required_fields = {"canonical_code", "rule_type", "subject_1_type", "subject_1_id", "subject_2_type", "subject_2_id", "system"}
    for item in dataset:
        validate_item_structure(item, required_fields)
        rule = item["interpretation_rule"]
        _ensure(rule["rule_type"] == RuleType.RULER_IN_HOUSE.value, f"{rule['canonical_code']} must use ruler_in_house")
