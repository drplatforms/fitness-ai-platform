# Nutrition Serving Unit Logging Streamlit UI v1

Status: accepted and merged.

Final status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

Owner: Streamlit UI.

Source baseline: `main` at `fd87538`.

Feature branch: `feature/nutrition-serving-unit-logging-streamlit-ui-v1`.

Feature commit: `15aa150 Add Streamlit serving unit nutrition logging`.

Canonical main merge commit: `0ebb1b4`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

QA status: PASS via completed manual Streamlit workflow smoke.

Separate QA handoff: not required unless Architecture explicitly requests independent QA review.

## Purpose

Add the first Streamlit UI path for logging a canonical food by backend-approved serving unit.

The accepted UI path is:

```text
canonical food search
-> select canonical food
-> load backend-approved serving units
-> select serving unit
-> enter quantity
-> POST /nutrition/{user_id}/log-serving
-> display backend-returned resolved grams and public-safe context
```

## Backend contract consumed

Canonical food search:

`GET /foods/canonical/search?q=<query>`

Serving-unit discovery:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Serving-unit logging:

`POST /nutrition/{user_id}/log-serving`

## Accepted boundaries

Streamlit does not:

- query raw database tables;
- inspect `canonical_food_serving_units` directly;
- invent serving-unit mappings;
- infer `serving_unit_id`;
- convert serving units to grams;
- submit grams overrides to `/nutrition/{user_id}/log-serving`;
- calculate nutrients/macros/actuals;
- expose raw source payloads or SQL/debug internals in normal UI;
- involve AI/provider/Ollama/CrewAI logic;
- redesign Target-vs-Actual or DailyCoachSynthesis.

Backend remains responsible for canonical food validation, serving-unit validation, ownership checks, quantity validation, grams resolution, food entry writes, provenance persistence, and Target-vs-Actual compatibility.

## Accepted UI behavior

- Reuses existing Nutrition page canonical food search.
- Shows serving-unit logging after canonical food selection.
- Calls the serving-unit discovery endpoint for the selected canonical food.
- Renders serving-unit labels from backend-returned values.
- Submits only backend-approved identifiers plus user quantity/date.
- Displays backend-returned resolved grams, date, confidence, source, and grams range when returned.
- Preserves canonical grams logging as a fallback.
- Preserves raw/source food database logging as an advanced fallback.
- Keeps Developer Mode details behind the existing Developer Mode gate.

## QA closeout

Manual Streamlit smoke: PASS.

Manual smoke confirmed the full user-facing path, existing fallback preservation, no traceback, no AI/provider path, no raw internals in normal UI, and no stale `serving_unit_id` submission after changing selected canonical food.

## Next recommended milestone

Nutrition Actuals Provenance & Confidence Model v1.

Purpose:

Create a backend-owned interpretation layer for nutrition actuals confidence and provenance now that serving-unit logging is user-facing.
