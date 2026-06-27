# Next Milestone — Daily Coach Narrative Value-Aware Provider Comparison v1 Review

Current backend milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Owner: Backend Development / Data Layer.

Secondary owner: Agent Engineering for provider/prompt/schema review.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Current accepted baseline

Current source of truth: `main`.

Required source main commit: `e1f7bd3`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_e1f7bd3_nutrition-actuals-provenance-debug-integration-design-v1.zip`.

## Review focus

Architecture should review whether the new Daily Coach narrative value-aware provider comparison path:

- keeps deterministic as default;
- keeps `direct_ollama` opt-in;
- keeps `openai` opt-in;
- uses strict CandidateDailyCoachValueNarrative JSON parsing;
- validates provider candidates against `DailyCoachSynthesis` and approved values;
- allows approved recovery/nutrition/training values to be quoted only when provided;
- rejects recovery-missing claims when recovery context exists;
- rejects `without needing to address training or recovery`;
- rejects unapproved calorie-target/under-eating/exact-serving claims;
- preserves deterministic fallback;
- hides runtime metadata on the normal endpoint;
- exposes runtime metadata on the debug endpoint only;
- preserves nutrition/workout/report behavior.

## Implemented endpoints

Normal endpoint:

`GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`

Debug endpoint:

`GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`

## QA expectation

QA class: CLASS 2 / CLASS 5 HYBRID.

Recommended QA: focused backend/API/provider-contract smoke with mocked providers plus optional manual runtime provider comparison.

Not required:

- full Streamlit workflow QA;
- full nutrition actuals QA;
- full workout/recovery/report QA;
- live provider calls in pytest.

## Post-acceptance routing

After Architecture acceptance, route focused QA for backend/API provider-contract validation.

Future milestones may decide whether this narrative appears in Developer Mode, Today, or Daily Command Center. Normal Streamlit UI is unchanged in this milestone.


## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- Deterministic fallback remains mandatory
- AI candidate output must be parsed and validated before user display
- Backend facts remain the source of truth

## Historical continuity anchors — additional reference-only preservation

- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
