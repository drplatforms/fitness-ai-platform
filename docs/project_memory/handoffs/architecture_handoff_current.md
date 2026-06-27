# Architecture Handoff Current

Milestone: Nutrition Serving Unit Logging Backend v1

Status: backend implementation drafted / ready for Architecture and QA review after validation.

Source baseline: `main` at `d74ddec`.

Branch: `feature/nutrition-serving-unit-logging-backend-v1`.

Milestone type: backend implementation / service / endpoint / tests / project memory.

## Review focus

Architecture should verify that the implementation stays inside the accepted serving-unit logging contract.

Primary review decisions:

1. Confirm `food_entries` remains the grams-based actuals bridge.
2. Confirm the companion provenance table preserves serving-unit metadata at log time.
3. Confirm the endpoint is dedicated to serving-unit logging: `POST /nutrition/{user_id}/log-serving`.
4. Confirm Target-vs-Actual behavior is unchanged and reads resolved grams through the existing path.
5. Confirm Streamlit and AI/provider behavior are untouched.
6. Confirm existing raw/source and canonical grams logging still work.
7. Confirm response fields are public-safe and do not expose raw source/provider internals.

## Implemented architecture shape

Expected backend path:

```text
POST /nutrition/{user_id}/log-serving
-> validate canonical_food_id
-> validate serving_unit_id
-> validate serving unit belongs to canonical food
-> validate quantity > 0
-> resolve quantity to grams/range/confidence
-> call existing canonical grams write-through
-> insert nutrition_serving_unit_log_metadata row
-> return public-safe response
```

## Scope preserved

This milestone should not:

- add Streamlit UI;
- change provider/Ollama/CrewAI behavior;
- redesign Target-vs-Actual;
- change nutrition targets;
- add meal planning;
- change food suggestions;
- change workouts/recovery/reports.

## Recommended final Architecture decision after QA pass

Accept Nutrition Serving Unit Logging Backend v1.

Recommended final status:

`NUTRITION_SERVING_UNIT_LOGGING_BACKEND_V1_ACCEPTED`

## Recommended next milestone

Nutrition Actuals Confidence Model v1.

Purpose:

- define confidence semantics for weighed grams, grams-entered, package labels, copied entries, and serving-unit estimates;
- prepare safe display language before Streamlit Serving Unit Logging UI v1.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
