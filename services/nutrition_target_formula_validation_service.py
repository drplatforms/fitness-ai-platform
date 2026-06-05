from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from models.nutrition_target_formula_models import (
    DISPLAY_FLAG_KEYS,
    MINIMUM_NON_EXTREME_CALORIE_TARGET,
    NUTRITION_TARGET_CONFIDENCE_VALUES,
    ApprovedMacroTargets,
    MacroTargetResult,
    NutritionTargetFormulaMetadata,
    NutritionTargetFormulaResult,
)
from services.nutrition_target_formula_service import approve_macro_targets

CALORIE_REQUIRED_INPUT_REASON_CODES = {
    "missing_body_weight",
    "missing_height",
    "missing_age",
    "missing_sex",
    "missing_activity_level",
    "missing_primary_goal",
}
MISSING_INPUT_REASON_PREFIX = "missing_"
ASSUMPTION_REASON_CODES = {
    "formula_assumption_used",
    "formula_inputs_limited",
    *CALORIE_REQUIRED_INPUT_REASON_CODES,
}

_TARGETS_BY_RESULT_FLAG = {
    "allow_calorie_targets": "calorie_target",
    "allow_protein_targets": "protein_target",
    "allow_carbohydrate_targets": "carbohydrate_target",
    "allow_fat_targets": "fat_target",
}
_TARGETS_BY_APPROVED_FLAG = {
    "allow_calorie_targets": "calorie_target",
    "allow_protein_targets": "protein_target_g",
    "allow_carbohydrate_targets": "carbohydrate_target_g",
    "allow_fat_targets": "fat_target_g",
}

_FORBIDDEN_LANGUAGE = [
    "ai-generated",
    "ai generated",
    "artificial intelligence generated",
    "crewai",
    "ollama",
    "llm generated",
    "must cut calories",
    "skip meals",
    "starve",
    "starvation",
    "eating disorder",
    "guaranteed fat loss",
    "fat-loss certainty",
    "stalled fat-loss",
    "stalled fat loss",
    "diagnose",
    "treat disease",
    "supplement recommendation",
    "take supplements",
]


def validate_nutrition_target_formula_result(
    formula_result: NutritionTargetFormulaResult,
) -> NutritionTargetFormulaResult:
    """Validate formula output before any public/API/UI integration.

    The formula models enforce many construction-time invariants. This service is a
    second approval boundary that checks mutated/assembled results, target
    dependencies, metadata completeness, display safety, and forbidden language.
    """

    _validate_common_contract(
        user_id=formula_result.user_id,
        confidence=formula_result.confidence,
        display_flags=formula_result.display_flags,
        formula_metadata=formula_result.formula_metadata,
        reason_codes=formula_result.reason_codes,
        limitations=formula_result.limitations,
        targets_by_flag={
            flag: getattr(formula_result, field_name)
            for flag, field_name in _TARGETS_BY_RESULT_FLAG.items()
        },
    )
    return formula_result


def validate_approved_macro_targets(
    approved_targets: ApprovedMacroTargets,
) -> ApprovedMacroTargets:
    """Validate the approved macro-target contract before downstream use."""

    _validate_common_contract(
        user_id=approved_targets.user_id,
        confidence=approved_targets.confidence,
        display_flags=approved_targets.display_flags,
        formula_metadata=approved_targets.formula_metadata,
        reason_codes=approved_targets.reason_codes,
        limitations=approved_targets.limitations,
        targets_by_flag={
            flag: getattr(approved_targets, field_name)
            for flag, field_name in _TARGETS_BY_APPROVED_FLAG.items()
        },
    )
    return approved_targets


def approve_validated_macro_targets(
    formula_result: NutritionTargetFormulaResult,
) -> ApprovedMacroTargets:
    """Validate formula output, approve it, then validate the approved contract."""

    validate_nutrition_target_formula_result(formula_result)
    approved_targets = approve_macro_targets(formula_result)
    return validate_approved_macro_targets(approved_targets)


