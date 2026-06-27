# Canonical Serving Unit Discovery API v1

Status: accepted and merged.

Branch: `feature/canonical-serving-unit-discovery-api-v1`.

Feature commit: `e6d8578 Add canonical serving unit discovery API`.

Main merge commit: `fd87538`.

Source baseline: `main` at `1820fd4`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_1820fd4_snapshot-ownership-main-acceptance-policy-v1.zip`.

Commit-check mode: code.

## Purpose

Expose active serving units for an active canonical food through a narrow public-safe backend endpoint before Streamlit serving-unit picker work begins.

Expected endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

## Why this milestone exists

Nutrition Serving Unit Logging Backend v1 is accepted and merged. Backend can log `canonical_food_id + serving_unit_id + quantity` through `POST /nutrition/{user_id}/log-serving`.

QA confirmed that logging path works, but manual QA had to look up `serving_unit_id` directly in the SQLite table `canonical_food_serving_units`.

That is acceptable for backend QA but not acceptable for Streamlit. Streamlit must consume backend-approved serving-unit options through a public-safe API.

## Required behavior

The endpoint must:

- verify `canonical_food_id` exists;
- hide/reject inactive canonical foods safely;
- return active serving units only;
- return deterministic ordering;
- expose `serving_unit_id` for UI selection;
- expose display-safe serving-unit metadata;
- avoid raw source payloads, raw SQL/debug fields, provider/runtime metadata, validation internals, and tracebacks.

Expected serving-unit fields:

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

## Acceptance criteria

Backend milestone is acceptable when:

1. `GET /foods/canonical/{canonical_food_id}/serving-units` exists.
2. Endpoint returns active serving units for active canonical foods.
3. Endpoint exposes `serving_unit_id`.
4. Endpoint exposes display-safe serving-unit metadata.
5. Endpoint does not expose raw source payloads.
6. Endpoint does not expose raw SQL/debug internals.
7. Endpoint excludes inactive serving units.
8. Endpoint handles missing/inactive canonical food safely.
9. Endpoint handles canonical foods with no active serving units safely.
10. Existing `/foods/canonical/search` behavior remains stable.
11. Existing `POST /nutrition/{user_id}/log-serving` behavior remains stable.
12. Existing `/nutrition/{user_id}/log-canonical` behavior remains stable.
13. Existing `/nutrition/log` behavior remains stable.
14. Target-vs-Actual remains stable.
15. No Streamlit files are changed.
16. No AI/provider files are changed.
17. Project memory is updated.
18. Focused tests pass.
19. Working tree is clean after commit.
20. Feature branch is pushed.

## Expected next milestone

Nutrition Serving Unit Logging Streamlit UI v1.

Completed by Nutrition Serving Unit Logging Streamlit UI v1.
