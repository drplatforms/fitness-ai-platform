# Project Continuity Bootstrap Update — Serving-Unit UI Accepted

Use this update as the active continuity layer for future chats.

Current source of truth: `main` at `0ebb1b4`.

Current canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Closed milestone: Nutrition Serving Unit Logging Streamlit UI v1.

Final accepted status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

QA status: PASS via completed manual Streamlit workflow smoke.

Recommended next milestone: Nutrition Actuals Provenance & Confidence Model v1.

Status of next milestone: recommended / pending Architecture authorization.

## What Future Chats Must Do First

1. Read this bootstrap.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/project_state.json`.
4. Read `docs/project_memory/next_milestone.md`.
5. Read the current Backend, Architecture, and QA handoffs.
6. Confirm the active branch and source baseline before proposing implementation.
7. Do not infer project rules from memory alone.
8. Distinguish feature commits/snapshots from canonical accepted main commits/snapshots.

## Current accepted serving-unit chain

The serving-unit user flow is now accepted end-to-end:

```text
GET /foods/canonical/search
-> user selects canonical food
-> GET /foods/canonical/{canonical_food_id}/serving-units
-> user selects backend-approved serving unit
-> user enters quantity
-> POST /nutrition/{user_id}/log-serving
-> backend validates food/unit/ownership
-> backend resolves grams
-> backend writes food_entries
-> backend writes serving-unit provenance metadata
-> existing Target-vs-Actual reads resolved grams
```

## Current Accepted Milestone Stack

### Daily Coach Async Service Shell / No Worker v1

Accepted historical milestone.

Scope reminder: service shell only; no provider execution added.

### Daily Coach Async Developer-Only Prototype v1

Accepted historical milestone.

Scope reminder: Developer Mode-only manual lifecycle prototype. Normal Today behavior remained unchanged.

### Daily Coach Async Provider Runtime Design v1

Accepted historical design milestone.

Scope reminder: qwen3 is not bridge-enabled. There is no provider runtime yet in this historical service shell lane. qwen3:32b is research / future premium async candidate only. Same-process hard-timeout provider execution is treated as risky.

### Nutrition Catalog + Serving Foundation Planning v1

Accepted and merged.

### Nutrition Catalog Diagnostic v1

Accepted and merged.

### Nutrition Serving Unit Data Model v1

Accepted and merged.

Accepted scope: serving-unit schema/model/service, seed script, conversion helpers, and tests.

### Nutrition Serving Unit Logging Contract Design v1

Accepted and merged.

Accepted contract baseline:

- keep `food_entries` as the grams-based actuals bridge;
- use a companion serving-unit provenance table;
- prefer `POST /nutrition/{user_id}/log-serving`;
- backend owns grams resolution;
- Target-vs-Actual remains unchanged initially;
- Streamlit must not invent mappings;
- AI/provider must not invent serving units, grams, conversions, macros, or actuals.

### Project Memory Warning Review v1

Accepted and merged.

Accepted scope: docs-only current project-memory cleanup. Remaining warnings are accepted as historical/archive/non-actionable continuity noise unless future checks prove otherwise.

### Snapshot Ownership / Main Acceptance Artifact Policy v1

Accepted and merged.

Canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge.

Feature snapshots may still exist as implementation artifacts, but they are not final accepted continuity snapshots unless explicitly designated.

Future handoffs must distinguish:

- feature commit;
- main merge commit;
- feature snapshot, if any;
- canonical accepted snapshot.

### Nutrition Serving Unit Logging Backend v1

Accepted and merged.

- Feature commit: `8b285c6`
- Main merge commit: `2279665`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

Accepted backend behavior:

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

### Canonical Serving Unit Discovery API v1

Accepted and merged.

- Main merge commit: `fd87538`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_fd87538_canonical-serving-unit-discovery-api-v1.zip`
- QA result: `CANONICAL_SERVING_UNIT_DISCOVERY_API_QA_V1_PASS`

Accepted endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

### Nutrition Serving Unit Logging Streamlit UI v1

Accepted and merged.

- Feature commit: `15aa150`
- Main merge commit: `0ebb1b4`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`
- Final status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`
- QA status: PASS via completed manual Streamlit workflow smoke

Accepted UI behavior:

- canonical food search;
- backend serving-unit discovery;
- backend-approved serving-unit selection;
- positive quantity entry;
- serving-unit log submission;
- backend-returned resolved grams display;
- existing grams logging and raw/source fallback preservation;
- existing Target-vs-Actual / Nutrition Today Summary behavior preservation.

## Current recommended next milestone

Nutrition Actuals Provenance & Confidence Model v1.

Recommended owner: Backend Development / Data Layer.

Primary question:

How should the backend represent and expose confidence/provenance for nutrition actuals now that serving-unit logging is user-facing?

Expected shape:

- narrow service/model contract;
- tests proving actuals confidence classification;
- no UI changes unless only project memory;
- no AI/provider changes;
- no Target-vs-Actual redesign yet.

## Current guardrails

Do not implement without separate Architecture authorization:

- new Streamlit serving-unit UI;
- meal planning;
- barcode scanning;
- USDA/Open Food Facts import;
- AI food matching;
- AI serving-size inference;
- nutrition explanation provider;
- food recommendation engine;
- macro target formula changes;
- Target-vs-Actual redesign;
- DailyCoachSynthesis redesign;
- workout/recovery/report changes;
- custom user serving units;
- broad nutrition logging rewrite.

## Known baseline notes

Project-memory warnings are accepted historical/archive/non-actionable continuity noise unless future checks prove otherwise.

Repo-wide mutating formatter commands should not be used during feature work. Use targeted formatting on touched files and non-mutating full-repo checks when needed.

Sound right and be right.

The `app` command launches Linux runtime; `wapp` is Windows-local only.
