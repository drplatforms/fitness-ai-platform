from __future__ import annotations

from dataclasses import asdict, dataclass, field

NUTRITION_FOOD_SUGGESTION_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

MACRO_NAME_CALORIES = "calories"
MACRO_NAME_PROTEIN = "protein_g"
MACRO_NAME_CARBOHYDRATE = "carbohydrate_g"
MACRO_NAME_FAT = "fat_g"

NUTRITION_MACRO_NAMES = {
    MACRO_NAME_CALORIES,
    MACRO_NAME_PROTEIN,
    MACRO_NAME_CARBOHYDRATE,
    MACRO_NAME_FAT,
}

TARGET_STATUS_BELOW = "below_target"
TARGET_STATUS_NEAR = "near_target"
TARGET_STATUS_ABOVE = "above_target"
TARGET_STATUS_UNAVAILABLE = "unavailable"
TARGET_STATUS_LIMITED = "limited"

NUTRITION_GAP_TARGET_STATUSES = {
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TARGET_STATUS_ABOVE,
    TARGET_STATUS_UNAVAILABLE,
    TARGET_STATUS_LIMITED,
}

ALLOWED_PRIMARY_GAPS = NUTRITION_MACRO_NAMES | {"none", None}

FORBIDDEN_NUTRITION_SUGGESTION_LANGUAGE = {
    "you must eat",
    "you failed",
    "burn this off",
    "skip meals",
    "compensate tomorrow",
    "fat-loss guarantee",
    "fat loss guarantee",
    "guaranteed fat loss",
    "exact physiological certainty",
    "ai-generated food",
    "ai generated food",
    "medical treatment",
    "disease treatment",
}


