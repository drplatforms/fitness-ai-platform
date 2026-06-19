from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_food_entry, get_daily_nutrition


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _client() -> TestClient:
    return TestClient(app)


def _seed_chicken() -> int:
    seed_starter_canonical_foods()
    response = _client().get("/foods/canonical/search?q=chicken%20breast")
    assert response.status_code == 200
    return int(response.json()["results"][0]["canonical_food_id"])


def test_canonical_food_can_be_logged_by_canonical_food_id(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 150,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["logged_food_entry_id"] > 0
    assert payload["canonical_food_id"] == canonical_food_id
    assert payload["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert payload["grams"] == 150.0
    assert payload["logged_date"] == "2026-06-05"
    assert payload["nutrient_summary"] == {
        "calories": 247.5,
        "protein_g": 46.5,
        "carbohydrate_g": 0.0,
        "fat_g": 5.4,
    }
    assert "source_payload_json" not in payload


def test_inactive_canonical_food_cannot_be_logged(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    inactive_food = create_canonical_food(
        "Inactive Canonical Food",
        "generic",
        active=False,
    )
    create_canonical_food_nutrient(inactive_food.id, "Calories", "kcal", 100)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": inactive_food.id, "grams": 100},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Canonical food is inactive."


def test_missing_canonical_food_returns_safe_404(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": 99999, "grams": 100},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Canonical food not found."


def test_canonical_logging_requires_positive_grams(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food_id, "grams": 0},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "grams must be greater than 0."


def test_invalid_canonical_logging_date_is_safe_400(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "06/05/2026",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "entry_date must use YYYY-MM-DD format."


def test_missing_canonical_nutrients_remain_missing_not_zero(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Protein Only Test Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 20)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["nutrient_summary"] == {"protein_g": 20.0}

    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")
    assert nutrition["Protein"]["amount"] == 20.0
    assert "Calories" not in nutrition
    assert "Carbohydrates" not in nutrition
    assert "Fat" not in nutrition


def test_canonical_logged_foods_create_usable_logged_actuals(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 200,
            "entry_date": "2026-06-05",
        },
    )
    assert response.status_code == 200

    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")
    assert nutrition["Calories"]["amount"] == 330.0
    assert nutrition["Protein"]["amount"] == 62.0
    assert nutrition["Carbohydrates"]["amount"] == 0.0
    assert nutrition["Fat"]["amount"] == 7.2


def test_target_vs_actual_reflects_canonical_logged_foods(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 200,
            "entry_date": "2026-06-05",
        },
    )
    assert response.status_code == 200

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")

    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["entry_count"] == 1
    assert actuals["logged_calories"] == 330.0
    assert actuals["logged_protein"] == 62.0
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 7.2


def test_expanded_canonical_food_can_be_logged_and_counted(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=tuna")
    assert search_response.status_code == 200
    tuna_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": tuna_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Tuna, Canned in Water"
    assert response.json()["nutrient_summary"] == {
        "calories": 116.0,
        "protein_g": 25.5,
        "carbohydrate_g": 0.0,
        "fat_g": 0.8,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 116.0
    assert actuals["logged_protein"] == 25.5
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 0.8


def test_food_catalog_expansion_v1_new_canonical_food_can_be_logged(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=skyr")
    assert search_response.status_code == 200
    skyr_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": skyr_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Skyr, Plain Nonfat"
    assert response.json()["nutrient_summary"] == {
        "calories": 63.0,
        "protein_g": 11.0,
        "carbohydrate_g": 4.0,
        "fat_g": 0.2,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 63.0
    assert actuals["logged_protein"] == 11.0
    assert actuals["logged_carbs"] == 4.0
    assert actuals["logged_fat"] == 0.2


def test_existing_raw_source_nutrition_log_behavior_remains_stable(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES ('Legacy Rice')")
    cursor.execute("SELECT id FROM foods WHERE name = 'Legacy Rice'")
    food_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM nutrients WHERE name = 'Carbohydrates'")
    carbohydrate_id = cursor.fetchone()["id"]
    cursor.execute(
        """
        INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
        VALUES (?, ?, ?)
        """,
        (food_id, carbohydrate_id, 28.0),
    )
    conn.commit()
    conn.close()

    add_food_entry(user_id=1, food_id=food_id, grams=150, entry_date="2026-06-05")
    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")

    assert nutrition["Carbohydrates"]["amount"] == 42.0
    assert nutrition["Carbohydrates"]["unit"] == "g"


def test_canonical_logging_does_not_expose_raw_source_payloads(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Linked Canonical Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-private",
        raw_description="Verbose raw source record",
        source_payload={"private_payload": True},
    )

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food.id, "grams": 100},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "source_payload_json" not in payload
    assert "raw_description" not in payload


def test_v3_daily_staple_canonical_food_can_be_logged(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=ground%20turkey")
    assert search_response.status_code == 200
    turkey_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": turkey_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Turkey, Ground 93/7"
    assert response.json()["nutrient_summary"] == {
        "calories": 150.0,
        "protein_g": 22.0,
        "carbohydrate_g": 0.0,
        "fat_g": 7.0,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 150.0
    assert actuals["logged_protein"] == 22.0
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 7.0
