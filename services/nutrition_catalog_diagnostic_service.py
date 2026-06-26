from __future__ import annotations

import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import database

CORE_MACRO_NAMES = {
    "calories": "calories",
    "calorie": "calories",
    "energy": "calories",
    "protein": "protein",
    "carbohydrate": "carbohydrates",
    "carbohydrates": "carbohydrates",
    "carbs": "carbohydrates",
    "total carbohydrate": "carbohydrates",
    "fat": "fat",
    "total fat": "fat",
}
CORE_MACROS = ("calories", "protein", "carbohydrates", "fat")
OPTIONAL_NUTRIENTS = ("fiber", "sugar", "sodium")
SERVING_UNIT_TABLE_CANDIDATES = (
    "serving_units",
    "food_serving_units",
    "canonical_food_serving_units",
)

HIGH_VALUE_STAPLES = {
    "proteins": [
        "chicken breast",
        "chicken thigh",
        "turkey",
        "lean ground beef",
        "eggs",
        "egg whites",
        "tuna",
        "salmon",
        "shrimp",
        "greek yogurt",
        "cottage cheese",
        "protein powder",
    ],
    "carbs": [
        "cooked white rice",
        "cooked brown rice",
        "potatoes",
        "sweet potatoes",
        "oats",
        "pasta",
        "bread",
        "tortillas",
        "cereal",
        "bananas",
        "apples",
        "berries",
    ],
    "fats": [
        "olive oil",
        "butter",
        "peanut butter",
        "avocado",
        "almonds",
        "mixed nuts",
        "cheese",
    ],
    "vegetables": [
        "broccoli",
        "spinach",
        "green beans",
        "peppers",
        "onions",
        "carrots",
        "salad greens",
        "mixed vegetables",
    ],
    "convenience_snacks": [
        "protein bars",
        "granola bars",
        "yogurt cups",
        "popcorn",
        "crackers",
    ],
}

NEAR_DUPLICATE_SEARCH_TERMS = (
    "chicken breast",
    "white rice",
    "greek yogurt",
    "peanut butter",
    "potato",
    "egg",
    "bread",
    "tortilla",
    "protein powder",
    "oats",
)


