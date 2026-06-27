# Backend Handoff Current

Milestone: Canonical Serving Unit Discovery API v1

Status: authorized backend implementation.

Source baseline: `main` at `1820fd4`.

Branch: `feature/canonical-serving-unit-discovery-api-v1`.

Milestone type: backend implementation / public-safe API / tests / project memory.

Commit-check mode: code.

## Why this exists

Nutrition Serving Unit Logging Backend v1 is accepted, QA-passed, and merged.

The backend can log:

```text
canonical_food_id + serving_unit_id + quantity
-> validated serving-unit log
-> resolved grams
-> food_entries actuals bridge
-> serving-unit provenance metadata
-> Target-vs-Actual compatibility
```

QA found one required follow-up before Streamlit Serving Unit Logging UI v1:

Serving-unit IDs are not discoverable through a public-safe API response. Manual QA had to look up `serving_unit_id` directly in `canonical_food_serving_units`.

That is acceptable for backend QA but not acceptable for Streamlit.

## Current task

Add a public-safe serving-unit discovery endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Purpose:

Allow Streamlit and QA to retrieve backend-approved active serving-unit options for a selected canonical food.

## Required behavior

The endpoint should:

- verify `canonical_food_id` exists;
- hide/reject inactive canonical foods safely;
- return active serving units only;
- return deterministic ordering;
- expose `serving_unit_id`;
- expose display-safe serving-unit metadata;
- avoid raw source payloads, raw SQL/debug fields, provider/runtime metadata, and tracebacks.

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

## Scope preserved

Do not change:

- Streamlit UI;
- `POST /nutrition/{user_id}/log-serving`;
- `/nutrition/{user_id}/log-canonical`;
- `/nutrition/log`;
- Target-vs-Actual behavior;
- DailyCoachSynthesis;
- AI/provider/Ollama/CrewAI behavior;
- nutrition explanations;
- food suggestions;
- meal planning;
- workout/recovery/report behavior.

## Likely files

Inspect current repo first. Likely files:

- `api/routes/food_canonical_search.py`;
- `services/nutrition_serving_unit_service.py`;
- `tests/test_canonical_serving_unit_discovery_api.py`;
- project-memory docs/handoffs.

Do not create duplicate route modules if the existing canonical food route module is sufficient.

## Validation expectations

Run targeted lint/format/checks for touched files only. Do not run repo-wide mutating formatter commands.

Focused tests should include:

- valid canonical food returns active serving units;
- inactive serving units excluded;
- inactive/missing canonical food safe error;
- canonical food with no units returns safe empty list;
- public-safe fields only;
- deterministic ordering;
- existing canonical search stable;
- existing serving-unit logging stable;
- Target-vs-Actual stable;
- project memory updated.

## Process notes

Use explicit staging only.

Do not use `git add .`.

Push must be its own separate phase.

Do not create a final canonical accepted snapshot from Backend. Architecture / TPM / Project Memory owns canonical accepted snapshots after merge to main.

## Runtime command continuity anchor

Linux pull/validation should use explicit commands only:

```bash
cd ~/projects/fitness-ai-platform
git fetch origin --prune
git switch feature/canonical-serving-unit-discovery-api-v1
git pull --ff-only origin feature/canonical-serving-unit-discovery-api-v1
source .venv/bin/activate
```

Do not use `lpush`.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
