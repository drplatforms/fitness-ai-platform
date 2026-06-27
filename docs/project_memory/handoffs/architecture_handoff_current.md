# Architecture Handoff Current — Daily Coach Narrative Value-Aware Provider Comparison v1

Recipient: Architecture.

CC: Backend Development / Data Layer, Agent Engineering, Streamlit UI, QA / Regression Testing, TPM / Project Control.

Current source of truth: `main` at `e1f7bd3`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_e1f7bd3_nutrition-actuals-provenance-debug-integration-design-v1.zip`.

Milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Branch: `feature/daily-coach-narrative-provider-comparison-v1`.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Summary

Backend added a strict provider-candidate comparison path for value-aware Daily Coach narrative synthesis.

Pattern implemented:

`DailyCoachSynthesis -> approved value context -> provider candidate JSON -> parser -> validator -> ApprovedDailyCoachValueNarrative -> deterministic renderer -> deterministic fallback`

## Endpoints

Normal endpoint:

`GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`

Debug endpoint:

`GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`

Normal endpoint hides runtime metadata.

Debug endpoint exposes public-safe runtime metadata and provider-context summary.

## Provider support

- deterministic default;
- `direct_ollama` opt-in;
- `openai` opt-in.

## Architecture review request

Please review whether this is the correct first value-aware provider comparison path for Daily Coach user-facing narrative content.

## Public-safe value context

Provider context may include approved recovery, nutrition, food-suggestion, workout, training/execution, limitation, and confidence values.

Provider candidates may quote only those approved values.

## Scope confirmation

No nutrition/debug endpoint behavior changed.

No Target-vs-Actual totals changed.

No logging behavior changed.

No Streamlit changed.

No report changed.

No provider enabled by default.

No snapshots committed.

## Requested decision

Accept this backend/API/provider comparison path as Daily Coach Narrative Value-Aware Provider Comparison v1.

Requested status:

`DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
