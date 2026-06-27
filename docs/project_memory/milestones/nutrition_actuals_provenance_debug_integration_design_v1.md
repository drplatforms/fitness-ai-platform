# Nutrition Actuals Provenance Debug / Integration Design v1

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

Branch: `feature/nutrition-actuals-provenance-debug-integration-design-v1`.

Source baseline: `main` at `9b7430c`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_9b7430c_future-feature-technology-inventory-v1.zip`.

Owner: Backend Development / Data Layer.

QA class: CLASS 2 / CLASS 3 HYBRID.

## Purpose

Expose the accepted NutritionActualInterpretation model/service through a narrow public-safe backend debug/integration path.

This proves downstream use without changing normal user UI, Target-vs-Actual totals, logging behavior, or AI/provider behavior.

## Implemented endpoint

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

## Response shape

The response includes:

- success;
- user_id;
- date;
- actuals;
- summary.

Each actual is generated from the existing NutritionActualInterpretation model and exposes only public-safe fields.

Summary includes:

- total_entries;
- entries_with_serving_unit_metadata;
- entries_with_grams_range;
- entries_with_low_or_unknown_confidence;
- entries_with_missing_nutrients.

## Public-safe boundary

The endpoint does not expose raw SQL rows, raw source payloads, raw DB object dumps, tracebacks, provider/runtime metadata, raw AI output, validator internals, or hidden source blobs.

## Tests added

Added `tests/test_nutrition_actuals_confidence_debug_api.py` covering:

- user/date payload success;
- raw/canonical/serving-unit classification through API;
- serving-unit range metadata;
- summary counts;
- missing nutrients remain missing/unknown, not zero;
- empty day safe response;
- invalid date safe error;
- no raw/debug/source leakage;
- Target-vs-Actual totals unchanged;
- existing raw/canonical/serving logging endpoints remain stable.

## Scope confirmation

No Streamlit changes.

No logging behavior changes.

No Target-vs-Actual totals changes.

No AI/provider changes.

No snapshots committed.