def normalize_food_key(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.lower().replace("%", " percent ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else database.DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"Nutrition database not found: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def _columns(cursor: sqlite3.Cursor, table_name: str) -> list[str]:
    if not _table_exists(cursor, table_name):
        return []
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [str(row["name"]) for row in cursor.fetchall()]


def _count(cursor: sqlite3.Cursor, table_name: str, where: str = "") -> int:
    if not _table_exists(cursor, table_name):
        return 0
    cursor.execute(f"SELECT COUNT(*) AS count FROM {table_name} {where}")
    return int(cursor.fetchone()["count"])


def _rows(
    cursor: sqlite3.Cursor,
    query: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def _food_name_index(
    canonical_foods: list[dict[str, Any]],
    aliases_by_food_id: dict[int, list[str]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for food in canonical_foods:
        food_id = int(food["id"])
        searchable_values = [food.get("display_name", "")]
        searchable_values.extend(aliases_by_food_id.get(food_id, []))
        for value in searchable_values:
            normalized = normalize_food_key(value)
            if normalized:
                index[normalized].append(food)
    return index


def _find_staple_matches(
    staple: str,
    canonical_foods: list[dict[str, Any]],
    aliases_by_food_id: dict[int, list[str]],
) -> list[dict[str, Any]]:
    normalized_staple = normalize_food_key(staple)
    matches: list[dict[str, Any]] = []
    for food in canonical_foods:
        food_id = int(food["id"])
        values = [food.get("display_name", "")]
        values.extend(aliases_by_food_id.get(food_id, []))
        normalized_values = [normalize_food_key(value) for value in values]
        if any(
            normalized_staple == value
            or normalized_staple in value
            or value in normalized_staple
            for value in normalized_values
            if value
        ):
            matches.append(food)
    return matches


def _nutrient_groups(
    canonical_nutrients: list[dict[str, Any]],
) -> dict[int, dict[str, dict[str, Any]]]:
    grouped: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in canonical_nutrients:
        nutrient_key = CORE_MACRO_NAMES.get(
            normalize_food_key(row.get("nutrient_name"))
        )
        if nutrient_key:
            grouped[int(row["canonical_food_id"])][nutrient_key] = row
        optional_key = normalize_food_key(row.get("nutrient_name"))
        if optional_key in OPTIONAL_NUTRIENTS:
            grouped[int(row["canonical_food_id"])][optional_key] = row
    return grouped


def _macro_completeness(
    canonical_foods: list[dict[str, Any]],
    nutrient_by_food_id: dict[int, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    complete_food_ids: list[int] = []
    incomplete_examples: list[dict[str, Any]] = []
    suspicious_zero_examples: list[dict[str, Any]] = []
    calorie_warning_examples: list[dict[str, Any]] = []
    optional_counts = {nutrient: 0 for nutrient in OPTIONAL_NUTRIENTS}

    for food in canonical_foods:
        food_id = int(food["id"])
        nutrients = nutrient_by_food_id.get(food_id, {})
        missing = [macro for macro in CORE_MACROS if macro not in nutrients]
        if not missing:
            complete_food_ids.append(food_id)
        elif len(incomplete_examples) < 20:
            incomplete_examples.append(
                {
                    "canonical_food_id": food_id,
                    "display_name": food.get("display_name"),
                    "missing_core_macros": missing,
                }
            )

        for nutrient in OPTIONAL_NUTRIENTS:
            if nutrient in nutrients:
                optional_counts[nutrient] += 1

        core_amounts = {
            macro: float(nutrients[macro]["amount_per_100g"])
            for macro in CORE_MACROS
            if (
                macro in nutrients
                and nutrients[macro].get("amount_per_100g") is not None
            )
        }
        if all(macro in core_amounts for macro in CORE_MACROS):
            if (
                core_amounts["calories"] <= 0
                and any(
                    core_amounts[macro] > 0
                    for macro in ("protein", "carbohydrates", "fat")
                )
                and len(suspicious_zero_examples) < 20
            ):
                suspicious_zero_examples.append(
                    {
                        "canonical_food_id": food_id,
                        "display_name": food.get("display_name"),
                        "reason": "calories_zero_with_nonzero_macros",
                    }
                )

            derived_calories = round(
                core_amounts["protein"] * 4
                + core_amounts["carbohydrates"] * 4
                + core_amounts["fat"] * 9,
                1,
            )
            calories = core_amounts["calories"]
            if calories > 0:
                diff_pct = abs(derived_calories - calories) / calories
                if diff_pct > 0.25 and len(calorie_warning_examples) < 20:
                    calorie_warning_examples.append(
                        {
                            "canonical_food_id": food_id,
                            "display_name": food.get("display_name"),
                            "label_calories_per_100g": calories,
                            "macro_derived_calories_per_100g": derived_calories,
                            "difference_percent": round(diff_pct * 100, 1),
                        }
                    )

    total = len(canonical_foods)
    return {
        "core_macro_names": list(CORE_MACROS),
        "complete_core_macro_foods": len(complete_food_ids),
        "missing_one_or_more_core_macro_foods": total - len(complete_food_ids),
        "complete_core_macro_percent": (
            round(len(complete_food_ids) * 100 / total, 1) if total else 0.0
        ),
        "optional_nutrient_counts": optional_counts,
        "suspicious_zero_macro_examples": suspicious_zero_examples,
        "macro_calorie_warning_examples": calorie_warning_examples,
        "incomplete_core_macro_examples": incomplete_examples,
    }


def _duplicate_risks(
    canonical_foods: list[dict[str, Any]],
    aliases_by_food_id: dict[int, list[str]],
) -> dict[str, Any]:
    normalized_name_counts = Counter(
        normalize_food_key(food.get("display_name")) for food in canonical_foods
    )
    duplicate_display_names = [
        {"normalized_name": name, "count": count}
        for name, count in sorted(normalized_name_counts.items())
        if name and count > 1
    ]

    near_duplicate_terms: list[dict[str, Any]] = []
    for term in NEAR_DUPLICATE_SEARCH_TERMS:
        normalized_term = normalize_food_key(term)
        matches = []
        for food in canonical_foods:
            food_id = int(food["id"])
            values = [food.get("display_name", "")]
            values.extend(aliases_by_food_id.get(food_id, []))
            if any(normalized_term in normalize_food_key(value) for value in values):
                matches.append(food.get("display_name"))
        unique_matches = sorted(set(matches))
        if len(unique_matches) > 1:
            near_duplicate_terms.append(
                {
                    "search_term": term,
                    "match_count": len(unique_matches),
                    "examples": unique_matches[:8],
                }
            )

    return {
        "exact_normalized_duplicate_display_names": duplicate_display_names[:20],
        "near_duplicate_search_terms": near_duplicate_terms[:20],
    }


def _staple_coverage(
    canonical_foods: list[dict[str, Any]],
    aliases_by_food_id: dict[int, list[str]],
    nutrient_by_food_id: dict[int, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    totals = {"present": 0, "missing": 0, "present_but_incomplete": 0}

    for category, staples in HIGH_VALUE_STAPLES.items():
        present: list[str] = []
        missing: list[str] = []
        present_but_incomplete: list[str] = []
        duplicate_risks: list[dict[str, Any]] = []
        for staple in staples:
            matches = _find_staple_matches(staple, canonical_foods, aliases_by_food_id)
            if not matches:
                missing.append(staple)
                continue
            present.append(staple)
            if len(matches) > 1:
                duplicate_risks.append(
                    {
                        "staple": staple,
                        "match_count": len(matches),
                        "examples": [
                            match.get("display_name") for match in matches[:8]
                        ],
                    }
                )
            if not any(
                all(
                    macro in nutrient_by_food_id.get(int(match["id"]), {})
                    for macro in CORE_MACROS
                )
                for match in matches
            ):
                present_but_incomplete.append(staple)

        totals["present"] += len(present)
        totals["missing"] += len(missing)
        totals["present_but_incomplete"] += len(present_but_incomplete)
        categories[category] = {
            "present": present,
            "missing": missing,
            "present_but_incomplete": present_but_incomplete,
            "duplicate_risks": duplicate_risks,
        }

    return {"totals": totals, "categories": categories}


def build_nutrition_catalog_diagnostic_summary(
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a read-only diagnostic summary of the nutrition catalog state."""

    db_path_resolved = str(Path(db_path) if db_path is not None else database.DB_PATH)
    conn = _connect(db_path)
    cursor = conn.cursor()

    tables = {
        "legacy_foods": _table_exists(cursor, "foods"),
        "legacy_nutrients": _table_exists(cursor, "nutrients"),
        "legacy_food_entries": _table_exists(cursor, "food_entries"),
        "canonical_foods": _table_exists(cursor, "canonical_foods"),
        "canonical_food_aliases": _table_exists(cursor, "canonical_food_aliases"),
        "canonical_food_nutrients": _table_exists(cursor, "canonical_food_nutrients"),
        "raw_food_source_records": _table_exists(cursor, "raw_food_source_records"),
        "food_source_links": _table_exists(cursor, "food_source_links"),
    }
    serving_unit_tables_present = [
        table for table in SERVING_UNIT_TABLE_CANDIDATES if _table_exists(cursor, table)
    ]

    canonical_foods = (
        _rows(cursor, "SELECT * FROM canonical_foods ORDER BY display_name")
        if tables["canonical_foods"]
        else []
    )
    canonical_nutrients = (
        _rows(cursor, "SELECT * FROM canonical_food_nutrients")
        if tables["canonical_food_nutrients"]
        else []
    )
    alias_rows = (
        _rows(cursor, "SELECT * FROM canonical_food_aliases")
        if tables["canonical_food_aliases"]
        else []
    )

    aliases_by_food_id: dict[int, list[str]] = defaultdict(list)
    for row in alias_rows:
        aliases_by_food_id[int(row["canonical_food_id"])].append(str(row["alias"]))

    nutrient_by_food_id = _nutrient_groups(canonical_nutrients)
    active_count = sum(1 for food in canonical_foods if int(food.get("active", 1)) == 1)
    inactive_count = len(canonical_foods) - active_count
    legacy_food_count = _count(cursor, "foods")
    raw_source_count = _count(cursor, "raw_food_source_records")
    user_created_foods = legacy_food_count
    canonical_mirror_count = 0
    if tables["legacy_foods"]:
        cursor.execute(
            "SELECT COUNT(*) AS count FROM foods WHERE name LIKE 'Canonical: %'"
        )
        canonical_mirror_count = int(cursor.fetchone()["count"])
        user_created_foods = max(0, legacy_food_count - canonical_mirror_count)

    legacy_food_entry_columns = _columns(cursor, "food_entries")
    canonical_food_columns = _columns(cursor, "canonical_foods")

    gram_default_count = sum(
        1
        for food in canonical_foods
        if str(food.get("default_unit", "")).strip().lower() == "grams"
    )
    default_grams_count = sum(
        1 for food in canonical_foods if food.get("default_grams") not in (None, "")
    )
    non_gram_default_count = sum(
        1
        for food in canonical_foods
        if str(food.get("default_unit", "")).strip().lower() not in {"", "grams"}
    )

    name_index = _food_name_index(canonical_foods, aliases_by_food_id)
    duplicate_risk_summary = _duplicate_risks(canonical_foods, aliases_by_food_id)
    macro_completeness = _macro_completeness(canonical_foods, nutrient_by_food_id)
    staple_coverage = _staple_coverage(
        canonical_foods, aliases_by_food_id, nutrient_by_food_id
    )

    suggestions_ready_foods = macro_completeness["complete_core_macro_foods"]
    has_alias_coverage = bool(canonical_foods) and all(
        aliases_by_food_id.get(int(food["id"])) for food in canonical_foods
    )
    serving_units_supported = bool(serving_unit_tables_present)

    conn.close()

    catalog_counts = {
        "database_path": db_path_resolved,
        "schema_tables_present": tables,
        "serving_unit_tables_present": serving_unit_tables_present,
        "total_legacy_food_records": legacy_food_count,
        "total_canonical_food_records": len(canonical_foods),
        "active_canonical_food_records": active_count,
        "inactive_canonical_food_records": inactive_count,
        "raw_source_food_records": raw_source_count,
        "user_created_or_legacy_food_records": user_created_foods,
        "canonical_foods_safe_for_logging": active_count,
        "canonical_foods_safe_for_suggestions": suggestions_ready_foods,
        "app_currently_has_single_legacy_food_table": tables["legacy_foods"],
        "app_currently_has_two_layer_food_tables": tables["canonical_foods"]
        and tables["raw_food_source_records"],
    }

    serving_unit_readiness = {
        "grams_supported_for_logging": "grams" in legacy_food_entry_columns,
        "canonical_default_unit_supported": "default_unit" in canonical_food_columns,
        "canonical_default_grams_supported": "default_grams" in canonical_food_columns,
        "serving_unit_model_or_table_present": serving_units_supported,
        "serving_unit_tables_present": serving_unit_tables_present,
        "household_units_supported": serving_units_supported,
        "foods_with_gram_default_unit": gram_default_count,
        "foods_with_default_grams": default_grams_count,
        "foods_with_non_gram_default_unit": non_gram_default_count,
        "foods_with_no_serving_unit_metadata": (
            len(canonical_foods) if not serving_units_supported else 0
        ),
        "status": (
            "ServingUnit model/table not present; current backend supports grams and "
            "canonical default_unit/default_grams only."
            if not serving_units_supported
            else (
                "Serving unit table detected; inspect table-specific "
                "coverage before use."
            )
        ),
    }

    alias_readiness = {
        "aliases_supported": tables["canonical_food_aliases"],
        "alias_rows": len(alias_rows),
        "foods_with_aliases": sum(
            1 for food in canonical_foods if aliases_by_food_id.get(int(food["id"]))
        ),
        "foods_without_aliases": sum(
            1 for food in canonical_foods if not aliases_by_food_id.get(int(food["id"]))
        ),
        "canonical_display_names_supported": tables["canonical_foods"],
        "normalized_names_supported": "normalized_name" in canonical_food_columns,
        "known_searchable_values": len(name_index),
        "status": (
            "Canonical aliases/search tokens are present."
            if tables["canonical_food_aliases"] and alias_rows
            else "Alias/search support is absent or empty."
        ),
    }

    logging_assumptions = {
        "food_entries_table_present": tables["legacy_food_entries"],
        "food_entries_columns": legacy_food_entry_columns,
        "uses_food_id_linkage": "food_id" in legacy_food_entry_columns,
        "uses_grams": "grams" in legacy_food_entry_columns,
        "uses_quantity_and_unit": {"quantity", "unit"}.issubset(
            legacy_food_entry_columns
        ),
        "uses_servings": "servings" in legacy_food_entry_columns,
        "uses_free_text_food_name": "food_name" in legacy_food_entry_columns,
        "uses_meal_grouping": "meal_id" in legacy_food_entry_columns,
        "uses_meal_type": "meal_type" in legacy_food_entry_columns,
        "uses_entry_date": "entry_date" in legacy_food_entry_columns,
        "uses_user_id": "user_id" in legacy_food_entry_columns,
        "macros_persisted_directly_on_logs": any(
            column in legacy_food_entry_columns
            for column in ("calories", "protein_g", "carbohydrate_g", "fat_g")
        ),
        "macros_recalculated_from_food_nutrients": tables["legacy_food_entries"]
        and tables["legacy_nutrients"],
        "current_summary": (
            "Food logs are grams-based and linked to legacy foods. Canonical "
            "logging uses write-through into legacy food/nutrient tables."
        ),
        "serving_units_representable_without_schema_change": False,
    }

    actuals_dependencies = {
        "daily_actuals_service": "services.nutrition_service.get_daily_nutrition",
        "target_vs_actual_service": (
            "services.nutrition_target_vs_actual_service."
            "build_target_vs_actual_nutrition_summary"
        ),
        "depends_on_tables": ["food_entries", "food_nutrients", "nutrients"],
        "actuals_assume_grams": logging_assumptions["uses_grams"],
        "macro_gaps_exist": True,
        "confidence_represented": False,
        "missing_logs_behavior": (
            "No rows aggregate to an empty nutrition actuals result; downstream "
            "target-vs-actual logic determines unavailable/zero display semantics."
        ),
        "estimated_serving_conversions_supported_later": (
            "Requires serving-unit and confidence model before estimated servings "
            "can be represented safely."
        ),
    }

    suggestion_readiness = {
        "deterministic_suggestion_service_present": True,
        "complete_macro_foods_available": suggestions_ready_foods,
        "active_canonical_foods_available": active_count,
        "serving_amounts_ready": serving_units_supported,
        "protein_carb_fat_groups_are_backend_derived": True,
        "common_snack_meal_coverage_present_count": staple_coverage["totals"][
            "present"
        ],
        "common_snack_meal_coverage_missing_count": staple_coverage["totals"][
            "missing"
        ],
        "confidence_source_present": False,
        "readiness": (
            "limited"
            if not serving_units_supported or not has_alias_coverage
            else "partial"
        ),
        "blockers": [
            blocker
            for blocker, active in (
                ("serving_unit_model_missing", not serving_units_supported),
                ("actuals_confidence_missing", True),
                ("source_confidence_not_catalog_level", True),
                (
                    "high_value_staple_gaps_exist",
                    staple_coverage["totals"]["missing"] > 0,
                ),
            )
            if active
        ],
    }

    provider_grounding_readiness = {
        "can_quote_actuals": True,
        "can_quote_targets": True,
        "can_quote_gaps": True,
        "can_quote_canonical_food_names": bool(canonical_foods),
        "can_use_serving_units_safely": serving_units_supported,
        "risk_of_invented_foods_or_macros": (
            "medium_until_serving_and_catalog_contracts_are_hardened"
        ),
        "validation_boundary_present": True,
        "readiness": "limited_until_serving_units_and_confidence_exist",
        "do_not_add_provider_behavior_in_this_milestone": True,
    }

    recommendations = [
        "Do not expand the catalog until Architecture reviews this diagnostic.",
        (
            "Treat ServingUnit/household conversion as a backend-owned "
            "model, not provider output."
        ),
        (
            "Add confidence/range semantics before exposing household "
            "measures as precise actuals."
        ),
    ]
    if not serving_units_supported:
        recommendations.append(
            "Prioritize canonical food model review or serving-unit data "
            "model before serving-based logging."
        )
    if staple_coverage["totals"]["missing"] > 0:
        recommendations.append(
            "Use missing high-value staples to scope Curated Food Catalog Expansion v1."
        )

    return {
        "catalog_summary": catalog_counts,
        "nutrient_completeness": macro_completeness,
        "serving_unit_readiness": serving_unit_readiness,
        "alias_search_readiness": alias_readiness,
        "high_value_staple_coverage": staple_coverage,
        "duplicate_near_duplicate_risks": duplicate_risk_summary,
        "logging_assumptions": logging_assumptions,
        "actuals_targets_dependencies": actuals_dependencies,
        "food_suggestion_readiness": suggestion_readiness,
        "ai_provider_grounding_readiness": provider_grounding_readiness,
        "recommended_next_steps": recommendations,
    }
