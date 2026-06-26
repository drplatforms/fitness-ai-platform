# Architecture Handoff Current

Milestone: Nutrition Serving Unit Logging Contract Design v1

Status: docs-only contract drafted / ready for Architecture review.

Source baseline: `main` at `9cb1d41`.

Branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Milestone type: backend design / contract / project memory only.

## Review focus

Architecture should review whether the proposed serving-unit logging contract is sufficient before backend implementation begins.

Primary review decisions:

1. Accept or revise the companion provenance table direction.
2. Confirm whether the future endpoint should be `POST /nutrition/{user_id}/log-serving`.
3. Confirm that `food_entries` remains the grams-based actuals bridge for v1.
4. Confirm that resolved grams, gram range, confidence, amount source, and original serving display should be persisted at log time.
5. Confirm that Target-vs-Actual should remain unchanged in the first implementation.
6. Confirm that actuals-confidence behavior should be a later milestone.
7. Confirm that Streamlit must not invent serving mappings.
8. Confirm that AI/provider should not receive serving-unit internals yet.

## Design recommendation

Architecture should accept the following design baseline:

```text
canonical_food_id + serving_unit_id + serving_quantity
-> backend validates canonical food and serving unit
-> backend resolves grams
-> backend writes resolved grams to food_entries
-> backend writes serving-unit provenance to companion table
-> Target-vs-Actual reads grams exactly as it does today
```

Preferred future table:

- `nutrition_serving_unit_log_metadata`

Acceptable alternate:

- `food_entry_serving_unit_metadata`

Preferred future endpoint:

- `POST /nutrition/{user_id}/log-serving`

## Scope preserved

The docs-only milestone does not:

- implement serving-unit logging;
- add API endpoints;
- change schema/code;
- modify `/nutrition/log`;
- modify `/nutrition/{user_id}/log-canonical`;
- modify Target-vs-Actual;
- modify Streamlit;
- modify provider/Ollama/CrewAI behavior;
- change food suggestions, meal planning, workouts, recovery, or reports.

## Recommended final Architecture decision

Accept Nutrition Serving Unit Logging Contract Design v1.

Recommended final status:

`NUTRITION_SERVING_UNIT_LOGGING_CONTRACT_DESIGN_V1_ACCEPTED`

## Recommended next milestone

Nutrition Serving Unit Logging Backend v1.

Recommended sequence after acceptance:

1. backend endpoint/service/provenance implementation;
2. actuals-confidence model design/implementation;
3. Streamlit serving-unit logging UI;
4. Target-vs-Actual confidence display;
5. serving-aware food suggestions.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
