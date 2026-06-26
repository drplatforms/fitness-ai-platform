# Backend Handoff Current

Milestone: Nutrition Serving Unit Logging Contract Design v1

Status: docs-only contract drafted / ready for Architecture review.

Source baseline: `main` at `9cb1d41`.

Branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Commit-check mode: docs-only.

## Backend scope

Backend drafted the serving-unit logging contract only.

No runtime implementation was added.

Primary deliverable:

- `docs/nutrition_serving_unit_logging_contract_design.md`

Project-memory updates:

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/milestones/nutrition_serving_unit_logging_contract_design_v1.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

## Contract summary

The contract recommends that future serving-unit logging should:

- keep `food_entries` as the grams-based actuals bridge;
- add a companion serving-unit provenance table;
- prefer a dedicated endpoint: `POST /nutrition/{user_id}/log-serving`;
- persist resolved grams used at log time;
- copy `grams_min`, `grams_max`, confidence, amount source, serving quantity, and original serving display into provenance;
- preserve `canonical_food_id` and `serving_unit_id` in provenance;
- keep legacy `food_entries.food_id` for current actuals compatibility;
- reject grams override in v1;
- reject user-defined serving overrides in v1;
- keep Target-vs-Actual math unchanged;
- keep Streamlit from inventing mappings;
- keep AI/provider from inventing serving units, grams, conversions, macros, or actuals.

## Recommended future implementation shape

Future backend endpoint:

```text
POST /nutrition/{user_id}/log-serving
```

Future request:

```json
{
  "canonical_food_id": 1,
  "serving_unit_id": 10,
  "serving_quantity": 1.0,
  "entry_date": "2026-06-26"
}
```

Future response should include:

- success;
- user id;
- logged food entry id;
- canonical food id;
- serving unit id;
- display name;
- serving display;
- serving quantity;
- resolved grams;
- grams min/max;
- confidence;
- amount source;
- logged date;
- public-safe nutrient summary where available.

## Backend validation expectations for next implementation

Future implementation must validate:

- active canonical food exists;
- active serving unit exists;
- serving unit belongs to canonical food;
- serving quantity is positive;
- resolved grams are positive;
- ranges are internally consistent;
- entry date is valid;
- canonical nutrient data is usable;
- caller cannot submit grams override;
- caller cannot submit arbitrary confidence or amount source.

## Scope preserved

No Python, API, database, Streamlit, provider, workout, recovery, report, or Target-vs-Actual behavior changed in this docs-only milestone.

## Next backend recommendation

After Architecture accepts this contract, proceed to Nutrition Serving Unit Logging Backend v1.

Do not start Streamlit serving-unit UI until the backend endpoint/provenance path is stable.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
