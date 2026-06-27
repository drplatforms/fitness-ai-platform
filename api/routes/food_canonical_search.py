from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.food_normalization_service import (
    ensure_starter_canonical_foods_seeded,
    get_canonical_food,
    get_nutrients_for_canonical_food,
    get_raw_food_source_record,
    get_source_links_for_canonical_food,
    search_canonical_foods,
)
from services.nutrition_serving_unit_service import (
    get_active_serving_units_for_canonical_food,
    seed_canonical_food_serving_units,
)

router = APIRouter()

_CANONICAL_SEARCH_MIN_QUERY_LENGTH = 2
_CANONICAL_SEARCH_DEFAULT_LIMIT = 10
_CANONICAL_SEARCH_MAX_LIMIT = 25

_NUTRIENT_SUMMARY_KEYS = {
    "calories": "calories_per_100g",
    "calorie": "calories_per_100g",
    "energy": "calories_per_100g",
    "protein": "protein_g_per_100g",
    "carbohydrate": "carbohydrate_g_per_100g",
    "carbohydrates": "carbohydrate_g_per_100g",
    "carbs": "carbohydrate_g_per_100g",
    "total carbohydrate": "carbohydrate_g_per_100g",
    "fat": "fat_g_per_100g",
    "total fat": "fat_g_per_100g",
}


def _normalize_nutrient_name(name: str) -> str:
    return " ".join(name.strip().lower().replace("_", " ").split())


def _bounded_limit(limit: int) -> int:
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be at least 1.")
    return min(limit, _CANONICAL_SEARCH_MAX_LIMIT)


def _build_nutrient_summary(canonical_food_id: int) -> dict[str, float]:
    summary: dict[str, float] = {}
    for nutrient in get_nutrients_for_canonical_food(canonical_food_id):
        summary_key = _NUTRIENT_SUMMARY_KEYS.get(
            _normalize_nutrient_name(nutrient.nutrient_name)
        )
        if summary_key is not None:
            summary[summary_key] = nutrient.amount_per_100g
    return summary


def _build_source_links(canonical_food_id: int) -> list[dict[str, str | int | None]]:
    public_links: list[dict[str, str | int | None]] = []
    for link in get_source_links_for_canonical_food(canonical_food_id):
        raw_record = get_raw_food_source_record(link.raw_food_source_record_id)
        if raw_record is None:
            continue
        public_links.append(
            {
                "relationship_type": link.relationship_type,
                "source_name": raw_record.source_name,
                "source_record_id": raw_record.source_record_id,
                "raw_description": raw_record.raw_description,
                "brand_name": raw_record.brand_name,
                "food_category": raw_record.food_category,
                "source_url": raw_record.source_url,
                "license": raw_record.license,
            }
        )
    return public_links


def _serving_unit_to_public_dict(serving_unit) -> dict:
    return {
        "serving_unit_id": serving_unit.id,
        "display_name": serving_unit.display_name,
        "unit_name": serving_unit.unit_name,
        "unit_quantity": serving_unit.unit_quantity,
        "grams_default": serving_unit.grams_default,
        "grams_min": serving_unit.grams_min,
        "grams_max": serving_unit.grams_max,
        "confidence": serving_unit.confidence,
        "amount_source": "serving_unit_estimate",
        "source": serving_unit.source,
        "source_notes": serving_unit.source_note,
        "sort_order": serving_unit.sort_order,
    }


def _get_public_active_canonical_food(canonical_food_id: int):
    canonical_food = get_canonical_food(canonical_food_id)
    if canonical_food is None or not canonical_food.active:
        raise HTTPException(status_code=404, detail="Canonical food not found.")
    return canonical_food


def _canonical_search_result_to_public_dict(
    result,
    *,
    include_source_links: bool,
) -> dict:
    food = result.canonical_food
    payload = {
        "canonical_food_id": food.id,
        "display_name": food.display_name,
        "food_type": food.food_type,
        "default_unit": food.default_unit,
        "default_grams": food.default_grams,
        "search_priority": food.search_priority,
        "matched_on": result.matched_on,
        "aliases": list(result.aliases),
    }

    nutrient_summary = _build_nutrient_summary(food.id)
    if nutrient_summary:
        payload["nutrient_summary"] = nutrient_summary

    if include_source_links:
        payload["source_links"] = _build_source_links(food.id)

    return payload


@router.get("/foods/canonical/search")
def canonical_food_search_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=_CANONICAL_SEARCH_DEFAULT_LIMIT),
    include_inactive: bool = False,
    include_source_links: bool = False,
):
    """Return public-safe canonical food search results for user-facing food picks."""

    query = q.strip()
    if len(query) < _CANONICAL_SEARCH_MIN_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="q must be at least 2 characters for canonical food search.",
        )

    ensure_starter_canonical_foods_seeded()
    results = search_canonical_foods(
        query,
        limit=_bounded_limit(limit),
        include_inactive=include_inactive,
    )

    return {
        "success": True,
        "query": query,
        "results": [
            _canonical_search_result_to_public_dict(
                result,
                include_source_links=include_source_links,
            )
            for result in results
        ],
    }


@router.get("/foods/canonical/{canonical_food_id}/serving-units")
def canonical_food_serving_units_endpoint(canonical_food_id: int):
    """Return public-safe active serving units for a canonical food."""

    ensure_starter_canonical_foods_seeded()
    seed_canonical_food_serving_units()

    canonical_food = _get_public_active_canonical_food(canonical_food_id)
    serving_units = get_active_serving_units_for_canonical_food(canonical_food.id)

    return {
        "success": True,
        "canonical_food_id": canonical_food.id,
        "display_name": canonical_food.display_name,
        "serving_units": [
            _serving_unit_to_public_dict(serving_unit) for serving_unit in serving_units
        ],
    }
