from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import get_daily_nutrition
from services.nutrition_serving_unit_logging_service import (
    get_serving_unit_log_metadata_for_food_entry,
)
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
    seed_canonical_food_serving_units,
)


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
        WHERE canonical_food_id = ? AND display_name = ?
        """,
        (canonical_food_id, display_name),
    )
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    return int(row["id"])


def test_log_serving_endpoint_succeeds_with_valid_request(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 1.5,
            "logged_date": "2026-06-26",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["user_id"] == 1
    assert body["food_entry_id"] == body["logged_food_entry_id"]
    assert body["canonical_food_id"] == chicken_id
    assert body["serving_unit_id"] == serving_unit_id
    assert body["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert body["serving_quantity"] == 1.5
    assert body["serving_display"] == "1.5 x 4 oz cooked chicken breast"
    assert body["resolved_grams"] == 169.5
    assert body["grams_min"] == 165.0
    assert body["grams_max"] == 174.0
    assert body["confidence"] == "High"
    assert body["amount_source"] == "serving_unit_estimate"
    assert body["logged_date"] == "2026-06-26"
    assert body["nutrient_summary"] == {
        "calories": 279.7,
        "protein_g": 52.5,
        "carbohydrate_g": 0.0,
        "fat_g": 6.1,
    }
    assert "source_payload_json" not in body
    assert "runtime_metadata" not in body
    assert "raw_provider_output" not in body

    metadata = get_serving_unit_log_metadata_for_food_entry(body["food_entry_id"])
    assert metadata is not None
    assert metadata.original_serving_display == "1.5 x 4 oz cooked chicken breast"


def test_log_serving_endpoint_rejects_missing_serving_unit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": 999_999,
            "quantity": 1,
            "logged_date": "2026-06-26",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Serving unit not found."


def test_log_serving_endpoint_rejects_wrong_food_serving_unit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    rice_id = _canonical_food_id("rice")
    rice_unit_id = _serving_unit_id(rice_id, "1 cup cooked white rice")

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": rice_unit_id,
            "quantity": 1,
            "logged_date": "2026-06-26",
        },
    )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]


def test_log_serving_endpoint_rejects_zero_quantity(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 0,
            "logged_date": "2026-06-26",
        },
    )

    assert response.status_code == 400
    assert "greater than 0" in response.json()["detail"]


def test_log_serving_endpoint_rejects_inactive_serving_unit(tmp_path, monkeypatch):
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

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": banana_id,
            "serving_unit_id": serving_unit.id,
            "quantity": 1,
            "logged_date": "2026-06-26",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Serving unit is inactive."


def test_log_serving_endpoint_preserves_existing_canonical_grams_logging(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": chicken_id,
            "grams": 150,
            "entry_date": "2026-06-26",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert body["grams"] == 150.0
    assert (
        get_serving_unit_log_metadata_for_food_entry(body["logged_food_entry_id"])
        is None
    )


def test_log_serving_endpoint_preserves_existing_raw_logging(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().post(
        "/nutrition/log",
        json={
            "user_id": 1,
            "food_id": 1,
            "grams": 50,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_log_serving_endpoint_updates_daily_nutrition_actuals(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "100g cooked chicken breast")

    response = _client().post(
        "/nutrition/1/log-serving",
        json={
            "canonical_food_id": chicken_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 2,
            "logged_date": "2026-06-26",
        },
    )
    assert response.status_code == 200

    nutrition = get_daily_nutrition(1, "2026-06-26")
    assert nutrition["Calories"]["amount"] == 330.0
    assert nutrition["Protein"]["amount"] == 62.0
    assert nutrition["Carbohydrates"]["amount"] == 0.0
    assert nutrition["Fat"]["amount"] == 7.2

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-26")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["entry_count"] == 1
    assert actuals["logged_calories"] == 330.0
    assert actuals["logged_protein"] == 62.0
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 7.2
