# QA Handoff Current

Milestone: Nutrition Serving Unit Data Model v1

QA status: scoped backend/data validation green with documented baseline full-suite exception.

Branch: `feature/nutrition-serving-unit-data-model-v1`.

## QA focus

Validate that serving-unit metadata exists, seeds safely, converts deterministically, and does not change user-facing nutrition logging or unrelated app behavior.

Primary checks:

- schema initializes safely;
- focused serving-unit tests pass;
- seed script runs on Windows;
- seed script runs on Linux;
- seed script is idempotent;
- active serving units are available for starter foods;
- conversion helper returns expected grams;
- serving units are linked to canonical foods;
- confidence is constrained;
- invalid grams/ranges are rejected;
- missing canonical foods are skipped safely;
- existing canonical search remains stable;
- existing canonical logging remains stable;
- Target-vs-Actual remains stable;
- no provider/Ollama/OpenAI/CrewAI is required;
- no Streamlit behavior changed.

## Expected validation

```powershell
git diff --check
python -m py_compile models/nutrition_serving_unit_models.py
python -m py_compile services/nutrition_serving_unit_service.py
python -m py_compile scripts/seed_canonical_food_serving_units.py
python -m py_compile tests/test_nutrition_serving_unit_data_model_v1.py
ruff check models/nutrition_serving_unit_models.py services/nutrition_serving_unit_service.py scripts/seed_canonical_food_serving_units.py tests/test_nutrition_serving_unit_data_model_v1.py
pytest tests/test_nutrition_serving_unit_data_model_v1.py -q
python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_first.json
python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_second.json
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q
scripts/dev_commit_check.ps1 -Mode code
```

Relevant nutrition/canonical tests should remain stable where present:

```powershell
pytest tests/test_nutrition_catalog_diagnostic_v1.py -q
pytest tests/test_food_normalization_service.py -q
pytest tests/test_food_canonical_search_api.py -q
pytest tests/test_canonical_food_logging_api.py -q
pytest tests/test_nutrition_target_vs_actual_service.py -q
```

## Seed smoke expected result

First run:

- inserted_count: 18
- active_serving_unit_count: 18
- foods_with_active_serving_units: 12
- missing_canonical_foods: []

Second run:

- inserted_count: 0
- updated_count: 18
- active_serving_unit_count: 18
- foods_with_active_serving_units: 12
- missing_canonical_foods: []

## Known baseline exception

Full pytest has 7 failures in unrelated Daily Coach / Daily Narrative tests that reproduce on source main `8b2c4c3`.

Known baseline failing files:

- `tests/test_daily_coach_narrative_preview_route.py`
- `tests/test_daily_narrative_rich_day_service.py`

Scoped full validation may exclude those files and document the exception.

## Browser smoke

Not required unless Streamlit/UI behavior changes.

Expected: no Streamlit/UI behavior changes.
