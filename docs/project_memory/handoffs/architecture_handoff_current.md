# Architecture Handoff Current

Milestone: Canonical Serving Unit Discovery API v1

Status: authorized backend implementation.

Source baseline: `main` at `1820fd4`.

Branch: `feature/canonical-serving-unit-discovery-api-v1`.

Milestone type: backend implementation / public-safe API / tests / project memory.

## Review focus

Architecture should verify that Backend adds only the narrow serving-unit discovery API needed before Streamlit serving-unit picker work.

Primary review decisions:

1. Confirm `GET /foods/canonical/{canonical_food_id}/serving-units` exists.
2. Confirm endpoint returns active serving units for active canonical foods.
3. Confirm `serving_unit_id` is visible for Streamlit selection.
4. Confirm response is public-safe and excludes raw source payloads/debug internals.
5. Confirm inactive serving units are excluded.
6. Confirm inactive/missing canonical foods are handled safely.
7. Confirm existing canonical search/logging behavior remains stable.
8. Confirm `POST /nutrition/{user_id}/log-serving` behavior is unchanged.
9. Confirm Target-vs-Actual remains grams-based and stable.
10. Confirm no Streamlit or AI/provider changes were made.

## Current accepted serving-unit backend state

Nutrition Serving Unit Logging Backend v1 is accepted and merged.

- Feature commit: `8b285c6`
- Main merge commit: `2279665`
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

Accepted behavior:

```text
canonical_food_id + serving_unit_id + quantity
-> backend validates canonical food
-> backend validates serving unit
-> backend verifies serving unit belongs to canonical food
-> backend resolves serving quantity to grams
-> backend writes resolved grams through food_entries
-> backend persists serving-unit provenance metadata
-> existing Target-vs-Actual reads resolved grams through existing actuals flow
```

## Snapshot policy reminder

Feature snapshots are implementation artifacts.

Canonical accepted snapshots are created from `main` after Architecture acceptance / merge and use the accepted main commit hash in the filename.

Backend does not create the final canonical accepted snapshot for this implementation milestone.

## Recommended final Architecture decision after review

Accept Canonical Serving Unit Discovery API v1.

Recommended final status:

`CANONICAL_SERVING_UNIT_DISCOVERY_API_V1_ACCEPTED`

## Recommended next milestone after acceptance

Nutrition Serving Unit Logging Streamlit UI v1.

Purpose:

Allow Streamlit to render backend-approved serving-unit options, submit `canonical_food_id + serving_unit_id + quantity`, and display backend-returned grams/confidence without inventing mappings or conversions.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
