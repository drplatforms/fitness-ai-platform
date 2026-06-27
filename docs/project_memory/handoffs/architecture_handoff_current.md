# Architecture Handoff Current — Nutrition Actuals Provenance Debug / Integration Design v1

Recipient: Architecture.

CC: Backend Development / Data Layer, Streamlit UI, QA / Regression Testing, TPM / Project Control.

Current source of truth: `main` at `9b7430c`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_9b7430c_future-feature-technology-inventory-v1.zip`.

Milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Branch: `feature/nutrition-actuals-provenance-debug-integration-design-v1`.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Summary

Backend added a narrow public-safe debug/integration endpoint over the accepted Nutrition Actuals Provenance & Confidence Model service.

Implemented route:

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

## Architecture review request

Please review whether this is the correct first downstream integration surface for NutritionActualInterpretation.

The route is intended for QA, Architecture, Developer Mode planning, and future UI/API integration design.

It is not a normal user UI surface yet.

## Public-safe response

The route returns:

- actual interpretation records;
- reason_codes;
- limitations;
- display_flags;
- grams range metadata when available;
- summary counts.

It excludes raw SQL, raw source payloads, raw DB objects, tracebacks, provider/runtime metadata, private debug internals, validator internals, and raw AI output.

## Scope confirmation

No Target-vs-Actual totals changed.

No logging behavior changed.

No Streamlit changed.

No AI/provider changed.

No snapshots committed.

## Requested decision

Accept this backend/API/debug integration path as Nutrition Actuals Provenance Debug / Integration Design v1.

Requested status:

`NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
