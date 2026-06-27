# Nutrition Actuals Provenance & Confidence Model v1

Status: backend implementation complete / ready for Architecture and focused QA review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_V1_ACCEPTED`.

Owner: Backend Development / Data Layer.

QA class: CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

## Baseline

Known accepted runtime/product baseline: `0ebb1b4 Nutrition Serving Unit Logging Streamlit UI v1`.

Known project-memory closeout feature commit: `d9a3906 Close Streamlit serving unit UI project memory`.

Canonical accepted product snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

## Purpose

Create a backend-owned interpretation layer for nutrition actuals confidence and provenance.

The service helps downstream nutrition features understand not just what grams were logged, but how reliable the logged actual is.

## Implemented files

- `models/nutrition_actuals_confidence_models.py`
- `services/nutrition_actuals_confidence_service.py`
- `tests/test_nutrition_actuals_confidence_service.py`

## Implemented service functions

- `build_nutrition_actual_interpretation(food_entry_id)`
- `build_nutrition_actual_interpretations_for_date(user_id, target_date)`
- `build_public_nutrition_actual_interpretation(food_entry_id)`

## Classification output

The interpretation model exposes:

- `food_entry_id`
- `user_id`
- `logged_date`
- `source_type`
- `precision`
- `confidence_level`
- `nutrient_completeness`
- `has_serving_unit_metadata`
- `has_grams_range`
- `resolved_grams`
- `grams_min`
- `grams_max`
- `grams_range_width`
- `grams_range_percent`
- `amount_source`
- `serving_unit_confidence`
- `missing_nutrients`
- `limitations`
- `reason_codes`
- `display_flags`

## Source types

- `raw_grams`
- `canonical_grams`
- `canonical_serving_unit`
- `unknown`

## Precision values

- `exact`
- `estimated`
- `ranged`
- `low_confidence`
- `unknown`

## Confidence values

- `high`
- `moderate`
- `low`
- `unknown`

## Nutrient completeness values

- `complete`
- `partial`
- `missing_nutrients`
- `unknown`

## Rules implemented

- Serving-unit metadata takes precedence for source classification.
- Canonical entries without serving-unit metadata classify as canonical grams.
- Legacy/user-entered entries without serving-unit metadata classify as raw grams.
- Missing/unclassifiable entries classify safely as unknown.
- Serving-unit gram ranges produce ranged precision.
- Wide serving-unit ranges produce public-safe limitations and reason codes.
- Low serving-unit confidence produces public-safe limitations and reason codes.
- Missing nutrient values remain missing/unknown and are not treated as zero.

## Public-safe boundary

Allowed output includes source type, precision, confidence level, completeness, resolved grams, grams range summary, reason codes, display flags, and limitations.

Disallowed output includes raw SQL rows, raw source payloads, provider runtime metadata, tracebacks, raw DB object dumps, internal validator internals, private debug context, and raw AI output.

## Scope boundaries

No Streamlit changes.

No Target-vs-Actual redesign.

No Target-vs-Actual total changes.

No macro target formula changes.

No logging endpoint behavior changes.

No AI/provider/CrewAI/direct_ollama changes.

No schema migration.

No snapshots committed.

## Validation

Sandbox validation:

- New focused tests: 11 passed.
- Adjacent focused nutrition/API/project-memory tests: 117 passed.
- Py compile for new model/service/test: PASS.

Ruff/Black were not available in the sandbox and should be run locally/Linux as targeted checks on the touched Python files.

## Follow-up direction

After Architecture acceptance and QA pass, future milestones may decide whether to expose actuals interpretation in Target-vs-Actual summaries, provider-safe nutrition context, or food suggestion logic.

No integration should begin without explicit Architecture authorization.
