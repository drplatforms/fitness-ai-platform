from __future__ import annotations

from dataclasses import asdict, dataclass, field

NUTRITION_ACTUAL_SOURCE_RAW_GRAMS = "raw_grams"
NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS = "canonical_grams"
NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT = "canonical_serving_unit"
NUTRITION_ACTUAL_SOURCE_UNKNOWN = "unknown"

NUTRITION_ACTUAL_PRECISION_EXACT = "exact"
NUTRITION_ACTUAL_PRECISION_ESTIMATED = "estimated"
NUTRITION_ACTUAL_PRECISION_RANGED = "ranged"
NUTRITION_ACTUAL_PRECISION_LOW_CONFIDENCE = "low_confidence"
NUTRITION_ACTUAL_PRECISION_UNKNOWN = "unknown"

NUTRITION_ACTUAL_COMPLETENESS_COMPLETE = "complete"
NUTRITION_ACTUAL_COMPLETENESS_PARTIAL = "partial"
NUTRITION_ACTUAL_COMPLETENESS_MISSING_NUTRIENTS = "missing_nutrients"
NUTRITION_ACTUAL_COMPLETENESS_UNKNOWN = "unknown"

NUTRITION_ACTUAL_CONFIDENCE_HIGH = "high"
NUTRITION_ACTUAL_CONFIDENCE_MODERATE = "moderate"
NUTRITION_ACTUAL_CONFIDENCE_LOW = "low"
NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class NutritionActualInterpretation:
    """Public-safe confidence/provenance interpretation for one food entry."""

    food_entry_id: int
    user_id: int | None
    logged_date: str | None
    source_type: str
    precision: str
    confidence_level: str
    nutrient_completeness: str
    has_serving_unit_metadata: bool
    has_grams_range: bool
    resolved_grams: float | None
    grams_min: float | None = None
    grams_max: float | None = None
    grams_range_width: float | None = None
    grams_range_percent: float | None = None
    amount_source: str | None = None
    serving_unit_confidence: str | None = None
    missing_nutrients: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    display_flags: list[str] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, object]:
        """Return a bounded public-safe dictionary without raw DB/source internals."""

        return asdict(self)
