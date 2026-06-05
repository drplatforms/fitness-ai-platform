import json

import database
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    get_aliases_for_canonical_food,
    get_nutrients_for_canonical_food,
    get_raw_food_source_record,
    get_source_links_for_canonical_food,
    link_canonical_food_to_source,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_food_entry, get_daily_nutrition


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def test_normalization_tables_initialize_safely(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    ensure_food_normalization_tables()

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name IN (
            'raw_food_source_records',
            'canonical_foods',
            'canonical_food_aliases',
            'canonical_food_nutrients',
            'food_source_links'
          )
        """
    )
    table_names = {row["name"] for row in cursor.fetchall()}
    conn.close()

    assert table_names == {
        "raw_food_source_records",
        "canonical_foods",
        "canonical_food_aliases",
        "canonical_food_nutrients",
        "food_source_links",
    }


def test_canonical_food_can_be_created(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    food = create_canonical_food(
        display_name="Chicken Breast, Cooked, Skinless",
        food_type="cooked",
        search_priority=10,
    )

    assert food.id is not None
    assert food.display_name == "Chicken Breast, Cooked, Skinless"
    assert food.normalized_name == "chicken breast cooked skinless"
    assert food.food_type == "cooked"
    assert food.default_unit == "grams"
    assert food.active is True


def test_canonical_aliases_can_be_created(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    alias = create_canonical_food_alias(food.id, "boneless chicken", priority=5)
    aliases = get_aliases_for_canonical_food(food.id)

    assert alias.canonical_food_id == food.id
    assert alias.normalized_alias == "boneless chicken"
    assert [stored.alias for stored in aliases] == ["boneless chicken"]


def test_canonical_nutrients_can_be_created(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    nutrient = create_canonical_food_nutrient(
        canonical_food_id=food.id,
        nutrient_name="Protein",
        nutrient_unit="g",
        amount_per_100g=31.0,
        source_policy="manually_curated",
        confidence="Moderate",
    )
    nutrients = get_nutrients_for_canonical_food(food.id)

    assert nutrient.amount_per_100g == 31.0
    assert nutrient.source_policy == "manually_curated"
    assert nutrient.confidence == "Moderate"
    assert [stored.nutrient_name for stored in nutrients] == ["Protein"]


def test_negative_canonical_nutrient_amount_is_rejected(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    try:
        create_canonical_food_nutrient(food.id, "Protein", "g", -1.0)
    except ValueError as exc:
        assert "cannot be negative" in str(exc)
    else:
        raise AssertionError("Expected negative canonical nutrient amount to fail.")


def test_raw_source_record_can_be_created_and_preserved(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    raw_record = create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="12345",
        raw_description="Chicken, broilers or fryers, breast, skinless, cooked",
        brand_name=None,
        food_category="Poultry Products",
        source_payload={"fdc_id": 12345, "raw": True},
        license="Public Domain",
        source_url="https://fdc.nal.usda.gov/fdc-app.html#/food-details/12345",
    )
    stored = get_raw_food_source_record(raw_record.id)

    assert stored is not None
    assert stored.source_name == "USDA FDC"
    assert stored.source_record_id == "12345"
    assert stored.raw_description == (
        "Chicken, broilers or fryers, breast, skinless, cooked"
    )
    assert stored.food_category == "Poultry Products"
    assert stored.license == "Public Domain"
    assert stored.source_url.endswith("12345")
    assert json.loads(stored.source_payload_json) == {"fdc_id": 12345, "raw": True}


def test_canonical_food_can_link_to_raw_source_record(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    raw_record = create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="12345",
        raw_description="Chicken, broilers or fryers, breast, skinless, cooked",
    )
    link = link_canonical_food_to_source(
        canonical_food_id=food.id,
        raw_food_source_record_id=raw_record.id,
        relationship_type="primary",
    )
    links = get_source_links_for_canonical_food(food.id)

    assert link.canonical_food_id == food.id
    assert link.raw_food_source_record_id == raw_record.id
    assert link.relationship_type == "primary"
    assert len(links) == 1
    assert links[0].raw_food_source_record_id == raw_record.id


def test_canonical_search_returns_display_name_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food(
        display_name="White Rice, Cooked",
        food_type="cooked",
        search_priority=10,
    )

    results = search_canonical_foods("white rice")

    assert results
    assert results[0].canonical_food.display_name == "White Rice, Cooked"
    assert results[0].matched_on == "display_name"


def test_canonical_search_returns_alias_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    create_canonical_food_alias(food.id, "boneless chicken", priority=5)

    results = search_canonical_foods("boneless chicken")

    assert results
    assert results[0].canonical_food.display_name == "Chicken Breast, Cooked, Skinless"
    assert results[0].matched_on == "alias"
    assert results[0].matched_value == "boneless chicken"


def test_canonical_search_ranks_higher_priority_foods_first(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food(
        "Chicken Breast, Cooked, Skinless", "cooked", search_priority=10
    )
    create_canonical_food("Chicken Breast, Raw, Skinless", "raw", search_priority=30)

    results = search_canonical_foods("chicken breast")

    assert [result.canonical_food.display_name for result in results[:2]] == [
        "Chicken Breast, Cooked, Skinless",
        "Chicken Breast, Raw, Skinless",
    ]


def test_duplicate_raw_records_do_not_create_duplicate_canonical_foods(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        "USDA FDC",
        "1001",
        "Chicken, breast, cooked, skinless, source variant A",
    )
    create_raw_food_source_record(
        "USDA FDC",
        "1002",
        "Chicken, breast, cooked, skinless, source variant B",
    )

    first = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    second = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM raw_food_source_records")
    raw_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) AS count FROM canonical_foods")
    canonical_count = cursor.fetchone()["count"]
    conn.close()

    assert raw_count == 2
    assert canonical_count == 1
    assert first.id == second.id


def test_starter_canonical_seed_is_small_and_idempotent(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    first_seed = seed_starter_canonical_foods()
    second_seed = seed_starter_canonical_foods()

    assert len(first_seed) == 15
    assert len(second_seed) == 15

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM canonical_foods")
    canonical_count = cursor.fetchone()["count"]
    conn.close()

    assert canonical_count == 15
    assert search_canonical_foods("egg")[0].canonical_food.display_name == "Egg, Large"


def test_existing_nutrition_logging_remains_stable(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES ('Legacy Chicken')")
    cursor.execute("SELECT id FROM foods WHERE name = 'Legacy Chicken'")
    food_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM nutrients WHERE name = 'Protein'")
    protein_id = cursor.fetchone()["id"]
    cursor.execute(
        """
        INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
        VALUES (?, ?, ?)
        """,
        (food_id, protein_id, 31.0),
    )
    conn.commit()
    conn.close()

    add_food_entry(user_id=1, food_id=food_id, grams=200)
    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")

    # add_food_entry uses today's runtime date; assert against whatever date was used
    # by checking the current totals for the generated entry if the fixed date differs.
    if not nutrition:
        from datetime import datetime

        nutrition = get_daily_nutrition(
            user_id=1,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
        )

    assert nutrition["Protein"]["amount"] == 62.0
    assert nutrition["Protein"]["unit"] == "g"
