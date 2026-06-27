# Daily Coach Narrative Value-Aware Provider Comparison v1

Status: backend implementation complete / ready for Architecture review.

Requested final status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Purpose

Add an opt-in provider comparison path for value-aware Daily Coach narrative synthesis while keeping deterministic output as the default and backend-approved facts as the source of truth.

## Implemented pattern

`DailyCoachSynthesis -> approved value context -> provider candidate JSON -> strict parser -> backend validator -> ApprovedDailyCoachValueNarrative -> deterministic renderer -> deterministic fallback`

## Provider options

- deterministic default;
- direct_ollama opt-in;
- openai opt-in.

## Endpoints

- `GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`
- `GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`

## Value-aware correction

This milestone is not only tone/copy comparison.

Provider candidates receive compact backend-approved value context and may quote approved values when display-safe, including recovery readiness, fatigue risk, sleep/energy/soreness summary, nutrition actuals, macro target/gap status, food suggestions, workout guidance, training/execution context, limitations, and confidence.

## Acceptance guards

Provider output must fall back deterministically on:

- malformed JSON;
- extra or missing keys;
- markdown/code fences;
- invalid confidence;
- confidence mismatch with DailyCoachSynthesis;
- recovery-missing claims when recovery context exists;
- `without needing to address training or recovery`;
- unapproved under-eating claims;
- unapproved calorie-target claims;
- unapproved exact-serving claims;
- provider timeout/connection/exception;
- raw/debug/internal metadata leakage.

## Scope preserved

No Streamlit changes.

No nutrition logging changes.

No Target-vs-Actual changes.

No workout/recommendation/report changes.

No provider is enabled by default.

No snapshots committed.
