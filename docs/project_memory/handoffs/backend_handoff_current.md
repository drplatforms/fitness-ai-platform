# Backend Handoff Current — Nutrition Actuals Provenance Debug / Integration Design v1

Recipient: Backend Development / Data Layer.

Current source of truth: `main` at `9b7430c`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_9b7430c_future-feature-technology-inventory-v1.zip`.

Current milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Branch: `feature/nutrition-actuals-provenance-debug-integration-design-v1`.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Backend implementation summary

Backend added the first debug/integration surface for NutritionActualInterpretation:

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

The route returns public-safe actuals confidence/provenance records for the requested user/date and summary counts for QA/Architecture inspection.

## Runtime files changed

- `api/routes/nutrition.py`
- `services/nutrition_actuals_confidence_service.py`
- `tests/test_nutrition_actuals_confidence_debug_api.py`

## Validation focus

Focused validation should include:

- targeted Ruff/Black checks on touched Python files;
- `tests/test_nutrition_actuals_confidence_service.py`;
- `tests/test_nutrition_actuals_confidence_debug_api.py`;
- serving-unit logging service/API regressions;
- canonical food logging/search regressions;
- Target-vs-Actual regressions;
- API smoke;
- project-memory checks.

## Scope boundaries

No Streamlit changes.

No logging behavior changes.

No Target-vs-Actual totals changes.

No AI/provider changes.

No snapshots committed.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
