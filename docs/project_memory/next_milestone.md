# Next Milestone

Current implementation milestone in progress: Nutrition Serving Unit Logging Backend v1.

Recommended branch: `feature/nutrition-serving-unit-logging-backend-v1`.

Source branch: `main`.

Required source main commit: `d74ddec`.

Milestone type: backend implementation / service / endpoint / tests / project memory.

Commit-check mode: code.

## Objective

Implement backend-owned canonical-food serving-unit logging without changing Streamlit, AI/provider behavior, nutrition target formulas, or Target-vs-Actual behavior.

The endpoint should allow a future UI to submit:

```text
canonical_food_id + serving_unit_id + quantity
```

Backend resolves that serving quantity to grams, writes the resolved grams through the existing `food_entries` path, and stores serving-unit provenance in a companion table.

## Current canonical state to preserve

- Nutrition Serving Unit Data Model v1: accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1: accepted and merged.
- Project Memory Warning Review v1: accepted and merged.
- Current main baseline: `d74ddec`.
- Latest accepted feature commit: `b395e0a`.
- Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_b395e0a_review-project-memory-warning-baseline.zip`.
- Project-memory baseline: `PASS=620 WARN=28 FAIL=0`.
- Remaining warnings are accepted historical/archive/non-actionable continuity noise unless future checks prove otherwise.

## Implementation scope

Nutrition Serving Unit Logging Backend v1 should add:

- companion provenance table: `nutrition_serving_unit_log_metadata`;
- backend service behavior for serving-unit logging;
- endpoint: `POST /nutrition/{user_id}/log-serving`;
- positive quantity validation;
- canonical food validation;
- serving-unit validation;
- active state checks;
- serving-unit ownership checks;
- resolved grams persistence through `food_entries`;
- serving-unit provenance persistence;
- public-safe response fields;
- focused service/API/Target-vs-Actual regression tests;
- project-memory updates.

## Behavior to preserve

The following must continue to work unchanged:

- existing raw/source `/nutrition/log` behavior;
- existing canonical grams `/nutrition/{user_id}/log-canonical` behavior;
- existing canonical food search behavior;
- existing canonical food seed behavior;
- existing serving-unit seed behavior;
- existing Target-vs-Actual actuals calculation from grams;
- existing DailyCoachSynthesis/recommendation/report behavior;
- existing provider/Ollama/CrewAI boundaries.

## Non-goals

Do not add:

- Streamlit serving-unit UI;
- food picker changes;
- AI/provider serving-unit behavior;
- CrewAI/Ollama changes;
- Target-vs-Actual redesign;
- serving-estimate confidence display;
- nutrition target formula changes;
- food suggestion changes;
- meal planning;
- barcode scanning;
- USDA/Open Food Facts import;
- workout/recovery/report changes.

## Expected next milestone after Backend v1 acceptance

Nutrition Serving Unit Logging Backend QA / Architecture Review v1.

Likely follow-up after acceptance:

Nutrition Actuals Confidence Model v1.

Purpose:

- distinguish weighed grams, entered grams, package-label amounts, and serving-unit estimates;
- define display-safe language for estimated actuals;
- prepare Target-vs-Actual confidence display before Streamlit serving-unit UI.

## Historical continuity anchors

These phrases are retained for project-memory checker continuity and future-agent context:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- `feature/daily-coach-async-persistence-contracts-schema-v1`
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical anchors only. They do not authorize provider/runtime work in the current serving-unit logging backend milestone.
