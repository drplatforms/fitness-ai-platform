# Next Milestone

Current authorized milestone: Canonical Serving Unit Discovery API v1.

Recommended branch: `feature/canonical-serving-unit-discovery-api-v1`.

Source branch: `main`.

Required source main commit: `1820fd4`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_1820fd4_snapshot-ownership-main-acceptance-policy-v1.zip`.

Milestone type: backend implementation / public-safe API / tests / project memory.

Commit-check mode: code.

## Objective

Expose active serving units for an active canonical food through a public-safe backend endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

This fills the QA-discovered gap after Nutrition Serving Unit Logging Backend v1: serving-unit IDs are currently usable by backend logging, but they are not discoverable through a public-safe API response for Streamlit.

## Current canonical state to preserve

- Snapshot Ownership / Main Acceptance Artifact Policy v1: accepted.
- Nutrition Serving Unit Logging Backend v1: accepted and merged.
- Current source of truth: `main` at `1820fd4`.
- Previous nutrition main merge commit: `2279665`.
- Previous nutrition feature commit: `8b285c6`.
- Previous nutrition canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`.
- Current canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_1820fd4_snapshot-ownership-main-acceptance-policy-v1.zip`.
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`.
- Project-memory baseline: `PASS=620 WARN=28 FAIL=0`.

## Required behavior

The endpoint should return:

- `success`;
- `canonical_food_id`;
- canonical food display name;
- active serving-unit options for that canonical food.

Each serving unit should include public-safe metadata such as:

- `serving_unit_id`;
- `display_name`;
- `unit_name`;
- `unit_quantity`;
- `grams_default`;
- `grams_min`;
- `grams_max`;
- `confidence`;
- `amount_source`;
- `source`;
- `source_notes`;
- `sort_order`.

The endpoint must not expose raw source payloads, raw SQL/debug output, provider/runtime metadata, validation internals, tracebacks, inactive serving units, or inactive canonical foods.

## Validation expectations

Focused tests should prove:

- valid canonical food returns active serving units;
- response includes `serving_unit_id`;
- inactive serving units are excluded;
- inactive/missing canonical foods are handled safely;
- foods with no active serving units return a safe empty list;
- ordering is deterministic;
- public-safe response does not expose raw source payloads or debug internals;
- existing canonical search remains stable;
- existing serving-unit logging remains stable;
- Target-vs-Actual remains stable.

## Strict non-goals

Do not implement:

- Streamlit serving-unit picker UI;
- Streamlit nutrition logging changes;
- new logging behavior;
- changes to `POST /nutrition/{user_id}/log-serving`;
- Target-vs-Actual changes;
- DailyCoachSynthesis changes;
- AI/provider changes;
- CrewAI changes;
- direct_ollama changes;
- nutrition explanation changes;
- meal planning;
- food suggestions;
- canonical food catalog expansion;
- USDA/Open Food Facts import;
- barcode scanning;
- user-defined serving units;
- serving-unit overrides;
- actuals confidence model;
- broad food normalization redesign;
- broad nutrition logging rewrite.

## Expected next milestone after acceptance

Nutrition Serving Unit Logging Streamlit UI v1.

Expected purpose:

- let Streamlit render backend-approved serving-unit options;
- submit `canonical_food_id + serving_unit_id + quantity`;
- render backend-returned grams/confidence/provenance;
- keep Streamlit out of conversion/mapping logic.

## Historical continuity anchors

The following phrases are preserved for project-memory continuity checks. They are reference-only and are not current Canonical Serving Unit Discovery API v1 scope.

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
