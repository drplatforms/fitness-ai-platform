from __future__ import annotations

import json
import sqlite3
import subprocess
import sys

import database
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    seed_starter_canonical_foods,
)
from services.nutrition_catalog_diagnostic_service import (
    build_nutrition_catalog_diagnostic_summary,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _table_counts() -> dict[str, int]:
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    counts = {}
    for table in (
        "foods",
        "food_entries",
        "canonical_foods",
        "canonical_food_aliases",
        "canonical_food_nutrients",
        "raw_food_source_records",
    ):
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
        counts[table] = int(cursor.fetchone()["count"])
    conn.close()
    return counts


def test_diagnostic_runs_and_reports_catalog_counts(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    summary = build_nutrition_catalog_diagnostic_summary()

    assert summary["catalog_summary"]["total_canonical_food_records"] >= 200
    assert summary["catalog_summary"]["active_canonical_food_records"] >= 200
    assert summary["catalog_summary"]["app_currently_has_two_layer_food_tables"] is True
    assert "nutrient_completeness" in summary


def test_diagnostic_reports_nutrient_completeness_and_warnings(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Unit Test Partial Food", "generic")
    create_canonical_food_nutrient(food.id, "Calories", "kcal", 100)
    create_canonical_food_nutrient(food.id, "Protein", "g", 10)

    summary = build_nutrition_catalog_diagnostic_summary()
    completeness = summary["nutrient_completeness"]

    assert completeness["missing_one_or_more_core_macro_foods"] == 1
    assert completeness["incomplete_core_macro_examples"]
    assert completeness["incomplete_core_macro_examples"][0]["missing_core_macros"] == [
        "carbohydrates",
        "fat",
    ]


def test_diagnostic_reports_serving_units_as_unsupported_for_current_schema(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    summary = build_nutrition_catalog_diagnostic_summary()
    serving = summary["serving_unit_readiness"]

    assert serving["grams_supported_for_logging"] is True
    assert serving["canonical_default_unit_supported"] is True
    assert serving["serving_unit_model_or_table_present"] is False
    assert "ServingUnit model/table not present" in serving["status"]


def test_diagnostic_reports_high_value_staple_coverage_and_missing_items(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    summary = build_nutrition_catalog_diagnostic_summary()
    coverage = summary["high_value_staple_coverage"]

    assert "chicken breast" in coverage["categories"]["proteins"]["present"]
    assert "cooked white rice" in coverage["categories"]["carbs"]["present"]
    assert coverage["totals"]["present"] > 0
    assert "missing" in coverage["categories"]["convenience_snacks"]


def test_diagnostic_reports_duplicate_and_alias_readiness(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    first = create_canonical_food("Greek Yogurt, Plain", "generic")
    second = create_canonical_food("Greek Yogurt, Nonfat", "generic")
    create_canonical_food_alias(first.id, "greek yogurt")
    create_canonical_food_alias(second.id, "nonfat greek yogurt")

    summary = build_nutrition_catalog_diagnostic_summary()
    aliases = summary["alias_search_readiness"]
    duplicate_risks = summary["duplicate_near_duplicate_risks"]

    assert aliases["aliases_supported"] is True
    assert aliases["alias_rows"] == 2
    assert any(
        risk["search_term"] == "greek yogurt"
        for risk in duplicate_risks["near_duplicate_search_terms"]
    )


def test_diagnostic_reports_logging_and_suggestion_readiness(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    summary = build_nutrition_catalog_diagnostic_summary()

    logging = summary["logging_assumptions"]
    assert logging["uses_food_id_linkage"] is True
    assert logging["uses_grams"] is True
    assert logging["uses_quantity_and_unit"] is False
    assert logging["serving_units_representable_without_schema_change"] is False

    suggestions = summary["food_suggestion_readiness"]
    assert suggestions["deterministic_suggestion_service_present"] is True
    assert suggestions["complete_macro_foods_available"] >= 200
    assert "serving_unit_model_missing" in suggestions["blockers"]


def test_diagnostic_is_read_only(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    before_counts = _table_counts()

    build_nutrition_catalog_diagnostic_summary()

    assert _table_counts() == before_counts


def test_cli_json_mode_runs_without_provider_or_streamlit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    result = subprocess.run(
        [
            sys.executable,
            "tools/nutrition_catalog_diagnostic.py",
            "--json",
            "--db-path",
            str(database.DB_PATH),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["catalog_summary"]["total_canonical_food_records"] >= 200
    assert (
        payload["ai_provider_grounding_readiness"][
            "do_not_add_provider_behavior_in_this_milestone"
        ]
        is True
    )