def _validate_common_contract(
    *,
    user_id: int,
    confidence: str,
    display_flags: dict[str, bool],
    formula_metadata: NutritionTargetFormulaMetadata | None,
    reason_codes: list[str],
    limitations: list[str],
    targets_by_flag: dict[str, MacroTargetResult | None],
) -> None:
    if user_id <= 0:
        raise ValueError("user_id must be positive")

    _validate_confidence(confidence)
    _validate_display_flags(display_flags)
    _validate_formula_metadata(formula_metadata)
    _validate_missing_input_rules(display_flags, targets_by_flag, reason_codes)
    _validate_targets_and_flags(display_flags, targets_by_flag)
    _validate_target_dependency_rules(display_flags, targets_by_flag)
    _validate_required_limitations(
        reason_codes=reason_codes,
        limitations=limitations,
        formula_metadata=formula_metadata,
        targets=targets_by_flag.values(),
    )
    _validate_no_forbidden_language(
        reason_codes=reason_codes,
        limitations=limitations,
        formula_metadata=formula_metadata,
        targets=targets_by_flag.values(),
    )


def _validate_confidence(confidence: str) -> None:
    if confidence not in NUTRITION_TARGET_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_display_flags(display_flags: dict[str, bool]) -> None:
    missing_flags = DISPLAY_FLAG_KEYS - set(display_flags)
    if missing_flags:
        raise ValueError(f"Missing display flags: {', '.join(sorted(missing_flags))}")

    extra_flags = set(display_flags) - DISPLAY_FLAG_KEYS
    if extra_flags:
        raise ValueError(f"Unknown display flags: {', '.join(sorted(extra_flags))}")

    for flag_name, flag_value in display_flags.items():
        if not isinstance(flag_value, bool):
            raise ValueError(f"Display flag must be boolean: {flag_name}")


def _validate_formula_metadata(
    formula_metadata: NutritionTargetFormulaMetadata | None,
) -> None:
    if formula_metadata is None:
        raise ValueError("formula_metadata is required")
    if not formula_metadata.formula_name:
        raise ValueError("formula_metadata.formula_name is required")
    if not formula_metadata.formula_version:
        raise ValueError("formula_metadata.formula_version is required")
    if not formula_metadata.inputs_used:
        raise ValueError("formula_metadata.inputs_used is required")
    if not formula_metadata.rounding_rules:
        raise ValueError("formula_metadata.rounding_rules is required")
    if not formula_metadata.target_basis:
        raise ValueError("formula_metadata.target_basis is required")
    if formula_metadata.assumptions and not formula_metadata.limitations:
        raise ValueError("formula_metadata.limitations are required with assumptions")


def _validate_targets_and_flags(
    display_flags: dict[str, bool],
    targets_by_flag: dict[str, MacroTargetResult | None],
) -> None:
    for flag_name, target in targets_by_flag.items():
        flag_value = display_flags[flag_name]

        if flag_value and target is None:
            raise ValueError(f"{flag_name} is true but target is missing")
        if target is None:
            continue

        _validate_target_values(target)

        if flag_value != target.display_allowed:
            raise ValueError(f"{flag_name} does not match target display_allowed")

        if target.display_allowed:
            _validate_displayable_target(target)
        elif not (target.reason_codes or target.limitations):
            raise ValueError(
                "Blocked macro targets require reason_codes or limitations"
            )


def _validate_displayable_target(target: MacroTargetResult) -> None:
    if target.value is None or target.min_value is None or target.max_value is None:
        raise ValueError(
            f"{target.target_type} display is allowed but values are missing"
        )
    if not target.display_value:
        raise ValueError(
            f"{target.target_type} display is allowed but display_value is missing"
        )
    if not target.method:
        raise ValueError(
            f"{target.target_type} display is allowed but method is missing"
        )


def _validate_target_values(target: MacroTargetResult) -> None:
    _validate_confidence(target.confidence)

    values = [target.value, target.min_value, target.max_value]
    for value in values:
        if value is not None and value < 0:
            raise ValueError(f"{target.target_type} target values must be non-negative")

    if (
        target.min_value is not None
        and target.max_value is not None
        and target.min_value > target.max_value
    ):
        raise ValueError(f"{target.target_type} min_value must be <= max_value")

    if target.target_type == "calories":
        for value in values:
            if (
                value is not None
                and value > 0
                and value < MINIMUM_NON_EXTREME_CALORIE_TARGET
            ):
                raise ValueError("Calorie target range implies extreme restriction")

    if target.display_allowed:
        _validate_rounding(target)


def _validate_rounding(target: MacroTargetResult) -> None:
    rounding_step = 50 if target.target_type == "calories" else 5
    for value in [target.value, target.min_value, target.max_value]:
        if value is not None and value % rounding_step != 0:
            raise ValueError(
                f"{target.target_type} target values must be rounded to {rounding_step}"
            )