@dataclass
class NutritionMacroGap:
    macro_name: str
    target_value: float | None
    actual_value: float | None
    gap_value: float | None
    unit: str
    target_status: str
    display_allowed: bool
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_macro_name(self.macro_name)
        _validate_optional_non_negative("target_value", self.target_value)
        _validate_optional_non_negative("actual_value", self.actual_value)
        _validate_optional_non_negative("gap_value", self.gap_value)
        _validate_target_status(self.target_status)
        _validate_confidence(self.confidence)

        if self.target_status in {TARGET_STATUS_UNAVAILABLE, TARGET_STATUS_LIMITED}:
            if self.display_allowed:
                raise ValueError(
                    "Unavailable or limited macro gaps cannot be display allowed"
                )
            if not (self.reason_codes or self.limitations):
                raise ValueError(
                    "Unavailable or limited macro gaps require reason_codes or limitations"
                )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CanonicalFoodSuggestionCandidate:
    canonical_food_id: int
    display_name: str
    food_type: str
    serving_grams: float
    calories: float | None
    protein_g: float | None
    carbohydrate_g: float | None
    fat_g: float | None
    macro_gap_addressed: str
    score: float
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("canonical_food_id", self.canonical_food_id)
        _validate_required_text("display_name", self.display_name)
        _validate_positive_number("serving_grams", self.serving_grams)
        _validate_optional_non_negative("calories", self.calories)
        _validate_optional_non_negative("protein_g", self.protein_g)
        _validate_optional_non_negative("carbohydrate_g", self.carbohydrate_g)
        _validate_optional_non_negative("fat_g", self.fat_g)
        _validate_macro_name(self.macro_gap_addressed)
        _validate_non_negative("score", self.score)
        _validate_confidence(self.confidence)
        _validate_no_forbidden_language(self.display_name)

        if self._has_missing_nutrients() and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Candidates with incomplete nutrient estimates require reason_codes or limitations"
            )

    def _has_missing_nutrients(self) -> bool:
        return any(
            value is None
            for value in (
                self.calories,
                self.protein_g,
                self.carbohydrate_g,
                self.fat_g,
            )
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovedFoodSuggestion:
    canonical_food_id: int
    display_name: str
    suggested_grams: float
    estimated_calories: float | None
    estimated_protein_g: float | None
    estimated_carbohydrate_g: float | None
    estimated_fat_g: float | None
    macro_gap_addressed: str
    suggestion_summary: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("canonical_food_id", self.canonical_food_id)
        _validate_required_text("display_name", self.display_name)
        _validate_positive_number("suggested_grams", self.suggested_grams)
        _validate_optional_non_negative("estimated_calories", self.estimated_calories)
        _validate_optional_non_negative("estimated_protein_g", self.estimated_protein_g)
        _validate_optional_non_negative(
            "estimated_carbohydrate_g", self.estimated_carbohydrate_g
        )
        _validate_optional_non_negative("estimated_fat_g", self.estimated_fat_g)
        _validate_macro_name(self.macro_gap_addressed)
        _validate_required_text("suggestion_summary", self.suggestion_summary)
        _validate_confidence(self.confidence)
        _validate_no_forbidden_language(self.display_name)
        _validate_no_forbidden_language(self.suggestion_summary)

        if self._has_missing_estimates() and not (
            self.reason_codes or self.limitations
        ):
            raise ValueError(
                "Approved suggestions with incomplete nutrient estimates require "
                "reason_codes or limitations"
            )

    def _has_missing_estimates(self) -> bool:
        return any(
            value is None
            for value in (
                self.estimated_calories,
                self.estimated_protein_g,
                self.estimated_carbohydrate_g,
                self.estimated_fat_g,
            )
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovedNutritionFoodSuggestions:
    user_id: int
    suggestion_date: str
    primary_gap: str | None
    macro_gaps: list[NutritionMacroGap]
    suggestions: list[ApprovedFoodSuggestion]
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("suggestion_date", self.suggestion_date)
        if self.primary_gap not in ALLOWED_PRIMARY_GAPS:
            raise ValueError(f"Invalid primary_gap: {self.primary_gap}")
        _validate_confidence(self.confidence)
        _validate_list_items("macro_gaps", self.macro_gaps, NutritionMacroGap)
        _validate_list_items("suggestions", self.suggestions, ApprovedFoodSuggestion)

        if not self.suggestions and not (self.reason_codes or self.limitations):
            raise ValueError(
                "ApprovedNutritionFoodSuggestions with no suggestions requires "
                "reason_codes or limitations"
            )

        self._validate_suggestions_address_approved_gaps()

    def _validate_suggestions_address_approved_gaps(self) -> None:
        gaps_by_macro = {gap.macro_name: gap for gap in self.macro_gaps}
        for suggestion in self.suggestions:
            gap = gaps_by_macro.get(suggestion.macro_gap_addressed)
            if gap is None:
                raise ValueError(
                    "Approved food suggestions must address a known macro gap"
                )
            if not gap.display_allowed or gap.target_status in {
                TARGET_STATUS_UNAVAILABLE,
                TARGET_STATUS_LIMITED,
            }:
                raise ValueError("Blocked targets cannot generate food suggestions")

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_confidence(confidence: str) -> None:
    if confidence not in NUTRITION_FOOD_SUGGESTION_CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {confidence}")


def _validate_macro_name(macro_name: str) -> None:
    if macro_name not in NUTRITION_MACRO_NAMES:
        raise ValueError(f"Invalid macro_name: {macro_name}")


def _validate_target_status(target_status: str) -> None:
    if target_status not in NUTRITION_GAP_TARGET_STATUSES:
        raise ValueError(f"Invalid target_status: {target_status}")


def _validate_required_text(field_name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_positive_int(field_name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_positive_number(field_name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_non_negative(field_name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_optional_non_negative(field_name: str, value: float | None) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_list_items(field_name: str, values: list, expected_type: type) -> None:
    for value in values:
        if not isinstance(value, expected_type):
            raise ValueError(
                f"{field_name} must contain {expected_type.__name__} items"
            )


def _validate_no_forbidden_language(value: str) -> None:
    normalized_value = value.lower()
    for phrase in FORBIDDEN_NUTRITION_SUGGESTION_LANGUAGE:
        if phrase in normalized_value:
            raise ValueError("Forbidden nutrition suggestion language is not allowed")
