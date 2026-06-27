# Current State Update — Daily Coach Narrative Approved Value Quote Validation v1

Current source of truth: `main`.

Required source main commit: `f13a898`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_f13a898_daily-coach-narrative-value-aware-provider-comparison-v1.zip`.

Previous milestone status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`.

Current backend milestone: Daily Coach Narrative Approved Value Quote Validation v1.

Branch: `feature/daily-coach-narrative-approved-value-quote-validation-v1`.

Commit-check mode: code.

QA class: CLASS 5 / PROVIDER SAFETY + CLAIM VALIDATION.

Status: backend implementation in progress.

Requested final status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

## Goal

Add an explicit approved value claim registry and quote/value validation layer for Daily Coach value-aware provider narratives.

Provider output may quote deterministic backend values only when those values are:

- backend-approved;
- public-safe;
- present in `approved_value_claims`;
- marked `display_allowed=true`;
- declared by key in `quoted_values_used`;
- validated before rendering.

## Implemented direction

The Daily Coach narrative candidate contract now includes `quoted_values_used`.

The approved narrative contract also carries `quoted_values_used` for public-safe traceability.

The provider context includes `approved_value_claims` built from approved recovery, nutrition actuals, target/gap status, food suggestion, training/RIR, confidence, limitation, and recommendation context where available.

The validator checks both declared `quoted_values_used` and the narrative prose for obvious undeclared value claims such as numbers, grams, calories, percentages, scores, RIR ranges, readiness/fatigue statuses, serving amounts, and target/gap language.

## Scope boundaries

Deterministic remains default.

`direct_ollama` remains opt-in.

`openai` remains opt-in.

No live provider calls are allowed in automated tests.

No Streamlit provider controls are added.

No raw provider output is exposed.

No runtime metadata is exposed in the normal endpoint.

No provider narrative persistence is added.

No nutrition target, nutrition actual, food suggestion, workout, recovery, report, or schema behavior is changed.

No snapshots are committed.

## Architecture review step

Return to Architecture after implementation and validation.

Requested final status:

`DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.


## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- Provider Narrative QA Matrix v2
- Daily Coach Async Service Shell / No Worker v1
- Daily Coach Async Provider Runtime Design v1
- qwen3:32b research / future premium async candidate only
- deterministic fallback remains mandatory
- Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries
- AI explains backend-approved truth
- no provider on normal Today page load unless explicitly configured

## Historical continuity anchors — additional reference-only preservation

These phrases are preserved to avoid losing accepted historical continuity context:

- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- No provider may run on normal Today page load
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- service shell only
- no provider execution added
