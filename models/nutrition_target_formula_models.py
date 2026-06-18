from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

NUTRITION_TARGET_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

TARGET_TYPE_CALORIES = "calories"
TARGET_TYPE_PROTEIN = "protein_g"
TARGET_TYPE_CARBOHYDRATE = "carbohydrate_g"
TARGET_TYPE_FAT = "fat_g"

NUTRITION_TARGET_TYPES = {
    TARGET_TYPE_CALORIES,
    TARGET_TYPE_PROTEIN,
    TARGET_TYPE_CARBOHYDRATE,
    TARGET_TYPE_FAT,
}

DISPLAY_FLAG_KEYS = {
    "allow_calorie_targets",
    "allow_protein_targets",
    "allow_carbohydrate_targets",
    "allow_fat_targets",
}

# Contract-level guardrail only. Formula implementation can refine this later,
# but model contracts should not allow obviously extreme calorie targets.
MINIMUM_NON_EXTREME_CALORIE_TARGET = 1200


@dataclass
class NutritionTargetFormulaInputs:
    user_id: int
    calculation_date: str
    body_weight_lb: float | None = None
    height_in: float | None = None
    age_years: int | None = None
    sex: str | None = None
    activity_level: str | None = None
    training_frequency_per_week: int | None = None
    training_load: str | None = None
    primary_goal: str | None = None
    goal_weight_lb: float | None = None
    recovery_status: str | None = None
    nutrition_logging_quality: str | None = None
    recent_weight_trend: str | None = None
    formula_version_requested: str | None = None
    input_source_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_optional_non_negative("body_weight_lb", self.body_weight_lb)
        _validate_optional_non_negative("height_in", self.height_in)
        _validate_optional_non_negative("age_years", self.age_years)
        _validate_optional_non_negative(
            "training_frequency_per_week", self.training_frequency_per_week
        )
        _validate_optional_non_negative("goal_weight_lb", self.goal_weight_lb)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MacroTargetResult:
    target_type: str
    value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    display_value: str | None = None
    unit: str = ""
    confidence: str = "Limited"
    display_allowed: bool = False
    method: str = ""
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.target_type not in NUTRITION_TARGET_TYPES:
            raise ValueError(f"Invalid target_type: {self.target_type}")

        _validate_confidence(self.confidence)
        _validate_optional_non_negative("value", self.value)
        _validate_optional_non_negative("min_value", self.min_value)
        _validate_optional_non_negative("max_value", self.max_value)
        _validate_range("min_value", self.min_value, "max_value", self.max_value)
        _validate_calorie_target_not_extreme(self)

        if not self.display_allowed and not (self.reason_codes or self.limitations):
            raise ValueError(
                "Blocked macro targets must include reason_codes or limitations."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionTargetFormulaMetadata:
    formula_name: str
    formula_version: str
    calculation_date: str
    inputs_used: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    rounding_rules: list[str] = field(default_factory=list)
    target_basis: str = ""
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.formula_name:
            raise ValueError("formula_name is required")
        if not self.formula_version:
            raise ValueError("formula_version is required")
        if self.assumptions and not self.limitations:
            raise ValueError("limitations are required when assumptions are used")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NutritionTargetFormulaResult:
    user_id: int
    calculation_date: str
    calorie_target: MacroTargetResult | None
    protein_target: MacroTargetResult | None
    carbohydrate_target: MacroTargetResult | None
    fat_target: MacroTargetResult | None
    formula_metadata: NutritionTargetFormulaMetadata
    confidence: str
    display_flags: dict[str, bool]
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_confidence(self.confidence)
        _validate_display_flags(self.display_flags)
        _validate_target_matches_type(
            "calorie_target", self.calorie_target, TARGET_TYPE_CALORIES
        )
        _validate_target_matches_type(
            "protein_target", self.protein_target, TARGET_TYPE_PROTEIN
        )
        _validate_target_matches_type(
            "carbohydrate_target",
            self.carbohydrate_target,
            TARGET_TYPE_CARBOHYDRATE,
        )
        _validate_target_matches_type("fat_target", self.fat_target, TARGET_TYPE_FAT)
        _validate_display_flags_match_targets(
            self.display_flags,
            {
                "allow_calorie_targets": self.calorie_target,
                "allow_protein_targets": self.protein_target,
                "allow_carbohydrate_targets": self.carbohydrate_target,
                "allow_fat_targets": self.fat_target,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovedMacroTargets:
    user_id: int
    calculation_date: str
    calorie_target: MacroTargetResult | None
    protein_target_g: MacroTargetResult | None
    carbohydrate_target_g: MacroTargetResult | None
    fat_target_g: MacroTargetResult | None
    confidence: str
    display_flags: dict[str, bool]
    formula_metadata: NutritionTargetFormulaMetadata
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_confidence(self.confidence)
        _validate_display_flags(self.display_flags)
        _validate_target_matches_type(
            "calorie_target", self.calorie_target, TARGET_TYPE_CALORIES
        )
        _validate_target_matches_type(
            "protein_target_g", self.protein_target_g, TARGET_TYPE_PROTEIN
        )
        _validate_target_matches_type(
            "carbohydrate_target_g",
            self.carbohydrate_target_g,
            TARGET_TYPE_CARBOHYDRATE,
        )
        _validate_target_matches_type(
            "fat_target_g", self.fat_target_g, TARGET_TYPE_FAT
        )
        _validate_display_flags_match_targets(
            self.display_flags,
            {
                "allow_calorie_targets": self.calorie_target,
                "allow_protein_targets": self.protein_target_g,
                "allow_carbohydrate_targets": self.carbohydrate_target_g,
                "allow_fat_targets": self.fat_target_g,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_confidence(confidence: str) -> None:
    if confidence not in NUTRITION_TARGET_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_display_flags(display_flags: dict[str, bool]) -> None:
    missing_flags = DISPLAY_FLAG_KEYS - set(display_flags)
    if missing_flags:
        missing = ", ".join(sorted(missing_flags))
        raise ValueError(f"Missing display flags: {missing}")

    for flag_name, flag_value in display_flags.items():
        if flag_name not in DISPLAY_FLAG_KEYS:
            raise ValueError(f"Unknown display flag: {flag_name}")
        if not isinstance(flag_value, bool):
            raise ValueError(f"Display flag must be boolean: {flag_name}")


def _validate_target_matches_type(
    field_name: str, target: MacroTargetResult | None, expected_target_type: str
) -> None:
    if target is None:
        return
    if target.target_type != expected_target_type:
        raise ValueError(
            f"{field_name} must have target_type {expected_target_type}; "
            f"got {target.target_type}"
        )


def _validate_display_flags_match_targets(
    display_flags: dict[str, bool], targets_by_flag: dict[str, MacroTargetResult | None]
) -> None:
    for flag_name, target in targets_by_flag.items():
        if display_flags[flag_name] and target is None:
            raise ValueError(f"{flag_name} is true but target is missing")
        if display_flags[flag_name] and target and not target.display_allowed:
            raise ValueError(f"{flag_name} is true but target display is blocked")


def _validate_optional_non_negative(field_name: str, value: float | int | None) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_positive_int(field_name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_range(
    min_field_name: str,
    min_value: float | None,
    max_field_name: str,
    max_value: float | None,
) -> None:
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError(f"{min_field_name} must be <= {max_field_name}")


def _validate_calorie_target_not_extreme(target: MacroTargetResult) -> None:
    if target.target_type != TARGET_TYPE_CALORIES:
        return

    calorie_values = [target.value, target.min_value, target.max_value]
    for calorie_value in calorie_values:
        if (
            calorie_value is not None
            and calorie_value > 0
            and calorie_value < MINIMUM_NON_EXTREME_CALORIE_TARGET
        ):
            raise ValueError("Calorie target range implies extreme restriction")
