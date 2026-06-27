# Next Milestone — Nutrition Actuals Provenance Debug / Integration Design v1 Review

Current backend milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Owner: Backend Development / Data Layer.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_DEBUG_INTEGRATION_DESIGN_V1_ACCEPTED`.

## Current accepted baseline

Current source of truth: `main`.

Required source main commit: `9b7430c`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_9b7430c_future-feature-technology-inventory-v1.zip`.

Previous technical milestone: Nutrition Actuals Provenance & Confidence Model v1.

Previous technical QA result: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_QA_V1_PASS`.

Previous docs milestone: Future Feature & Technology Inventory v1.

Previous docs status: `FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED_AND_MERGED`.

## Review focus

Architecture should review whether the new debug/integration endpoint:

- reuses the accepted NutritionActualInterpretation service;
- returns public-safe user/date actuals confidence/provenance records;
- includes useful summary counts;
- handles empty days safely;
- validates date input safely;
- excludes raw/debug/source/provider internals;
- preserves logging behavior;
- preserves Target-vs-Actual totals;
- avoids Streamlit changes;
- avoids AI/provider behavior changes.

## Implemented endpoint

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

## QA expectation

QA class: CLASS 2 / CLASS 3 HYBRID.

Recommended QA: focused backend/API/debug contract and semantics smoke.

Not required:

- full Streamlit workflow QA;
- full AI/provider QA;
- full workout/recovery/report QA.

## Post-acceptance routing

After Architecture acceptance, route focused QA for backend/API/debug contract validation.

Future milestones may decide whether these interpretations surface in Developer Mode, Target-vs-Actual confidence notes, Nutrition Today Summary annotations, DailyCoachSynthesis context, or AI nutrition explanation provider context.


## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are not current implementation scope:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- feature/project-continuity-system-v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
- provider runtime implementation
- raw provider output persistence
- rejected provider output persistence
- qwen3
- not bridge-enabled
- qwen3:32b
- research / future premium async candidate only
- Deterministic fallback remains mandatory.
- normal Today provider call
- public async narrative display
