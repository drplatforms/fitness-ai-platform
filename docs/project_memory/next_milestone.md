# Next Milestone — Daily Coach Narrative Approved Value Quote Validation v1

Current backend milestone: Daily Coach Narrative Approved Value Quote Validation v1.

Owner: Backend Development / Data Layer.

Secondary owner: Agent Engineering for provider/prompt/schema review.

Status: authorized for backend implementation.

Requested final status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

## Current accepted baseline

Current source of truth: `main`.

Required source main commit: `f13a898`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_f13a898_daily-coach-narrative-value-aware-provider-comparison-v1.zip`.

Previous status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`.

## Implementation focus

Add explicit quote/value validation for Daily Coach provider narratives:

- add approved value claim model/registry;
- add `approved_value_claims` to provider context;
- add `quoted_values_used` to candidate and approved narratives;
- require provider candidates to declare every quoted value;
- reject quoted values not present in the approved value registry;
- reject display-blocked values;
- scan prose for undeclared numbers/statuses/target/gap claims;
- fall back deterministically on quote/value validation failure.

## QA expectation

QA class: CLASS 5 / PROVIDER SAFETY + CLAIM VALIDATION.

Recommended QA: focused backend/API/provider-contract smoke with mocked providers.

Not required:

- full Streamlit workflow QA;
- live OpenAI calls;
- live Ollama calls;
- nutrition actuals full regression beyond adjacent focused tests;
- workout/recovery/report full QA.

## Post-acceptance routing

After Architecture acceptance, route focused QA for quote/value validation and provider-safety regression.

Potential follow-up: Daily Coach Narrative Provider Runtime Trial Matrix v1 or Developer Mode rendering of debug metadata.


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
