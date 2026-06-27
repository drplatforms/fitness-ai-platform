from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
    seed_canonical_food_serving_units,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    seed_canonical_food_serving_units()


def _client() -> TestClient:
    return TestClient(app)


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def test_serving_unit_discovery_returns_active_units_for_canonical_food(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")

    response = _client().get(f"/foods/canonical/{banana_id}/serving-units")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["canonical_food_id"] == banana_id
    assert payload["display_name"] == "Banana"
    assert payload["serving_units"]

    unit = payload["serving_units"][0]
    assert unit == {
        "serving_unit_id": unit["serving_unit_id"],
        "display_name": "1 medium banana",
        "unit_name": "medium banana",
        "unit_quantity": 1.0,
        "grams_default": 118.0,
        "grams_min": 100.0,
        "grams_max": 136.0,
        "confidence": "Moderate",
        "amount_source": "serving_unit_estimate",
        "source": "manually_curated_v1",
        "source_notes": "Common medium-banana edible portion estimate.",
        "sort_order": 10,
    }


def test_serving_unit_discovery_is_public_safe(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-secret",
        raw_description="Raw payload should not be exposed",
        source_payload={"private": True},
    )

    response = _client().get(f"/foods/canonical/{banana_id}/serving-units")

    assert response.status_code == 200
    payload = response.json()
    serialized = str(payload).lower()
    assert "source_payload_json" not in serialized
    assert "raw_source_record_id" not in serialized
    assert "private" not in serialized
    assert "traceback" not in serialized
    assert "sql" not in serialized


def test_serving_unit_discovery_excludes_inactive_serving_units(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")
    inactive_unit, _ = create_or_update_serving_unit(
        canonical_food_id=banana_id,
        unit_name="small banana",
        unit_quantity=1,
        display_name="1 small banana",
        grams_default=101,
        grams_min=90,
        grams_max=110,
        confidence="Moderate",
        active=False,
        sort_order=1,
    )

    response = _client().get(f"/foods/canonical/{banana_id}/serving-units")

    assert response.status_code == 200
    ids = {unit["serving_unit_id"] for unit in response.json()["serving_units"]}
    assert inactive_unit.id not in ids


def test_serving_unit_discovery_rejects_inactive_canonical_food(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    inactive_food = create_canonical_food(
        "Inactive Serving Unit Food",
        active=False,
    )
    create_or_update_serving_unit(
        canonical_food_id=inactive_food.id,
        unit_name="piece",
        unit_quantity=1,
        display_name="1 piece",
        grams_default=50,
        confidence="Moderate",
        active=True,
    )

    response = _client().get(f"/foods/canonical/{inactive_food.id}/serving-units")

    assert response.status_code == 404
    assert response.json()["detail"] == "Canonical food not found."


def test_serving_unit_discovery_missing_canonical_food_returns_safe_404(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/999999/serving-units")

    assert response.status_code == 404
    assert response.json()["detail"] == "Canonical food not found."


def test_serving_unit_discovery_returns_empty_list_for_food_without_units(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Unitless Test Food", active=True)

    response = _client().get(f"/foods/canonical/{food.id}/serving-units")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["canonical_food_id"] == food.id
    assert payload["display_name"] == "Unitless Test Food"
    assert payload["serving_units"] == []


def test_serving_unit_discovery_order_is_deterministic(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Ordering Test Food", active=True)
    later_unit, _ = create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="later",
        unit_quantity=1,
        display_name="later serving",
        grams_default=100,
        confidence="Moderate",
        active=True,
        sort_order=20,
    )
    earlier_unit, _ = create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="earlier",
        unit_quantity=1,
        display_name="earlier serving",
        grams_default=50,
        confidence="Moderate",
        active=True,
        sort_order=10,
    )

    response = _client().get(f"/foods/canonical/{food.id}/serving-units")

    assert response.status_code == 200
    ids = [unit["serving_unit_id"] for unit in response.json()["serving_units"]]
    assert ids == [earlier_unit.id, later_unit.id]


def test_serving_unit_discovery_preserves_existing_canonical_search(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/search?q=banana")

    assert response.status_code == 200
    assert response.json()["results"][0]["display_name"] == "Banana"
