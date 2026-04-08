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


def _validate_modifier(modifier: dict[str, Any], *, rule_code: str, index: int) -> None:
    modifier_type = modifier.get("type")
    _ensure(modifier_type in ALLOWED_MODIFIER_TYPES, f"{rule_code} modifier[{index}] has invalid type")

    condition = modifier.get("condition")
    _ensure(isinstance(condition, dict), f"{rule_code} modifier[{index}] condition must be an object")
    condition_type = condition.get("type")
    _ensure(condition_type in ALLOWED_CONDITION_TYPES, f"{rule_code} modifier[{index}] has invalid condition.type")

    value = condition.get("value")
    _ensure(value is not None, f"{rule_code} modifier[{index}] must include condition.value")

    if condition_type == "house":
        _ensure(isinstance(value, dict), f"{rule_code} modifier[{index}] house condition must be an object")
        has_category = "category" in value
        has_house = "house" in value
        _ensure(has_category ^ has_house, f"{rule_code} modifier[{index}] house condition must use category or house")
        if has_category:
            _ensure(value["category"] in {"angular", "succedent", "cadent"}, f"{rule_code} modifier[{index}] invalid house category")
        if has_house:
            _ensure(isinstance(value["house"], int) and 1 <= value["house"] <= 12, f"{rule_code} modifier[{index}] invalid house number")

    elif condition_type == "aspect":
        _ensure(isinstance(value, dict), f"{rule_code} modifier[{index}] aspect condition must be an object")
        _ensure(set(value) == {"aspect", "planet"}, f"{rule_code} modifier[{index}] aspect condition must include aspect and planet")
        _ensure(isinstance(value["aspect"], str), f"{rule_code} modifier[{index}] aspect must be a string")
        _ensure(isinstance(value["planet"], str), f"{rule_code} modifier[{index}] planet must be a string")
        _ensure_lowercase(value["aspect"], f"{rule_code} modifier[{index}] aspect")
        _ensure_lowercase(value["planet"], f"{rule_code} modifier[{index}] planet")

    elif condition_type == "dignity":
        _ensure(isinstance(value, dict), f"{rule_code} modifier[{index}] dignity condition must be an object")
        _ensure(set(value) == {"state", "planet"}, f"{rule_code} modifier[{index}] dignity condition must include state and planet")
        _ensure(value["state"] in {item.value for item in DignityType}, f"{rule_code} modifier[{index}] invalid dignity state")
        _ensure(isinstance(value["planet"], str), f"{rule_code} modifier[{index}] dignity planet must be a string")
        _ensure_lowercase(value["planet"], f"{rule_code} modifier[{index}] dignity planet")

    elif condition_type == "rulership":
        _ensure(isinstance(value, dict), f"{rule_code} modifier[{index}] rulership condition must be an object")
        _ensure(set(value) == {"ruler", "placement"}, f"{rule_code} modifier[{index}] rulership condition must include ruler and placement")
        _ensure(isinstance(value["ruler"], str), f"{rule_code} modifier[{index}] ruler must be a string")
        _ensure_lowercase(value["ruler"], f"{rule_code} modifier[{index}] ruler")
        placement = value["placement"]
        _ensure(isinstance(placement, dict), f"{rule_code} modifier[{index}] rulership placement must be an object")
        _ensure(placement.get("type") == "house", f"{rule_code} modifier[{index}] rulership placement.type must be 'house'")
        _ensure(isinstance(placement.get("value"), int) and 1 <= placement["value"] <= 12, f"{rule_code} modifier[{index}] invalid rulership house")

    weight_delta = modifier.get("weight_delta")
    _ensure(isinstance(weight_delta, (int, float)), f"{rule_code} modifier[{index}] weight_delta must be numeric")
    if modifier_type == "amplifier":
        _ensure(0.15 <= float(weight_delta) <= 0.25, f"{rule_code} modifier[{index}] amplifier weight_delta out of range")
    elif modifier_type == "mitigator":
        _ensure(-0.15 <= float(weight_delta) <= -0.05, f"{rule_code} modifier[{index}] mitigator weight_delta out of range")
    else:
        _ensure(0.05 <= float(weight_delta) <= 0.12, f"{rule_code} modifier[{index}] redirector weight_delta out of range")

    effect = modifier.get("effect")
    _ensure(isinstance(effect, str) and effect.strip(), f"{rule_code} modifier[{index}] effect is required")


