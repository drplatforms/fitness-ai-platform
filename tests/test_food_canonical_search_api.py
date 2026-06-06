from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    link_canonical_food_to_source,
)
from services.nutrition_service import add_food_entry, get_daily_nutrition


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _client() -> TestClient:
    return TestClient(app)


def test_search_endpoint_returns_seeded_canonical_chicken_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/search?q=chicken breast")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["query"] == "chicken breast"
    assert payload["results"][0]["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert payload["results"][0]["matched_on"] in {"display_name", "alias"}
    assert payload["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 165.0,
        "protein_g_per_100g": 31.0,
        "carbohydrate_g_per_100g": 0.0,
        "fat_g_per_100g": 3.6,
    }
    assert "raw_description" not in payload["results"][0]
    assert "source_payload_json" not in payload["results"][0]


def test_search_endpoint_returns_common_seeded_foods(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    expected_by_query = {
        "rice": "White Rice, Cooked",
        "egg": "Egg, Large",
        "oats": "Oats, Dry",
    }

    for query, expected_name in expected_by_query.items():
        response = _client().get(f"/foods/canonical/search?q={query}")

        assert response.status_code == 200
        results = response.json()["results"]
        assert results
        assert results[0]["display_name"] == expected_name
        assert "nutrient_summary" in results[0]


def test_search_endpoint_returns_alias_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    create_canonical_food_alias(food.id, "boneless chicken", priority=5)

    response = _client().get("/foods/canonical/search?q=boneless chicken")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert result["matched_on"] == "alias"
    assert "boneless chicken" in result["aliases"]


def test_higher_priority_canonical_food_ranks_first(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Chicken Breast, Raw, Skinless", "raw", search_priority=30)
    create_canonical_food(
        "Chicken Breast, Cooked, Skinless", "cooked", search_priority=10
    )

    response = _client().get("/foods/canonical/search?q=chicken breast")

    assert response.status_code == 200
    results = response.json()["results"]
    assert [result["display_name"] for result in results[:2]] == [
        "Chicken Breast, Cooked, Skinless",
        "Chicken Breast, Raw, Skinless",
    ]


def test_search_results_are_bounded_by_limit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    for index in range(5):
        create_canonical_food(f"Test Food {index}", "generic", search_priority=index)

    response = _client().get("/foods/canonical/search?q=test&limit=2")

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_search_limit_is_capped_to_public_safe_maximum(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    for index in range(30):
        create_canonical_food(f"Search Food {index}", "generic", search_priority=index)

    response = _client().get("/foods/canonical/search?q=search&limit=100")

    assert response.status_code == 200
    assert len(response.json()["results"]) == 25


def test_inactive_foods_are_hidden_by_default(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Active Rice", "cooked", active=True, search_priority=10)
    create_canonical_food("Inactive Rice", "cooked", active=False, search_priority=1)

    response = _client().get("/foods/canonical/search?q=rice")

    assert response.status_code == 200
    names = [result["display_name"] for result in response.json()["results"]]
    assert "Active Rice" in names
    assert "Inactive Rice" not in names


def test_inactive_foods_can_be_requested_explicitly(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Inactive Rice", "cooked", active=False, search_priority=1)

    response = _client().get("/foods/canonical/search?q=rice&include_inactive=true")

    assert response.status_code == 200
    names = [result["display_name"] for result in response.json()["results"]]
    assert "Inactive Rice" in names


def test_raw_source_payloads_are_not_exposed(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    raw_record = create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="12345",
        raw_description="Chicken, source variant with verbose USDA description",
        source_payload={"private_raw_payload": True},
    )
    link_canonical_food_to_source(food.id, raw_record.id)

    response = _client().get(
        "/foods/canonical/search?q=chicken&include_source_links=true"
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert "source_payload_json" not in result
    assert "source_links" in result
    assert "source_payload_json" not in result["source_links"][0]
    assert result["source_links"][0]["source_name"] == "USDA FDC"


def test_raw_source_records_do_not_appear_as_default_user_facing_results(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-1",
        raw_description="Chicken, breast, duplicate-looking raw source record",
    )
    create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    response = _client().get("/foods/canonical/search?q=chicken")

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert results[0]["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert all("raw_source_record_id" not in result for result in results)
    assert all("source_payload_json" not in result for result in results)


def test_nutrient_summary_is_included_only_when_nutrients_exist(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    plain_food = create_canonical_food("Plain Test Food", "generic")
    chicken = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    create_canonical_food_nutrient(chicken.id, "Calories", "kcal", 165)
    create_canonical_food_nutrient(chicken.id, "Protein", "g", 31)
    create_canonical_food_nutrient(chicken.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(chicken.id, "Fat", "g", 3.6)

    chicken_response = _client().get("/foods/canonical/search?q=chicken")
    plain_response = _client().get("/foods/canonical/search?q=plain test")

    assert chicken_response.status_code == 200
    assert chicken_response.json()["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 165.0,
        "protein_g_per_100g": 31.0,
        "carbohydrate_g_per_100g": 0.0,
        "fat_g_per_100g": 3.6,
    }
    assert plain_response.status_code == 200
    assert plain_response.json()["results"][0]["canonical_food_id"] == plain_food.id
    assert "nutrient_summary" not in plain_response.json()["results"][0]


def test_empty_or_short_query_is_safe_and_deterministic(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    empty_response = _client().get("/foods/canonical/search?q=")
    short_response = _client().get("/foods/canonical/search?q=a")

    assert empty_response.status_code == 422
    assert short_response.status_code == 400
    assert short_response.json()["detail"] == (
        "q must be at least 2 characters for canonical food search."
    )


def test_nonexistent_query_returns_success_with_empty_results(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    response = _client().get("/foods/canonical/search?q=dragonfruit")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["results"] == []


def test_existing_nutrition_logging_remains_stable(tmp_path, monkeypatch):
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

    add_food_entry(user_id=1, food_id=food_id, grams=150)
    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")

    if not nutrition:
        from datetime import datetime

        nutrition = get_daily_nutrition(
            user_id=1,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
        )

    assert nutrition["Carbohydrates"]["amount"] == 42.0
    assert nutrition["Carbohydrates"]["unit"] == "g"
