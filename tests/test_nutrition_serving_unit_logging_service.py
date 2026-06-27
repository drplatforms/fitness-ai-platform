from __future__ import annotations

import sqlite3

import pytest

import database
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import get_daily_nutrition
from services.nutrition_serving_unit_logging_service import (
    SERVING_UNIT_LOG_METADATA_TABLE_NAME,
    ServingUnitFoodMismatchError,
    ServingUnitInactiveError,
    ServingUnitNotFoundError,
    ServingUnitQuantityError,
    build_serving_unit_display,
    get_serving_unit_log_metadata_for_food_entry,
    log_canonical_food_serving,
    resolve_serving_unit_log_request,
)
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
    find_serving_unit,
    seed_canonical_food_serving_units,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    seed_starter_canonical_foods()
    seed_canonical_food_serving_units()


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _serving_unit_id(canonical_food_id: int, display_name: str) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM canonical_food_serving_units
        WHERE canonical_food_id = ? AND display_name = ?
        """,
        (canonical_food_id, display_name),
    )
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    return int(row["id"])


def _food_entry_row(food_entry_id: int) -> sqlite3.Row:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM food_entries WHERE id = ?", (food_entry_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    return row


def _metadata_table_rows() -> list[sqlite3.Row]:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {SERVING_UNIT_LOG_METADATA_TABLE_NAME}")
    rows = cursor.fetchall()
    conn.close()
    return list(rows)


def test_serving_unit_quantity_resolves_to_grams_and_range(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")

    resolved = resolve_serving_unit_log_request(
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1.5,
    )

    resolved_grams, grams_min, grams_max, confidence, serving_display = resolved
    assert resolved_grams == 169.5
    assert grams_min == 165.0
    assert grams_max == 174.0
    assert confidence == "High"
    assert serving_display == "1.5 x 4 oz cooked chicken breast"


def test_decimal_quantity_logs_resolved_grams_and_metadata(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")

    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1.5,
        entry_date="2026-06-26",
    )

    assert response["food_entry_id"] == response["logged_food_entry_id"]
    assert response["canonical_food_id"] == chicken_id
    assert response["serving_unit_id"] == serving_unit_id
    assert response["serving_quantity"] == 1.5
    assert response["resolved_grams"] == 169.5
    assert response["grams_min"] == 165.0
    assert response["grams_max"] == 174.0
    assert response["confidence"] == "High"
    assert response["amount_source"] == "serving_unit_estimate"
    assert response["logged_date"] == "2026-06-26"
    assert response["nutrient_summary"] == {
        "calories": 279.7,
        "protein_g": 52.5,
        "carbohydrate_g": 0.0,
        "fat_g": 6.1,
    }

    food_entry = _food_entry_row(response["food_entry_id"])
    assert food_entry["grams"] == 169.5
    assert food_entry["entry_date"] == "2026-06-26"

    metadata = get_serving_unit_log_metadata_for_food_entry(response["food_entry_id"])
    assert metadata is not None
    assert metadata.food_entry_id == response["food_entry_id"]
    assert metadata.user_id == 1
    assert metadata.canonical_food_id == chicken_id
    assert metadata.serving_unit_id == serving_unit_id
    assert metadata.serving_quantity == 1.5
    assert metadata.resolved_grams == 169.5
    assert metadata.grams_min == 165.0
    assert metadata.grams_max == 174.0
    assert metadata.serving_unit_confidence == "High"
    assert metadata.amount_source == "serving_unit_estimate"
    assert metadata.original_serving_display == "1.5 x 4 oz cooked chicken breast"
    assert metadata.source == "manually_curated_v1"
    assert (
        metadata.source_notes
        == "Ounce-to-gram serving estimate rounded for food logging."
    )


def test_serving_unit_logged_food_appears_in_daily_nutrition(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")

    log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=2,
        entry_date="2026-06-26",
    )

    nutrition = get_daily_nutrition(1, "2026-06-26")
    assert nutrition["Calories"]["amount"] == 330.0
    assert nutrition["Protein"]["amount"] == 62.0
    assert nutrition["Carbohydrates"]["amount"] == 0.0
    assert nutrition["Fat"]["amount"] == 7.2


def test_zero_and_negative_quantity_are_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")

    with pytest.raises(ServingUnitQuantityError, match="greater than 0"):
        log_canonical_food_serving(
            user_id=1,
            canonical_food_id=chicken_id,
            serving_unit_id=serving_unit_id,
            quantity=0,
        )

    with pytest.raises(ServingUnitQuantityError, match="greater than 0"):
        log_canonical_food_serving(
            user_id=1,
            canonical_food_id=chicken_id,
            serving_unit_id=serving_unit_id,
            quantity=-1,
        )


def test_missing_serving_unit_is_rejected_safely(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")

    with pytest.raises(ServingUnitNotFoundError, match="Serving unit not found"):
        log_canonical_food_serving(
            user_id=1,
            canonical_food_id=chicken_id,
            serving_unit_id=999_999,
            quantity=1,
        )


def test_inactive_serving_unit_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")
    serving_unit, _ = create_or_update_serving_unit(
        canonical_food_id=banana_id,
        unit_name="tiny banana",
        unit_quantity=1,
        display_name="1 tiny banana",
        grams_default=80,
        confidence="Low",
        active=False,
    )

    with pytest.raises(ServingUnitInactiveError, match="inactive"):
        log_canonical_food_serving(
            user_id=1,
            canonical_food_id=banana_id,
            serving_unit_id=serving_unit.id,
            quantity=1,
        )


def test_serving_unit_from_different_food_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    rice_id = _canonical_food_id("rice")
    rice_unit_id = _serving_unit_id(rice_id, "1 cup cooked white rice")

    with pytest.raises(ServingUnitFoodMismatchError, match="does not belong"):
        log_canonical_food_serving(
            user_id=1,
            canonical_food_id=chicken_id,
            serving_unit_id=rice_unit_id,
            quantity=1,
        )


def test_missing_optional_grams_range_remains_missing_not_zero(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    test_food = create_canonical_food("No Range Test Food", default_grams=100)
    create_canonical_food_nutrient(test_food.id, "Protein", "g", 10)
    unit, _ = create_or_update_serving_unit(
        canonical_food_id=test_food.id,
        unit_name="piece",
        unit_quantity=1,
        display_name="1 piece no range food",
        grams_default=50,
        grams_min=None,
        grams_max=None,
        confidence="Moderate",
        source="unit_test",
        source_note="No range test note.",
    )

    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=test_food.id,
        serving_unit_id=unit.id,
        quantity=2,
        entry_date="2026-06-26",
    )

    assert response["resolved_grams"] == 100.0
    assert response["grams_min"] is None
    assert response["grams_max"] is None
    metadata = get_serving_unit_log_metadata_for_food_entry(response["food_entry_id"])
    assert metadata is not None
    assert metadata.grams_min is None
    assert metadata.grams_max is None
    nutrition = get_daily_nutrition(1, "2026-06-26")
    assert nutrition["Protein"]["amount"] == 10.0
    assert "Calories" not in nutrition


def test_original_serving_display_builder_preserves_one_quantity():
    assert build_serving_unit_display(1, "1 large egg") == "1 large egg"
    assert build_serving_unit_display(2, "1 large egg") == "2 large egg"
    assert build_serving_unit_display(1.5, "4 oz cooked chicken breast") == (
        "1.5 x 4 oz cooked chicken breast"
    )


def test_metadata_table_contains_only_public_safe_provenance(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")

    log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-06-26",
    )

    rows = _metadata_table_rows()
    assert len(rows) == 1
    keys = set(rows[0].keys())
    assert "source_payload_json" not in keys
    assert "raw_provider_output" not in keys
    assert "ai_metadata" not in keys
    assert find_serving_unit(serving_unit_id) is not None
