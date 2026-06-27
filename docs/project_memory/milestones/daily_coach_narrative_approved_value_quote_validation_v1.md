# Daily Coach Narrative Approved Value Quote Validation v1

Status: authorized for backend implementation.

Requested final status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

Source baseline: `main` at `f13a898`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_f13a898_daily-coach-narrative-value-aware-provider-comparison-v1.zip`.

## Purpose

Add an explicit quote/value validation fence for Daily Coach value-aware provider narratives.

Provider output may quote deterministic backend values only when they are approved, public-safe, present in the approved value registry, display-allowed, and declared in `quoted_values_used`.

## Accepted implementation shape

- `ApprovedNarrativeValueClaim` model records approved quoteable values.
- Provider context includes `approved_value_claims`.
- `CandidateDailyCoachValueNarrative` includes `quoted_values_used`.
- `ApprovedDailyCoachValueNarrative` includes `quoted_values_used`.
- Validator checks declared quoted values and scans narrative prose for undeclared numeric/status claims.
- Invalid quote/value claims fall back deterministically.

## Non-goals

No Streamlit changes.

No provider default changes.

No live provider calls in tests.

No provider narrative persistence.

No nutrition target, nutrition actual, food suggestion, workout, recovery, report, or schema behavior changes.

No snapshots committed by Backend.

## QA class

CLASS 5 / PROVIDER SAFETY + CLAIM VALIDATION.
