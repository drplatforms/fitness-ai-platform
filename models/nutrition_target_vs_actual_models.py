from __future__ import annotations

from dataclasses import asdict, dataclass, field

NUTRITION_CONFIDENCE_VALUES = {"Limited", "Low", "Moderate", "High"}

LOGGING_COMPLETENESS_NO_LOGS = "no_logs"
LOGGING_COMPLETENESS_PARTIAL_DAY = "partial_day"
LOGGING_COMPLETENESS_LIKELY_INCOMPLETE = "likely_incomplete"
LOGGING_COMPLETENESS_REASONABLY_COMPLETE = "reasonably_complete"
LOGGING_COMPLETENESS_COMPLETE_ENOUGH = "complete_enough_for_guidance"

TARGET_STATUS_BELOW = "below_target"
TARGET_STATUS_NEAR = "near_target"
TARGET_STATUS_ABOVE = "above_target"
TARGET_STATUS_UNAVAILABLE = "unavailable"


@dataclass
class NutritionActuals:
    user_id: int
    logging_date: str
    logging_window: str
    logged_calories: float | None = None
    logged_protein: float | None = None
    logged_carbs: float | None = None
    logged_fat: float | None = None
    logged_fiber: float | None = None
    logged_meal_count: int = 0
    entry_count: int = 0
    source_count: int = 0
    missing_calorie_entries: int = 0
    missing_protein_entries: int = 0
    missing_carb_entries: int = 0
    missing_fat_entries: int = 0
    missing_fiber_entries: int = 0
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NutritionLoggingSummary:
    user_id: int
    logging_date: str
    logging_completeness: str
    confidence: str
    logged_meal_count: int
    entry_count: int
    missing_nutrient_fields: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NutritionTargetComparison:
    nutrient: str
    actual: float | None
    target_min: float | None
    target_max: float | None
    delta_min: float | None
    delta_max: float | None
    percent_of_target: float | None
    target_status: str
    comparison_available: bool
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TargetVsActualNutritionSummary:
    user_id: int
    date: str
    nutrition_actuals: NutritionActuals
    logging_summary: NutritionLoggingSummary
    comparisons: dict[str, NutritionTargetComparison]
    logging_completeness: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["nutrition_actuals"] = self.nutrition_actuals.to_dict()
        payload["logging_summary"] = self.logging_summary.to_dict()
        payload["comparisons"] = {
            nutrient: comparison.to_dict()
            for nutrient, comparison in self.comparisons.items()
        }
        return payload


@dataclass
class ApprovedNutritionGuidance:
    user_id: int
    date: str
    summary_message: str
    protein_guidance: str
    calorie_guidance: str
    macro_guidance: str
    logging_guidance: str
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
