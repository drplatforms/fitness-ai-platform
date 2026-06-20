from __future__ import annotations

import database
from services.food_normalization_service import (
    STARTER_CANONICAL_FOODS,
    get_nutrients_for_canonical_food,
    search_canonical_foods,
    seed_starter_canonical_foods,
)

FOOD_CATALOG_IMPORT_BATCH_V1_EXPECTED = {
    "pollock": "Alaska Pollock, Raw",
    "apricot": "Apricot, Raw",
    "arugula": "Arugula, Raw",
    "beets": "Beets, Raw",
    "beet greens": "Beet Greens, Raw",
    "bok choy": "Bok Choy, Raw",
    "red cabbage": "Red Cabbage, Raw",
    "collard greens": "Collard Greens, Raw",
    "fennel": "Fennel Bulb, Raw",
    "dried figs": "Figs, Dried",
    "haddock": "Haddock, Raw",
    "catfish": "Catfish, Raw",
    "plantain": "Plantain, Raw",
    "mandarin": "Mandarin, Raw",
    "black rice": "Black Rice, Dry",
    "red rice": "Red Rice, Dry",
    "fonio": "Fonio Grain, Dry",
    "khorasan": "Khorasan Grain, Dry",
    "parsnip": "Parsnips, Raw",
    "radish": "Radishes, Raw",
}


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()


def test_food_catalog_import_batch_v1_contains_exact_reviewed_row_count():
    batch_rows = [
        seed_food
        for seed_food in STARTER_CANONICAL_FOODS
        if "Food Catalog Import Batch v1" in seed_food.get("notes", "")
    ]

    assert len(batch_rows) == 20
    assert {row["display_name"] for row in batch_rows} == set(
        FOOD_CATALOG_IMPORT_BATCH_V1_EXPECTED.values()
    )


def test_food_catalog_import_batch_v1_rows_are_searchable_with_required_nutrients(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    for query, expected_name in FOOD_CATALOG_IMPORT_BATCH_V1_EXPECTED.items():
        results = search_canonical_foods(query)
        assert results, query
        assert results[0].canonical_food.display_name == expected_name

        nutrients = get_nutrients_for_canonical_food(results[0].canonical_food.id)
        nutrient_amounts = {
            nutrient.nutrient_name: nutrient.amount_per_100g for nutrient in nutrients
        }
        assert set(nutrient_amounts) >= {
            "Calories",
            "Protein",
            "Carbohydrate",
            "Fat",
        }
        assert 0 <= nutrient_amounts["Calories"] <= 900
        assert 0 <= nutrient_amounts["Protein"] <= 100
        assert 0 <= nutrient_amounts["Carbohydrate"] <= 100
        assert 0 <= nutrient_amounts["Fat"] <= 100


def test_food_catalog_import_batch_v1_rows_preserve_source_policy_and_confidence(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    results = search_canonical_foods("pollock")
    assert results
    assert results[0].canonical_food.display_name == "Alaska Pollock, Raw"
    assert "USDA FoodData Central Foundation Foods" in results[0].canonical_food.notes
    assert "fdc_id 2768188" in results[0].canonical_food.notes

    nutrients = get_nutrients_for_canonical_food(results[0].canonical_food.id)
    assert nutrients
    assert {nutrient.source_policy for nutrient in nutrients} == {"direct_source"}
    assert {nutrient.confidence for nutrient in nutrients} == {"High"}


def test_food_catalog_import_batch_v1_does_not_change_exercise_or_runtime_catalogs():
    # This milestone adds only canonical food seed rows. It intentionally does not
    # add exercise rows, runtime hooks, provider calls, or staged artifact fixtures.
    assert all(
        "exercise" not in seed_food["display_name"].lower()
        for seed_food in STARTER_CANONICAL_FOODS
    )
