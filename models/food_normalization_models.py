from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawFoodSourceRecord:
    id: int
    source_name: str
    source_record_id: str
    raw_description: str
    brand_name: str | None = None
    food_category: str | None = None
    source_payload_json: str | None = None
    license: str | None = None
    source_url: str | None = None
    imported_at: str | None = None
    updated_at: str | None = None


@dataclass
class CanonicalFood:
    id: int
    display_name: str
    normalized_name: str
    food_type: str = "generic"
    default_unit: str = "grams"
    default_grams: float | None = None
    search_priority: int = 100
    active: bool = True
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class CanonicalFoodAlias:
    id: int
    canonical_food_id: int
    alias: str
    normalized_alias: str
    priority: int = 100
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class CanonicalFoodNutrient:
    id: int
    canonical_food_id: int
    nutrient_name: str
    nutrient_unit: str
    amount_per_100g: float
    source_policy: str = "manually_curated"
    confidence: str = "Moderate"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class FoodSourceLink:
    id: int
    canonical_food_id: int
    raw_food_source_record_id: int
    relationship_type: str = "primary"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class CanonicalFoodSearchResult:
    canonical_food: CanonicalFood
    matched_on: str
    matched_value: str
    rank_score: int
    aliases: list[str] = field(default_factory=list)