def _validate_target_dependency_rules(
    display_flags: dict[str, bool],
    targets_by_flag: dict[str, MacroTargetResult | None],
) -> None:
    calorie_allowed = display_flags["allow_calorie_targets"]
    protein_allowed = display_flags["allow_protein_targets"]
    fat_allowed = display_flags["allow_fat_targets"]
    carbohydrate_allowed = display_flags["allow_carbohydrate_targets"]

    if carbohydrate_allowed and not calorie_allowed:
        raise ValueError("Carbohydrate targets cannot display without calorie targets")
    if carbohydrate_allowed and not protein_allowed:
        raise ValueError("Carbohydrate targets cannot display without protein targets")
    if carbohydrate_allowed and not fat_allowed:
        raise ValueError("Carbohydrate targets cannot display without fat targets")
    if fat_allowed and not calorie_allowed:
        raise ValueError("Fat targets cannot display without calorie targets")

    carbohydrate_target = targets_by_flag["allow_carbohydrate_targets"]
    if (
        carbohydrate_target
        and carbohydrate_target.display_allowed
        and not calorie_allowed
    ):
        raise ValueError("Carbohydrate target display depends on approved calories")

    fat_target = targets_by_flag["allow_fat_targets"]
    if fat_target and fat_target.display_allowed and not calorie_allowed:
        raise ValueError("Fat target display depends on approved calories")


def _validate_missing_input_rules(
    display_flags: dict[str, bool],
    targets_by_flag: dict[str, MacroTargetResult | None],
    reason_codes: list[str],
) -> None:
    all_reason_codes = set(reason_codes)
    for target in targets_by_flag.values():
        if target:
            all_reason_codes.update(target.reason_codes)

    if "missing_body_weight" in all_reason_codes:
        protein_target = targets_by_flag["allow_protein_targets"]
        if display_flags["allow_protein_targets"] or (
            protein_target and protein_target.display_allowed
        ):
            raise ValueError(
                "Protein display must be blocked when body weight is missing"
            )

    if all_reason_codes & CALORIE_REQUIRED_INPUT_REASON_CODES:
        calorie_target = targets_by_flag["allow_calorie_targets"]
        if display_flags["allow_calorie_targets"] or (
            calorie_target and calorie_target.display_allowed
        ):
            raise ValueError(
                "Calorie display must be blocked when formula inputs are missing"
            )


def _validate_required_limitations(
    *,
    reason_codes: list[str],
    limitations: list[str],
    formula_metadata: NutritionTargetFormulaMetadata,
    targets: Iterable[MacroTargetResult | None],
) -> None:
    all_reason_codes = set(reason_codes) | set(formula_metadata.reason_codes)
    target_limitations: list[str] = []
    for target in targets:
        if target is None:
            continue
        all_reason_codes.update(target.reason_codes)
        target_limitations.extend(target.limitations)

    has_missing_input = any(
        code.startswith(MISSING_INPUT_REASON_PREFIX) for code in all_reason_codes
    )
    has_assumption_or_limitation_reason = bool(
        all_reason_codes & ASSUMPTION_REASON_CODES
    )
    if (
        has_missing_input
        or has_assumption_or_limitation_reason
        or formula_metadata.assumptions
    ):
        if not (limitations or formula_metadata.limitations or target_limitations):
            raise ValueError(
                "Limitations are required when inputs are missing or assumptions are used"
            )


def _validate_no_forbidden_language(
    *,
    reason_codes: list[str],
    limitations: list[str],
    formula_metadata: NutritionTargetFormulaMetadata,
    targets: Iterable[MacroTargetResult | None],
) -> None:
    text_parts: list[str] = [
        *reason_codes,
        *limitations,
        formula_metadata.formula_name,
        formula_metadata.formula_version,
        formula_metadata.target_basis,
        *formula_metadata.inputs_used,
        *formula_metadata.assumptions,
        *formula_metadata.rounding_rules,
        *formula_metadata.reason_codes,
        *formula_metadata.limitations,
    ]

    for target in targets:
        if target is None:
            continue
        text_parts.extend(
            [
                target.display_value or "",
                target.method,
                *target.reason_codes,
                *target.limitations,
            ]
        )

    combined_text = _normalize_text(" ".join(text_parts))
    for forbidden_phrase in _FORBIDDEN_LANGUAGE:
        if forbidden_phrase in combined_text:
            raise ValueError(f"Forbidden nutrition target language: {forbidden_phrase}")


def _normalize_text(value: Any) -> str:
    return str(value).lower().replace("_", "-")
