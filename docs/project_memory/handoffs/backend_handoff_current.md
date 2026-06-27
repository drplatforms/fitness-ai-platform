# Backend Handoff Current

Milestone: Nutrition Serving Unit Logging Backend v1

Status: authorized for backend implementation / patch drafted.

Source baseline: `main` at `d74ddec`.

Branch: `feature/nutrition-serving-unit-logging-backend-v1`.

Milestone type: backend implementation / service / endpoint / tests / project memory.

Commit-check mode: code.

## Why this exists

Nutrition Serving Unit Data Model v1 and Nutrition Serving Unit Logging Contract Design v1 are accepted and merged.

Project Memory Warning Review v1 is accepted and merged with current memory baseline:

```text
PASS=620 WARN=28 FAIL=0
```

Remaining warnings are accepted historical/archive/non-actionable continuity noise unless future checks prove otherwise.

Backend is now authorized to implement the serving-unit logging vertical slice.

## Current task

Implement backend-owned canonical food serving-unit logging:

```text
canonical_food_id + serving_unit_id + quantity
-> backend validates canonical food and serving unit
-> backend resolves grams
-> backend writes resolved grams to food_entries
-> backend writes serving-unit provenance metadata
-> Target-vs-Actual reads grams exactly as it does today
```

## Expected implementation

- Add companion provenance table: `nutrition_serving_unit_log_metadata`.
- Add backend service behavior for serving-unit logging.
- Add dedicated endpoint: `POST /nutrition/{user_id}/log-serving`.
- Validate canonical food exists and is active.
- Validate serving unit exists and is active.
- Validate serving unit belongs to the requested canonical food.
- Validate quantity is positive.
- Resolve grams using backend-owned serving-unit metadata.
- Persist resolved grams through the existing canonical grams logging path.
- Persist serving-unit provenance metadata.
- Return public-safe fields only.

## Scope preserved

Do not change:

- Streamlit;
- AI/provider/Ollama/CrewAI behavior;
- Target-vs-Actual behavior/design;
- nutrition target formulas;
- food suggestions;
- meal planning;
- workout/recovery/report behavior;
- raw/source food import behavior;
- canonical search behavior.

## Required tests

Focused tests should cover:

- service grams resolution and gram range resolution;
- positive decimal quantities;
- zero/negative quantity rejection;
- missing/inactive/wrong-food serving units;
- resolved grams persisted into `food_entries`;
- serving-unit metadata persisted;
- missing optional ranges remain missing, not zero;
- serving-unit logs appear in daily nutrition/Target-vs-Actual actuals;
- existing raw/source grams logging remains stable;
- existing canonical grams logging remains stable;
- public-safe API response.

## Process notes

Use explicit staging only.

Do not use `git add .`.

Push must be its own separate phase.

## Runtime command continuity anchor

Linux pull/validation should use explicit commands only:

```bash
cd ~/projects/fitness-ai-platform
git fetch origin --prune
git switch feature/nutrition-serving-unit-logging-backend-v1
git pull --ff-only origin feature/nutrition-serving-unit-logging-backend-v1
source .venv/bin/activate
```

Do not use `lpush`.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
