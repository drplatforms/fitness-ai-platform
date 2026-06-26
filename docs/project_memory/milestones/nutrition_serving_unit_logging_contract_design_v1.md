# Nutrition Serving Unit Logging Contract Design v1

Status: docs-only contract drafted / ready for Architecture review.

Branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Source baseline: `main` at `9cb1d41`.

Milestone type: backend design / contract / project memory only.

Commit-check mode: docs-only.

## Purpose

Define how serving-unit metadata should enter future food logging safely without changing runtime behavior in this milestone.

The contract establishes that serving-unit logging is a backend-owned convenience layer:

```text
canonical food + serving unit + quantity
-> backend resolves grams
-> backend logs grams
-> backend preserves provenance
-> existing Target-vs-Actual remains grams-based
```

## Design deliverable

Added:

- `docs/nutrition_serving_unit_logging_contract_design.md`

Updated:

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/milestones/nutrition_serving_unit_logging_contract_design_v1.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

## Accepted design direction proposed

The contract recommends:

- keep `food_entries` as the grams-based actuals bridge;
- add a companion serving-unit provenance table in the future backend milestone;
- prefer `POST /nutrition/{user_id}/log-serving` as a dedicated future endpoint;
- persist resolved grams at log time;
- copy `grams_min`, `grams_max`, confidence, amount source, serving quantity, and original serving display into provenance;
- preserve both legacy `food_id` and canonical food/serving-unit identity;
- use backend-derived `amount_source = serving_unit_estimate` for the first endpoint;
- keep serving-unit row confidence as `Low` / `Moderate` / `High`;
- defer actuals-confidence behavior to a later milestone;
- keep Target-vs-Actual unchanged except for reading resolved grams through the existing path;
- keep Streamlit as a backend-approved selector/renderer only;
- keep AI/provider away from raw serving-unit internals until approved summaries and confidence contracts exist.

## Strict scope preserved

This milestone does not:

- implement serving-unit logging;
- add an endpoint;
- change schema/code migrations;
- modify `/nutrition/log`;
- modify `/nutrition/{user_id}/log-canonical`;
- modify Target-vs-Actual;
- modify Streamlit;
- modify provider/Ollama/CrewAI behavior;
- modify food suggestions;
- add meal planning;
- change workout/recovery/report behavior.

## Recommended next milestone

Nutrition Serving Unit Logging Backend v1.

Recommended scope:

- add backend endpoint/service;
- resolve serving-unit quantity to grams;
- insert resolved grams through existing `food_entries` actuals bridge;
- persist serving-unit provenance in a companion table;
- preserve existing grams/canonical logging;
- preserve Target-vs-Actual behavior;
- no Streamlit change until backend path is stable.

## Proposed final status after Architecture acceptance

`NUTRITION_SERVING_UNIT_LOGGING_CONTRACT_DESIGN_V1_ACCEPTED`
