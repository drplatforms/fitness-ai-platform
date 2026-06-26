# Nutrition Serving Unit Data Model v1

Status: implemented / validation green with documented baseline exception / ready for Architecture review after feature snapshot.

Branch: `feature/nutrition-serving-unit-data-model-v1`.

Source baseline: `main` at `8b2c4c3`.

Milestone type: backend data model / service / seed script / tests / project memory update.

## Purpose

Nutrition Catalog Diagnostic v1 showed that the canonical nutrition catalog is stronger than expected, but serving-unit and confidence infrastructure is absent.

This milestone adds backend-owned serving-unit metadata so future nutrition logging, suggestions, and AI explanations can reference practical household units without AI inventing conversions.

## Implementation summary

Added:

- `models/nutrition_serving_unit_models.py`
- `services/nutrition_serving_unit_service.py`
- `scripts/seed_canonical_food_serving_units.py`
- `tests/test_nutrition_serving_unit_data_model_v1.py`

The v1 service adds a `canonical_food_serving_units` persistence layer and deterministic helpers for schema initialization, seed upsert, active lookup, single-unit lookup, grams estimation, and nutrient estimation.

## Data model summary

Serving units are linked to canonical foods and include:

- canonical food id
- unit name
- unit quantity
- display name
- grams default
- grams min
- grams max
- confidence
- source/source note
- user override flag
- active state
- sort order
- created/updated timestamps

Confidence vocabulary used:

- `Low`
- `Moderate`
- `High`

## Seed summary

Manual/backend seed smoke produced:

- first run inserted: 18 serving units
- second run inserted: 0 serving units
- second run updated: 18 serving units
- skipped: 0
- active serving-unit count: 18
- foods with active serving units: 12
- missing canonical foods: none

Starter foods covered:

- cooked white rice
- cooked brown rice
- egg, large
- banana
- peanut butter
- Greek yogurt, plain
- oats, dry
- chicken breast, cooked, skinless
- olive oil
- potato, baked
- apple
- whey protein powder

## Conversion examples

- 1/2 cup cooked white rice -> about 90g, range 80g..100g, confidence Moderate
- 1 large egg -> about 50g, range 45g..55g, confidence High
- 1 medium banana -> about 118g, range 100g..136g, confidence Moderate
- 1 tablespoon peanut butter -> about 16g, range 14g..18g, confidence High
- 4 oz cooked chicken breast -> about 113g, range 110g..116g, confidence High
- 1 scoop whey protein powder -> about 30g, range 25g..35g, confidence Moderate

## Scope boundaries preserved

This milestone did not:

- change `/nutrition/log` behavior
- allow users to log by serving unit
- modify Streamlit nutrition logging UI
- modify Target-vs-Actual calculations
- modify nutrition target formula behavior
- modify nutrition food suggestions
- modify Daily Coach synthesis
- modify provider/Ollama/CrewAI behavior
- add AI serving inference
- add meal planning
- import USDA/source data
- expand canonical foods broadly
- change workout generation
- change recovery logic

## Validation summary

Focused and scoped validation passed:

- serving-unit model/service/seed tests
- seed idempotency smoke
- nutrition/catalog related tests
- project memory checks after closeout
- commit-check mode: code

Full-suite baseline exception:

- 7 unrelated Daily Coach / Daily Narrative tests fail on source main `8b2c4c3`.
- These failures reproduce on the source baseline and are not caused by this serving-unit branch.
- They were not fixed in this milestone because Daily Coach / Daily Narrative behavior is outside scope.

Known baseline-failing files:

- `tests/test_daily_coach_narrative_preview_route.py`
- `tests/test_daily_narrative_rich_day_service.py`

## Recommended next milestone

Recommended: Nutrition Serving Unit Logging Contract Design v1.

Purpose:

Design how serving-unit metadata should enter food logging without corrupting grams-based actuals.

Questions for the next milestone:

- Should logs store `serving_unit_id`?
- Should logs store original quantity/unit plus resolved grams?
- Should logs store grams default/min/max used at time of logging?
- Should logs preserve confidence source?
- How should weighed vs estimated entries display in Target-vs-Actual?
- How should user overrides work?
- Should serving-unit entries be editable after logging?

Alternative: Nutrition Actuals Confidence Model v1 if Architecture wants confidence semantics before logging-contract design.
