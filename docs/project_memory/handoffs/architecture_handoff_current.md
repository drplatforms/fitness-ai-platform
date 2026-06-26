# Architecture Handoff Current

Milestone: Nutrition Serving Unit Data Model v1

Status: implemented / scoped validation green / ready for Architecture review after feature snapshot.

Source baseline: `main` at `8b2c4c3`.

Branch: `feature/nutrition-serving-unit-data-model-v1`.

Milestone type: backend data model / service / seed script / tests / project memory update.

## Review focus

Architecture should review whether the backend-owned serving-unit model is sufficient as the foundation for future serving-based logging, deterministic food suggestions, and AI explanations.

Primary decisions:

- whether to accept Nutrition Serving Unit Data Model v1;
- whether `canonical_food_serving_units` is the correct persistence shape for v1;
- whether the confidence vocabulary `Low` / `Moderate` / `High` is acceptable;
- whether the starter seed set is sufficient for the next logging-contract design;
- whether Nutrition Serving Unit Logging Contract Design v1 should be next;
- whether Nutrition Actuals Confidence Model v1 should happen before serving-unit logging.

## Implementation summary

Added:

- `models/nutrition_serving_unit_models.py`
- `services/nutrition_serving_unit_service.py`
- `scripts/seed_canonical_food_serving_units.py`
- `tests/test_nutrition_serving_unit_data_model_v1.py`
- project-memory closeout docs

## Seed summary

Manual/backend seed smoke produced:

- first run inserted 18 serving units;
- second run inserted 0 and updated 18;
- active serving-unit count is 18;
- foods with active serving units is 12;
- missing canonical foods is empty.

Starter units cover rice, egg, banana, peanut butter, Greek yogurt, oats, chicken breast, olive oil, baked potato, apple, and whey protein powder.

## Scope preserved

No food logging behavior changed.

No user-facing serving-unit logging was added.

No Streamlit UI changed.

No Target-vs-Actual behavior changed.

No provider/Ollama/CrewAI behavior changed.

No catalog expansion, USDA import, meal planning, workout generation, recovery, or report behavior changed.

## Baseline exception

Full pytest has 7 unrelated Daily Coach / Daily Narrative failures that reproduce on source main `8b2c4c3`.

They are not caused by this serving-unit branch and were not fixed here because they are outside the milestone scope.

## Recommended next milestone

Recommended: Nutrition Serving Unit Logging Contract Design v1.

Purpose: design how serving-unit metadata should enter nutrition logging while preserving grams-based actuals, confidence, target-vs-actual safety, and auditability.

Alternative: Nutrition Actuals Confidence Model v1 if Architecture wants explicit confidence semantics before logging-contract design.

Proposed final status after successful closeout: `NUTRITION_SERVING_UNIT_DATA_MODEL_V1_ACCEPTED`.