def validate_planet_in_sign_item(item: dict[str, Any]) -> None:
    _ensure(set(item) == {"interpretation_rule", "interpretation_block"}, "dataset item must contain interpretation_rule and interpretation_block")
    rule = item["interpretation_rule"]
    block = item["interpretation_block"]
    _ensure(isinstance(rule, dict), "interpretation_rule must be an object")
    _ensure(isinstance(block, dict), "interpretation_block must be an object")

    required_rule_fields = {
        "canonical_code",
        "rule_type",
        "subject_1_type",
        "subject_1_id",
        "subject_2_type",
        "subject_2_id",
        "system",
        "base_weight",
        "status",
        "version",
    }
    required_block_fields = {
        "theme",
        "core_statement",
        "manifestation",
        "risk_expression",
        "modifiers_json",
        "interpretive_weight",
        "priority",
    }

    _ensure(required_rule_fields <= set(rule), f"{rule.get('canonical_code', '<unknown>')} missing required rule fields")
    _ensure(required_block_fields <= set(block), f"{rule.get('canonical_code', '<unknown>')} missing required block fields")

    for field_name in LOWERCASE_FIELDS & set(rule):
        value = rule[field_name]
        _ensure(isinstance(value, str), f"{field_name} must be a string")
        _ensure_lowercase(value, field_name)

    _ensure(rule["rule_type"] == RuleType.PLANET_IN_SIGN.value, f"{rule['canonical_code']} must use planet_in_sign")
    _ensure(rule["subject_1_type"] == "planet", f"{rule['canonical_code']} subject_1_type must be planet")
    _ensure(rule["subject_2_type"] == "sign", f"{rule['canonical_code']} subject_2_type must be sign")
    _ensure(isinstance(rule["base_weight"], (int, float)), f"{rule['canonical_code']} base_weight must be numeric")
    _ensure(isinstance(rule["version"], int) and rule["version"] >= 1, f"{rule['canonical_code']} version must be >= 1")

    theme = block["theme"]
    _ensure(theme == InterpretiveTheme.IDENTITY.value, f"{rule['canonical_code']} theme must be identity in MVP")
    _ensure_lowercase(theme, "theme")

    for field_name in ("core_statement", "manifestation", "risk_expression"):
        value = block[field_name]
        _ensure(isinstance(value, str) and value.strip(), f"{rule['canonical_code']} {field_name} is required")

    modifiers = block["modifiers_json"]
    _ensure(isinstance(modifiers, list) and len(modifiers) >= 2, f"{rule['canonical_code']} must include at least 2 modifiers")
    for index, modifier in enumerate(modifiers):
        _ensure(isinstance(modifier, dict), f"{rule['canonical_code']} modifier[{index}] must be an object")
        _validate_modifier(modifier, rule_code=rule["canonical_code"], index=index)


def validate_planet_in_sign_dataset(dataset: Sequence[dict[str, Any]]) -> None:
    _ensure(isinstance(dataset, Sequence) and not isinstance(dataset, (str, bytes)), "dataset must be a sequence of items")
    seen_codes: set[str] = set()
    for item in dataset:
        validate_planet_in_sign_item(item)
        canonical_code = item["interpretation_rule"]["canonical_code"]
        _ensure(canonical_code not in seen_codes, f"duplicate canonical_code: {canonical_code}")
        seen_codes.add(canonical_code)
