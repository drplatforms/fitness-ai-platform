from __future__ import annotations

from dataclasses import dataclass, field

SERVING_UNIT_CONFIDENCE_LOW = "Low"
SERVING_UNIT_CONFIDENCE_MODERATE = "Moderate"
SERVING_UNIT_CONFIDENCE_HIGH = "High"

ALLOWED_SERVING_UNIT_CONFIDENCE = {
    SERVING_UNIT_CONFIDENCE_LOW,
    SERVING_UNIT_CONFIDENCE_MODERATE,
    SERVING_UNIT_CONFIDENCE_HIGH,
}


@dataclass
class NutritionServingUnit:
    id: int
    canonical_food_id: int
    unit_name: str
    unit_quantity: float
    display_name: str
    grams_default: float
    grams_min: float | None = None
    grams_max: float | None = None
    confidence: str = SERVING_UNIT_CONFIDENCE_MODERATE
    source: str | None = None
    source_note: str | None = None
    user_override_allowed: bool = False
    active: bool = True
    sort_order: int = 100
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ServingUnitConversionEstimate:
    serving_unit_id: int
    canonical_food_id: int
    requested_quantity: float
    estimated_grams: float
    grams_min: float | None
    grams_max: float | None
    confidence: str
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ServingUnitSeedSpec:
    canonical_food_display_name: str
    unit_name: str
    unit_quantity: float
    display_name: str
    grams_default: float
    grams_min: float | None
    grams_max: float | None
    confidence: str
    source: str
    source_note: str
    sort_order: int = 100
    user_override_allowed: bool = False
    active: bool = True


@dataclass
class ServingUnitSeedResult:
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    missing_canonical_foods: list[str] = field(default_factory=list)
    active_serving_unit_count: int = 0
    seeded_serving_units: list[NutritionServingUnit] = field(default_factory=list)
