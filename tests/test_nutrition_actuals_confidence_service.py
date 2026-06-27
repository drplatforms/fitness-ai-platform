from __future__ import annotations

import database
from models.nutrition_actuals_confidence_models import (
    NUTRITION_ACTUAL_COMPLETENESS_COMPLETE,
    NUTRITION_ACTUAL_COMPLETENESS_PARTIAL,
    NUTRITION_ACTUAL_CONFIDENCE_HIGH,
    NUTRITION_ACTUAL_CONFIDENCE_LOW,
    NUTRITION_ACTUAL_CONFIDENCE_MODERATE,
    NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN,
    NUTRITION_ACTUAL_PRECISION_EXACT,
    NUTRITION_ACTUAL_PRECISION_LOW_CONFIDENCE,
    NUTRITION_ACTUAL_PRECISION_RANGED,
    NUTRITION_ACTUAL_PRECISION_UNKNOWN,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT,
    NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
    NUTRITION_ACTUAL_SOURCE_UNKNOWN,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_actuals_confidence_service import (
    build_nutrition_actual_interpretation,
    build_nutrition_actual_interpretations_for_date,
    build_public_nutrition_actual_interpretation,
)
from services.nutrition_service import (
    add_canonical_food_entry,
    add_food_entry,
)
from services.nutrition_serving_unit_logging_service import log_canonical_food_serving
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
    seed_canonical_food_serving_units,
)
from services.nutrition_target_vs_actual_service import build_nutrition_actuals


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
        WHERE canonical_food_id = ?
          AND display_name = ?
        """,
        (canonical_food_id, display_name),
    )
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    return int(row["id"])


def _create_legacy_food_with_core_nutrients(name: str) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO foods (name) VALUES (?)", (name,))
    food_id = int(cursor.lastrowid)
    nutrients = [
        ("Calories", "kcal", 100),
        ("Protein", "g", 10),
        ("Carbohydrates", "g", 20),
        ("Fat", "g", 5),
    ]
    for nutrient_name, unit, amount_per_100g in nutrients:
        cursor.execute(
            "INSERT OR IGNORE INTO nutrients (name, unit) VALUES (?, ?)",
            (nutrient_name, unit),
        )
        cursor.execute("SELECT id FROM nutrients WHERE name = ?", (nutrient_name,))
        nutrient_id = int(cursor.fetchone()["id"])
        cursor.execute(
            """
            INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
            VALUES (?, ?, ?)
            """,
            (food_id, nutrient_id, amount_per_100g),
        )
    conn.commit()
    conn.close()
    return food_id


def _create_complete_canonical_food(display_name: str):
    canonical_food = create_canonical_food(display_name, default_grams=100)
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 10)
    create_canonical_food_nutrient(canonical_food.id, "Carbohydrates", "g", 20)
    create_canonical_food_nutrient(canonical_food.id, "Fat", "g", 5)
    return canonical_food


def test_raw_grams_entry_classifies_as_raw_grams(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food_id = _create_legacy_food_with_core_nutrients("User Entered Oatmeal")
    food_entry_id = add_food_entry(
        user_id=1,
        food_id=food_id,
        grams=125,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(food_entry_id)

    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_RAW_GRAMS
    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_EXACT
    assert interpretation.confidence_level == NUTRITION_ACTUAL_CONFIDENCE_MODERATE
    assert (
        interpretation.nutrient_completeness == NUTRITION_ACTUAL_COMPLETENESS_COMPLETE
    )
    assert interpretation.resolved_grams == 125
    assert interpretation.has_serving_unit_metadata is False
    assert "raw_grams_entry" in interpretation.reason_codes
    assert "no_serving_unit_metadata" in interpretation.reason_codes


def test_canonical_grams_entry_classifies_as_canonical_grams(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    response = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=150,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(
        int(response["logged_food_entry_id"])
    )

    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS
    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_EXACT
    assert interpretation.confidence_level == NUTRITION_ACTUAL_CONFIDENCE_MODERATE
    assert interpretation.has_serving_unit_metadata is False
    assert interpretation.resolved_grams == 150
    assert "canonical_food_entry" in interpretation.reason_codes
    assert "user_entered_grams" in interpretation.reason_codes


def test_serving_unit_entry_classifies_as_canonical_serving_unit(
    tmp_path,
    monkeypatch,
):
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

    interpretation = build_nutrition_actual_interpretation(
        int(response["food_entry_id"])
    )

    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT
    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_RANGED
    assert interpretation.confidence_level == NUTRITION_ACTUAL_CONFIDENCE_HIGH
    assert interpretation.has_serving_unit_metadata is True
    assert interpretation.has_grams_range is True
    assert interpretation.resolved_grams == 169.5
    assert interpretation.grams_min == 165.0
    assert interpretation.grams_max == 174.0
    assert interpretation.grams_range_width == 9.0
    assert interpretation.grams_range_percent == 5.3
    assert interpretation.amount_source == "serving_unit_estimate"
    assert interpretation.serving_unit_confidence == "High"
    assert "serving_unit_entry" in interpretation.reason_codes
    assert "grams_range_available" in interpretation.reason_codes
    assert "resolved_grams_from_backend_serving_unit" in interpretation.reason_codes
    assert "show_serving_unit_provenance" in interpretation.display_flags


def test_wide_serving_unit_range_adds_limitation_and_reason_code(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = _create_complete_canonical_food("Wide Range Test Food")
    serving_unit, _ = create_or_update_serving_unit(
        canonical_food_id=canonical_food.id,
        unit_name="bowl",
        unit_quantity=1,
        display_name="1 bowl wide range food",
        grams_default=100,
        grams_min=50,
        grams_max=170,
        confidence="Moderate",
        source="unit_test",
        source_note="Wide bowl estimate for test.",
    )
    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=canonical_food.id,
        serving_unit_id=serving_unit.id,
        quantity=1,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(response["food_entry_id"])

    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_RANGED
    assert interpretation.grams_range_width == 120.0
    assert interpretation.grams_range_percent == 120.0
    assert "wide_serving_unit_range" in interpretation.reason_codes
    assert "Serving-size estimate has a wider gram range." in interpretation.limitations
    assert "show_wide_range_limitation" in interpretation.display_flags


def test_low_confidence_serving_unit_adds_limitation_and_reason_code(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = _create_complete_canonical_food("Low Confidence Test Food")
    serving_unit, _ = create_or_update_serving_unit(
        canonical_food_id=canonical_food.id,
        unit_name="piece",
        unit_quantity=1,
        display_name="1 piece low confidence food",
        grams_default=80,
        confidence="Low",
        source="unit_test",
        source_note="Low confidence piece estimate for test.",
    )
    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=canonical_food.id,
        serving_unit_id=serving_unit.id,
        quantity=1,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(response["food_entry_id"])

    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_LOW_CONFIDENCE
    assert interpretation.confidence_level == NUTRITION_ACTUAL_CONFIDENCE_LOW
    assert "low_confidence_serving_unit" in interpretation.reason_codes
    assert "Serving-unit confidence is limited." in interpretation.limitations
    assert "show_low_confidence_limitation" in interpretation.display_flags


def test_missing_serving_unit_metadata_does_not_crash_classification(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    response = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(
        response["logged_food_entry_id"]
    )

    assert interpretation.has_serving_unit_metadata is False
    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS
    assert "no_serving_unit_metadata" in interpretation.reason_codes


def test_missing_nutrient_values_are_missing_not_zero(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Protein Only Confidence Test Food")
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 20)
    response = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=canonical_food.id,
        grams=100,
        entry_date="2026-06-26",
    )

    interpretation = build_nutrition_actual_interpretation(
        response["logged_food_entry_id"]
    )

    assert interpretation.nutrient_completeness == NUTRITION_ACTUAL_COMPLETENESS_PARTIAL
    assert interpretation.missing_nutrients == ["calories", "carbs", "fat"]
    assert "missing_nutrient_values" in interpretation.reason_codes
    assert any("not treated as zero" in item for item in interpretation.limitations)
    public_payload = interpretation.to_public_dict()
    assert public_payload["missing_nutrients"] == ["calories", "carbs", "fat"]
    assert public_payload["resolved_grams"] == 100


def test_unknown_source_classifies_safely_for_missing_food_entry(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    interpretation = build_nutrition_actual_interpretation(999_999)

    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_UNKNOWN
    assert interpretation.precision == NUTRITION_ACTUAL_PRECISION_UNKNOWN
    assert interpretation.confidence_level == NUTRITION_ACTUAL_CONFIDENCE_UNKNOWN
    assert interpretation.resolved_grams is None
    assert "actual_source_unclassified" in interpretation.reason_codes
    assert "food_entry_not_found" in interpretation.reason_codes
    assert "Actual source could not be classified safely." in interpretation.limitations


def test_public_output_excludes_raw_source_sql_and_debug_fields(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")
    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-06-26",
    )

    payload = build_public_nutrition_actual_interpretation(response["food_entry_id"])

    forbidden_keys = {
        "source_payload_json",
        "raw_source_payload",
        "raw_sql",
        "sql",
        "debug_context",
        "traceback",
        "cursor",
        "db_row",
        "provider_runtime_metadata",
        "raw_ai_output",
    }
    assert forbidden_keys.isdisjoint(payload.keys())
    assert payload["source_type"] == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT
    assert payload["food_entry_id"] == response["food_entry_id"]


def test_interpretation_for_date_is_deterministically_ordered(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food_id = _create_legacy_food_with_core_nutrients("User Entered Rice")
    first_entry_id = add_food_entry(
        user_id=1,
        food_id=food_id,
        grams=50,
        entry_date="2026-06-26",
    )
    chicken_id = _canonical_food_id("chicken breast")
    second = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-26",
    )

    interpretations = build_nutrition_actual_interpretations_for_date(
        user_id=1,
        target_date="2026-06-26",
    )

    assert [item.food_entry_id for item in interpretations] == [
        first_entry_id,
        second["logged_food_entry_id"],
    ]
    assert [item.source_type for item in interpretations] == [
        NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
        NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
    ]


def test_interpretation_does_not_change_target_vs_actual_totals(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")
    response = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=2,
        entry_date="2026-06-26",
    )

    before = build_nutrition_actuals(user_id=1, target_date="2026-06-26")
    interpretation = build_nutrition_actual_interpretation(response["food_entry_id"])
    after = build_nutrition_actuals(user_id=1, target_date="2026-06-26")

    assert interpretation.source_type == NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT
    assert before == after
    assert after.logged_calories == 330.0
    assert after.logged_protein == 62.0
    assert after.logged_carbs == 0.0
    assert after.logged_fat == 7.2
