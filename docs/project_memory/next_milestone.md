# Next Milestone

Current milestone in progress: Nutrition Serving Unit Data Model v1.

Recommended branch: `feature/nutrition-serving-unit-data-model-v1`.

Source branch: `main`.

Required source main commit: `8b2c4c3`.

Milestone type: backend data model / service / tests / project memory update.

## Objective

Add backend-owned serving-unit metadata for canonical foods so future nutrition logging, food suggestions, and AI explanations can safely reference practical household units without AI inventing grams, macros, or conversions.

The milestone creates trusted metadata only. Normal nutrition logging remains grams-first and unchanged.

## Implemented behavior

Implemented files:

- `models/nutrition_serving_unit_models.py`
- `services/nutrition_serving_unit_service.py`
- `scripts/seed_canonical_food_serving_units.py`
- `tests/test_nutrition_serving_unit_data_model_v1.py`

Implemented concepts:

- serving-unit model/dataclass layer
- serving-unit schema/table initialization
- canonical-food-linked serving units
- positive grams/default range validation
- constrained confidence vocabulary: Low, Moderate, High
- deterministic lookup helpers
- deterministic gram conversion helper
- deterministic nutrient estimate helper
- idempotent starter seed behavior

## Seed smoke result

Windows seed smoke produced:

- first run inserted: 18
- second run inserted: 0
- second run updated: 18
- skipped: 0
- active serving-unit count: 18
- foods with active serving units: 12
- missing canonical foods: []

Seeded examples:

- 1/2 cup cooked white rice: 90g, range 80-100g, Moderate
- 1 cup cooked white rice: 180g, range 160-200g, Moderate
- 1 large egg: 50g, range 45-55g, High
- 1 medium banana: 118g, range 100-136g, Moderate
- 1 tablespoon peanut butter: 16g, range 14-18g, High
- 1 cup Greek yogurt, plain: 245g, range 225-265g, Moderate
- 1/2 cup dry oats: 40g, range 35-45g, High
- 100g cooked chicken breast: 100g, range 100-100g, High
- 4 oz cooked chicken breast: 113g, range 110-116g, High
- 1 tablespoon olive oil: 14g, range 13-15g, High
- 1 medium baked potato: 173g, range 150-200g, Moderate
- 1 medium apple: 182g, range 160-205g, Moderate
- 1 scoop whey protein powder: 30g, range 25-35g, Moderate

## Known baseline validation exception

Full pytest on source main `8b2c4c3` has 7 unrelated Daily Coach / Daily Narrative failures.

Affected baseline files:

- `tests/test_daily_coach_narrative_preview_route.py`
- `tests/test_daily_narrative_rich_day_service.py`

These failures reproduced on source main before serving-unit changes and are not caused by this milestone. Do not fix those files inside this milestone unless Architecture explicitly authorizes a separate Daily Coach / Daily Narrative baseline repair.

Scoped serving-unit validation is expected to pass. Full-suite validation should either document the known baseline exception or run with those known baseline-failing files excluded until the separate baseline repair happens.

## Strict non-goals

Do not change `/nutrition/log` behavior yet.

Do not allow users to log food by serving unit yet.

Do not modify Streamlit nutrition logging UI.

Do not modify Target-vs-Actual calculations.

Do not modify nutrition target formula behavior.

Do not modify nutrition food suggestion behavior.

Do not modify Daily Coach synthesis behavior.

Do not modify AI nutrition explanation behavior.

Do not modify provider/Ollama/CrewAI behavior.

Do not add meal planning.

Do not add barcode scanning.

Do not import USDA/source data.

Do not expand the canonical food catalog broadly.

Do not change workout generation.

Do not change recovery logic.

Do not commit snapshots, qa_artifacts, local JSON/text seed output, patch files, or apply scripts.

Do not use `git add .`.

## Validation

```powershell
git diff --check

python -m py_compile models/nutrition_serving_unit_models.py
python -m py_compile services/nutrition_serving_unit_service.py
python -m py_compile scripts/seed_canonical_food_serving_units.py
python -m py_compile tests/test_nutrition_serving_unit_data_model_v1.py
python -m py_compile ui/streamlit_app.py

ruff check models/nutrition_serving_unit_models.py services/nutrition_serving_unit_service.py scripts/seed_canonical_food_serving_units.py tests/test_nutrition_serving_unit_data_model_v1.py

pytest tests/test_nutrition_serving_unit_data_model_v1.py -q
pytest tests/test_nutrition_catalog_diagnostic_v1.py -q
pytest tests/test_project_memory_check.py -q

python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_first.json
python scripts/seed_canonical_food_serving_units.py --output ..\nutrition_serving_unit_seed_v1_second.json

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief

scripts/dev_commit_check.ps1 -Mode code
```

## Recommended next milestone after acceptance

Recommended: Nutrition Serving Unit Logging Contract Design v1.

Purpose: design how serving-unit metadata should enter food logging without corrupting grams-based actuals.

Questions to answer later:

- Should logs store `serving_unit_id`?
- Should logs store original quantity/unit plus resolved grams?
- Should logs store grams_default used at the time of logging?
- Should logs preserve grams_min/grams_max?
- Should logs preserve confidence/source?
- How should Target-vs-Actual display estimated vs weighed entries?
- How should user overrides work?
- Should serving-unit entries be editable after logging?
- How should canonical-food logging endpoint accept serving units?

Alternative next milestone: Nutrition Actuals Confidence Model v1.
