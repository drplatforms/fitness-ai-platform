# Backend Handoff Current — Daily Coach Narrative Approved Value Quote Validation v1

Recipient: Architecture.

Current source of truth: `main` at `f13a898`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_f13a898_daily-coach-narrative-value-aware-provider-comparison-v1.zip`.

Previous milestone status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`.

Current milestone: Daily Coach Narrative Approved Value Quote Validation v1.

Branch: `feature/daily-coach-narrative-approved-value-quote-validation-v1`.

Status: backend implementation in progress / pending validation.

Requested final status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

## Backend implementation target

Add an approved value claim registry to the Daily Coach provider context and require provider candidates to declare every quoted backend value through `quoted_values_used`.

The validator must reject invented, display-blocked, undeclared, or unknown value claims and use deterministic fallback when quote/value validation fails.

## Likely runtime files

- `models/daily_coach_value_narrative_models.py`
- `services/daily_coach_value_narrative_service.py`
- `services/daily_coach_narrative_validation_service.py`
- `api/routes/daily_coach.py`
- `tests/test_daily_coach_value_narrative_service.py`
- `tests/test_daily_coach_value_narrative_api.py`

## Scope boundaries

No Streamlit changes.

No provider default changes.

No live provider calls in tests.

No nutrition/workout/recovery/report behavior changes.

No snapshots committed.


## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.

## Historical command/runtime anchors — required continuity phrases

The app` is now the canonical Linux runtime launcher.

Linux is the canonical FastAPI + Streamlit app runtime.
