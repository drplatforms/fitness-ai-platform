from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from models.nutrition_actuals_confidence_models import (
    NUTRITION_ACTUAL_COMPLETENESS_PARTIAL,
    NUTRITION_ACTUAL_CONFIDENCE_HIGH,
    NUTRITION_ACTUAL_PRECISION_EXACT,
    NUTRITION_ACTUAL_PRECISION_RANGED,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
    NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT,
    NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry, add_food_entry
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


def _client() -> TestClient:
    return TestClient(app)


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
    for nutrient_name, unit, amount_per_100g in [
        ("Calories", "kcal", 100),
        ("Protein", "g", 10),
        ("Carbohydrates", "g", 20),
        ("Fat", "g", 5),
    ]:
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


def _create_protein_only_canonical_food():
    canonical_food = create_canonical_food("Protein Only Debug Food", default_grams=100)
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 20)
    return canonical_food


def test_actuals_confidence_debug_endpoint_returns_public_safe_user_date_payload(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    raw_food_id = _create_legacy_food_with_core_nutrients("Debug Raw Oatmeal")
    raw_entry_id = add_food_entry(
        user_id=1,
        food_id=raw_food_id,
        grams=125,
        entry_date="2026-06-26",
    )
    chicken_id = _canonical_food_id("chicken breast")
    canonical_entry = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=150,
        entry_date="2026-06-26",
    )
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    serving_entry = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1.5,
        entry_date="2026-06-26",
    )

    response = _client().get("/nutrition/1/actuals-confidence/debug?date=2026-06-26")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["date"] == "2026-06-26"
    assert [item["food_entry_id"] for item in payload["actuals"]] == [
        raw_entry_id,
        canonical_entry["logged_food_entry_id"],
        serving_entry["food_entry_id"],
    ]
    assert [item["source_type"] for item in payload["actuals"]] == [
        NUTRITION_ACTUAL_SOURCE_RAW_GRAMS,
        NUTRITION_ACTUAL_SOURCE_CANONICAL_GRAMS,
        NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT,
    ]
    assert payload["summary"] == {
        "total_entries": 3,
        "entries_with_serving_unit_metadata": 1,
        "entries_with_grams_range": 1,
        "entries_with_low_or_unknown_confidence": 0,
        "entries_with_missing_nutrients": 0,
    }

    serving_actual = payload["actuals"][2]
    assert serving_actual["precision"] == NUTRITION_ACTUAL_PRECISION_RANGED
    assert serving_actual["confidence_level"] == NUTRITION_ACTUAL_CONFIDENCE_HIGH
    assert serving_actual["has_serving_unit_metadata"] is True
    assert serving_actual["has_grams_range"] is True
    assert serving_actual["resolved_grams"] == 169.5
    assert serving_actual["grams_min"] == 165.0
    assert serving_actual["grams_max"] == 174.0
    assert serving_actual["grams_range_width"] == 9.0
    assert serving_actual["grams_range_percent"] == 5.3
    assert "serving_unit_entry" in serving_actual["reason_codes"]
    assert "grams_range_available" in serving_actual["reason_codes"]
    assert "show_serving_unit_provenance" in serving_actual["display_flags"]

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
    public_text = str(payload).lower()
    assert forbidden_keys.isdisjoint(payload.keys())
    assert not any(key in public_text for key in forbidden_keys)


def test_actuals_confidence_debug_endpoint_marks_missing_nutrients_not_zero(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = _create_protein_only_canonical_food()
    serving_unit, _ = create_or_update_serving_unit(
        canonical_food_id=canonical_food.id,
        unit_name="serving",
        unit_quantity=1,
        display_name="1 serving protein only debug food",
        grams_default=100,
        grams_min=80,
        grams_max=130,
        confidence="Moderate",
        source="unit_test",
        source_note="Protein-only debug serving estimate.",
    )
    log_canonical_food_serving(
        user_id=2,
        canonical_food_id=canonical_food.id,
        serving_unit_id=serving_unit.id,
        quantity=1,
        entry_date="2026-06-26",
    )

    response = _client().get("/nutrition/2/actuals-confidence/debug?date=2026-06-26")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["entries_with_missing_nutrients"] == 1
    actual = payload["actuals"][0]
    assert actual["nutrient_completeness"] == NUTRITION_ACTUAL_COMPLETENESS_PARTIAL
    assert actual["missing_nutrients"] == ["calories", "carbs", "fat"]
    assert "missing_nutrient_values" in actual["reason_codes"]
    assert any("not treated as zero" in item for item in actual["limitations"])
    assert actual["resolved_grams"] == 100.0
    assert actual["grams_min"] == 80.0
    assert actual["grams_max"] == 130.0


def test_actuals_confidence_debug_endpoint_returns_empty_day_safely(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/nutrition/999/actuals-confidence/debug?date=2026-06-26")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "user_id": 999,
        "date": "2026-06-26",
        "actuals": [],
        "summary": {
            "total_entries": 0,
            "entries_with_serving_unit_metadata": 0,
            "entries_with_grams_range": 0,
            "entries_with_low_or_unknown_confidence": 0,
            "entries_with_missing_nutrients": 0,
        },
    }


def test_actuals_confidence_debug_endpoint_rejects_invalid_date_safely(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/nutrition/1/actuals-confidence/debug?date=06/26/2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_actuals_confidence_debug_endpoint_does_not_change_target_vs_actual_totals(
    tmp_path,
    monkeypatch,
):
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
    before = build_nutrition_actuals(user_id=1, target_date="2026-06-26")

    response = _client().get("/nutrition/1/actuals-confidence/debug?date=2026-06-26")
    after = build_nutrition_actuals(user_id=1, target_date="2026-06-26")

    assert response.status_code == 200
    assert response.json()["actuals"][0]["source_type"] == (
        NUTRITION_ACTUAL_SOURCE_CANONICAL_SERVING_UNIT
    )
    assert before == after
    assert after.logged_calories == 330.0
    assert after.logged_protein == 62.0
    assert after.logged_carbs == 0.0
    assert after.logged_fat == 7.2


def test_actuals_confidence_debug_endpoint_preserves_logging_endpoints(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    raw_food_id = _create_legacy_food_with_core_nutrients("Debug Raw Rice")

    raw_response = _client().post(
        "/nutrition/log",
        json={"user_id": 1, "food_id": raw_food_id, "grams": 50},
    )
    canonical_response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": chicken_id,
            "grams": 100,
            "entry_date": "2026-06-26",
        },
    )
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    serving_response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 1,
            "logged_date": "2026-06-26",
        },
    )

    assert raw_response.status_code == 200
    assert canonical_response.status_code == 200
    assert serving_response.status_code == 200
    payload = (
        _client().get("/nutrition/1/actuals-confidence/debug?date=2026-06-26").json()
    )
    assert [item["precision"] for item in payload["actuals"]] == [
        NUTRITION_ACTUAL_PRECISION_EXACT,
        NUTRITION_ACTUAL_PRECISION_RANGED,
    ]
