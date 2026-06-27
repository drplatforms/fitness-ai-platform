# Architecture Handoff Current

Milestone: Nutrition Actuals Provenance & Confidence Model v1

Branch: `feature/nutrition-actuals-provenance-confidence-model-v1`

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_V1_ACCEPTED`.

Known accepted runtime/product baseline: `0ebb1b4 Nutrition Serving Unit Logging Streamlit UI v1`.

Known project-memory closeout feature commit: `d9a3906 Close Streamlit serving unit UI project memory`.

Canonical accepted product snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

## Architecture review summary

Backend implemented the authorized narrow interpretation layer for nutrition actuals confidence/provenance.

The feature does not redesign Target-vs-Actual. It prepares future nutrition transparency/product work by producing public-safe interpretation objects for logged actual entries.

## Implemented contract

New model/service files:

- `models/nutrition_actuals_confidence_models.py`
- `services/nutrition_actuals_confidence_service.py`

Primary functions:

- `build_nutrition_actual_interpretation(food_entry_id)`
- `build_nutrition_actual_interpretations_for_date(user_id, target_date)`
- `build_public_nutrition_actual_interpretation(food_entry_id)`

Output distinguishes:

- raw grams entries;
- canonical grams entries;
- canonical serving-unit entries;
- unknown/unclassified entries;
- exact, estimated, ranged, low-confidence, and unknown precision;
- high/moderate/low/unknown confidence;
- complete, partial, missing, and unknown nutrient completeness.

## Public-safe boundary

The service exposes public-safe fields only:

- source type;
- precision;
- confidence level;
- resolved grams;
- optional grams range summary;
- nutrient completeness;
- reason codes;
- display flags;
- limitations.

It does not expose raw SQL rows, raw source payloads, provider runtime metadata, tracebacks, raw DB object dumps, validator internals, private debug context, or raw AI output.

## Scope confirmation

No Streamlit changes.

No logging behavior changes.

No Target-vs-Actual totals changes.

No API route changes.

No schema migration.

No AI/provider behavior changes.

No snapshots committed.

## Review request

Please review the v1 classification vocabulary, public-safe output contract, and focused tests.

Requested decision:

Accept Nutrition Actuals Provenance & Confidence Model v1 as the backend baseline for future actuals confidence/provenance interpretation.

## Historical continuity anchors

These phrases are reference-only for project-memory continuity:

- Local Command Menu App Runtime Correction v1
- app` is now the canonical Linux runtime launcher
- wapp
- Linux is the canonical FastAPI + Streamlit app runtime
