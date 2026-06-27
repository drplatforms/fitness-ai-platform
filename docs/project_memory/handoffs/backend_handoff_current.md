# Backend Handoff Current — Daily Coach Narrative Value-Aware Provider Comparison v1

Recipient: Backend Development / Data Layer.

Current source of truth: `main` at `e1f7bd3`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_e1f7bd3_nutrition-actuals-provenance-debug-integration-design-v1.zip`.

Current milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Branch: `feature/daily-coach-narrative-provider-comparison-v1`.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Backend implementation summary

Backend added a provider-comparison path for Daily Coach narrative synthesis.

Normal route:

`GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`

Debug route:

`GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`

Provider options:

- deterministic default;
- `direct_ollama` opt-in;
- `openai` opt-in.

## Value-aware behavior

Provider candidates receive compact backend-approved value context and may quote approved values such as readiness, fatigue risk, nutrition actuals, macro status, food suggestion context, workout guidance, training context, limitations, and confidence.

Provider candidates are rejected if they quote values or claims that are not approved/display-safe.

## Runtime files changed

- `models/daily_coach_value_narrative_models.py`
- `services/daily_coach_value_narrative_service.py`
- `services/daily_coach_narrative_validation_service.py`
- `api/routes/daily_coach.py`
- `tests/test_daily_coach_value_narrative_service.py`
- `tests/test_daily_coach_value_narrative_api.py`

## Validation focus

Focused validation should include:

- targeted Ruff/Black checks on touched Python files;
- value-aware Daily Coach narrative service tests;
- value-aware Daily Coach narrative API tests;
- Daily Coach synthesis tests;
- existing Daily Coach narrative preview route tests;
- API smoke;
- project-memory checks.

## Scope boundaries

No Streamlit changes.

No nutrition actuals provenance debug endpoint behavior changes.

No nutrition logging behavior changes.

No Target-vs-Actual totals changes.

No workout/recommendation/report behavior changes.

No provider is enabled by default.

No snapshots committed.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
