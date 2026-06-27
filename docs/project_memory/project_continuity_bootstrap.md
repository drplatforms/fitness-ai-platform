# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Current source of truth: `main` at `1820fd4` after Snapshot Ownership / Main Acceptance Artifact Policy v1 was accepted.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_1820fd4_snapshot-ownership-main-acceptance-policy-v1.zip`.

Current authorized milestone: Canonical Serving Unit Discovery API v1.

Recommended branch: `feature/canonical-serving-unit-discovery-api-v1`.

Milestone type: backend implementation / public-safe API / tests / project memory.

Commit-check mode: code.

This milestone exposes active serving units for active canonical foods through a public-safe API endpoint so Streamlit can later build a serving-unit picker without direct database lookup or invented mappings.

No Streamlit UI, logging behavior, Target-vs-Actual, or provider/AI behavior changes are authorized in this milestone.



## What Future Chats Must Do First

1. Read this bootstrap.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/project_state.json`.
4. Read `docs/project_memory/next_milestone.md`.
5. Read the current Backend, Architecture, and QA handoffs.
6. Confirm the active branch and source baseline before proposing implementation.
7. Do not infer project rules from memory alone.
8. Distinguish feature commits/snapshots from canonical accepted main commits/snapshots.

## Snapshot Ownership / Main Acceptance Artifact Policy v1

Canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge.

Feature snapshots may still exist as implementation artifacts, but they are not final accepted continuity snapshots unless explicitly designated.

Future handoffs must distinguish:

- feature commit;
- main merge commit;
- feature snapshot, if any;
- canonical accepted snapshot.

For Nutrition Serving Unit Logging Backend v1:

- Feature commit: `8b285c6 Add nutrition serving unit logging backend`
- Main merge commit: `2279665 Merge nutrition serving unit logging backend v1`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

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

- Feature commit: `8c72f23`
- Main merge commit: `94dc8fd`

### Nutrition Catalog Diagnostic v1

Accepted and merged through diagnostic project-memory/code closeout.

- Feature implementation commit: `6765abb`
- Main merge commit: `8b2c4c3`

### Nutrition Serving Unit Data Model v1

Accepted and merged.

- Feature commits: `3f0d9b6`, `e2c467d`
- Main merge commit: `9cb1d41`
- Snapshot: `fitness_ai_snapshot_2026-06-26_e2c467d_nutrition-serving-unit-data-model-v1.zip`

Accepted scope: serving-unit schema/model/service, seed script, conversion helpers, and tests. No logging endpoint or Streamlit UI was added.

### Nutrition Serving Unit Logging Contract Design v1

Accepted and merged.

- Feature commit: `68ca6c3`
- Main merge commit: `4abf453`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`

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

- Feature commit: `b395e0a`
- Main merge commit: `d74ddec`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_b395e0a_review-project-memory-warning-baseline.zip`

Accepted scope: docs-only current project-memory cleanup. Current warning baseline after review: `PASS=620 WARN=28 FAIL=0`. Remaining warnings are accepted as historical/archive/non-actionable continuity noise unless future checks prove otherwise.

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

## Current implementation milestone

Canonical Serving Unit Discovery API v1.

Expected owner: Backend Development / Data Layer.

Goal:

Expose active serving units for an active canonical food through a public-safe endpoint so Streamlit can later build a serving-unit picker without direct database lookup or invented mappings.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Rules:

- only active canonical foods;
- only active serving units;
- no raw source payloads;
- no raw SQL/debug output;
- no AI/provider involvement;
- no Streamlit mapping/inference;
- backend remains source of truth.

## Current guardrails

Do not implement Streamlit UI, provider behavior, Target-vs-Actual changes, or serving-unit logging changes in Canonical Serving Unit Discovery API v1.

Do not change:

- Python runtime code;
- API routes;
- schemas;
- Streamlit;
- tests unless project-memory tooling requires it;
- provider/Ollama/CrewAI behavior;
- nutrition actuals;
- food suggestions;
- meal planning;
- workout/recovery/report behavior.

## Known baseline notes

Project-memory check baseline before this policy closeout:

```text
PASS=620 WARN=28 FAIL=0
```

Remaining warnings are accepted historical/archive/non-actionable continuity noise unless future checks prove otherwise.

Repo-wide mutating formatter commands should not be used during feature work. Use targeted formatting on touched files and non-mutating full-repo checks when needed.

## Runtime command continuity anchor

Linux pull/validation should use explicit commands only:

```bash
cd ~/projects/fitness-ai-platform
git fetch origin --prune
git switch <branch>
git pull --ff-only origin <branch>
source .venv/bin/activate
```

Do not use `lpush`.

`app` is the canonical Linux runtime launcher for FastAPI + Streamlit.

`wapp` remains Windows-local only.
