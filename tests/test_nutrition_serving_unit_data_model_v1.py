from __future__ import annotations

import sqlite3

import pytest

import database
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry, get_daily_nutrition
from services.nutrition_serving_unit_service import (
    DEFAULT_SERVING_UNIT_SEEDS,
    SERVING_UNIT_TABLE_NAME,
    count_active_serving_units,
    count_canonical_foods_with_active_serving_units,
    create_or_update_serving_unit,
    ensure_serving_unit_schema,
    estimate_grams_from_serving,
    estimate_nutrients_for_serving,
    find_serving_unit,
    get_active_serving_units_for_canonical_food,
    get_serving_units_for_canonical_food,
    seed_canonical_food_serving_units,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _seed_starter_foods(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    return seed_starter_canonical_foods()


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _table_exists(table_name: str) -> bool:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def test_serving_unit_schema_initializes_safely(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    ensure_serving_unit_schema()
    ensure_serving_unit_schema()

    assert _table_exists(SERVING_UNIT_TABLE_NAME)


def test_serving_unit_seed_is_idempotent_and_links_to_canonical_foods(
    tmp_path, monkeypatch
):
    _seed_starter_foods(tmp_path, monkeypatch)

    first_result = seed_canonical_food_serving_units()
    second_result = seed_canonical_food_serving_units()

    assert first_result.inserted_count >= 10
    assert second_result.inserted_count == 0
    assert second_result.updated_count == first_result.inserted_count
    assert second_result.skipped_count == 0
    assert second_result.missing_canonical_foods == []
    assert count_active_serving_units() == first_result.inserted_count
    assert count_canonical_foods_with_active_serving_units() >= 8
    assert all(
        unit.canonical_food_id > 0 for unit in second_result.seeded_serving_units
    )


def test_serving_unit_validation_rejects_bad_values(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    rice_id = _canonical_food_id("white rice")

    with pytest.raises(ValueError, match="grams_default"):
        create_or_update_serving_unit(
            canonical_food_id=rice_id,
            unit_name="cup",
            unit_quantity=1,
            display_name="bad cup",
            grams_default=0,
        )

    with pytest.raises(ValueError, match="grams_min"):
        create_or_update_serving_unit(
            canonical_food_id=rice_id,
            unit_name="cup",
            unit_quantity=1,
            display_name="bad range",
            grams_default=90,
            grams_min=100,
            grams_max=120,
        )

    with pytest.raises(ValueError, match="grams_max"):
        create_or_update_serving_unit(
            canonical_food_id=rice_id,
            unit_name="cup",
            unit_quantity=1,
            display_name="bad range",
            grams_default=130,
            grams_min=100,
            grams_max=120,
        )

    with pytest.raises(ValueError, match="confidence"):
        create_or_update_serving_unit(
            canonical_food_id=rice_id,
            unit_name="cup",
            unit_quantity=1,
            display_name="bad confidence",
            grams_default=90,
            confidence="Certain",
        )

    with pytest.raises(ValueError, match="known food"):
        create_or_update_serving_unit(
            canonical_food_id=999_999,
            unit_name="cup",
            unit_quantity=1,
            display_name="missing food",
            grams_default=90,
        )


def test_active_lookup_excludes_inactive_serving_units(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")

    active_unit, _ = create_or_update_serving_unit(
        canonical_food_id=banana_id,
        unit_name="medium banana",
        unit_quantity=1,
        display_name="1 medium banana",
        grams_default=118,
        grams_min=100,
        grams_max=136,
        confidence="Moderate",
        active=True,
        sort_order=10,
    )
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
        sort_order=20,
    )

    all_units = get_serving_units_for_canonical_food(banana_id)
    active_units = get_active_serving_units_for_canonical_food(banana_id)

    assert {unit.id for unit in all_units} == {active_unit.id, inactive_unit.id}
    assert [unit.id for unit in active_units] == [active_unit.id]


def test_conversion_helper_returns_expected_grams_and_range(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    seed_canonical_food_serving_units()
    peanut_butter_id = _canonical_food_id("peanut butter")
    tablespoon = next(
        unit
        for unit in get_active_serving_units_for_canonical_food(peanut_butter_id)
        if unit.display_name == "1 tablespoon peanut butter"
    )

    estimate = estimate_grams_from_serving(tablespoon.id, quantity=2)

    assert estimate.estimated_grams == 32
    assert estimate.grams_min == 28
    assert estimate.grams_max == 36
    assert estimate.confidence == "High"
    assert "serving_unit_backend_estimate" in estimate.reason_codes

    with pytest.raises(ValueError, match="greater than 0"):
        estimate_grams_from_serving(tablespoon.id, quantity=0)


def test_estimate_nutrients_for_serving_uses_canonical_per_100g(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Unit Test Food", default_grams=100)
    create_canonical_food_nutrient(food.id, "calories", "kcal", 200)
    create_canonical_food_nutrient(food.id, "protein", "g", 10)
    serving_unit, _ = create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="piece",
        unit_quantity=1,
        display_name="1 piece",
        grams_default=50,
        grams_min=45,
        grams_max=55,
        confidence="Moderate",
    )

    nutrients = estimate_nutrients_for_serving(food.id, serving_unit.id, quantity=2)

    assert nutrients["calories"] == {"amount": 200.0, "unit": "kcal"}
    assert nutrients["protein"] == {"amount": 10.0, "unit": "g"}

    other_food = create_canonical_food("Other Unit Test Food", default_grams=100)
    with pytest.raises(ValueError, match="does not belong"):
        estimate_nutrients_for_serving(other_food.id, serving_unit.id)


def test_seed_skips_missing_canonical_foods_safely(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    rice = create_canonical_food("White Rice, Cooked", default_grams=100)
    seed_specs = (
        DEFAULT_SERVING_UNIT_SEEDS[0],
        DEFAULT_SERVING_UNIT_SEEDS[-1],
    )

    result = seed_canonical_food_serving_units(seed_specs)

    assert result.inserted_count == 1
    assert result.skipped_count == 1
    assert result.missing_canonical_foods == ["Whey Protein Powder, Generic"]
    assert get_active_serving_units_for_canonical_food(rice.id)


def test_seed_does_not_change_grams_based_canonical_logging(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast cooked")

    before_response = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-26",
    )
    before_totals = get_daily_nutrition(1, "2026-06-26")

    seed_canonical_food_serving_units()
    after_response = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-27",
    )
    after_totals = get_daily_nutrition(1, "2026-06-27")

    assert before_response["grams"] == after_response["grams"] == 100.0
    assert before_response["nutrient_summary"] == after_response["nutrient_summary"]
    assert before_totals == after_totals


def test_database_check_constraints_guard_direct_sql_inserts(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    rice_id = _canonical_food_id("white rice")
    ensure_serving_unit_schema()

    conn = database.get_connection()
    cursor = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            f"""
            INSERT INTO {SERVING_UNIT_TABLE_NAME} (
                canonical_food_id,
                unit_name,
                normalized_unit_name,
                unit_quantity,
                display_name,
                grams_default,
                grams_min,
                grams_max,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rice_id,
                "cup",
                "cup",
                1,
                "bad direct insert",
                90,
                100,
                95,
                "Moderate",
            ),
        )
    conn.close()


def test_seeded_rice_egg_and_banana_units_are_retrievable(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    result = seed_canonical_food_serving_units()

    assert result.missing_canonical_foods == []

    rice_units = get_active_serving_units_for_canonical_food(
        _canonical_food_id("white rice")
    )
    egg_units = get_active_serving_units_for_canonical_food(_canonical_food_id("egg"))
    banana_units = get_active_serving_units_for_canonical_food(
        _canonical_food_id("banana")
    )

    assert {unit.display_name for unit in rice_units} >= {
        "1/2 cup cooked white rice",
        "1 cup cooked white rice",
    }
    assert {unit.display_name for unit in egg_units} >= {"1 large egg"}
    assert {unit.display_name for unit in banana_units} >= {"1 medium banana"}

    assert find_serving_unit(rice_units[0].id) is not None
