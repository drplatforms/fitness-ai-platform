# Current State

Latest accepted milestone: Snapshot Ownership / Main Acceptance Artifact Policy v1.

Latest accepted main commit: `1820fd4`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_1820fd4_snapshot-ownership-main-acceptance-policy-v1.zip`.

Previous accepted nutrition milestone: Nutrition Serving Unit Logging Backend v1.

Previous nutrition feature commit: `8b285c6`.

Previous nutrition main merge commit: `2279665`.

Previous nutrition canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`.

Previous nutrition QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`.

Current authorized milestone: Canonical Serving Unit Discovery API v1.

Current recommended branch: `feature/canonical-serving-unit-discovery-api-v1`.

Milestone type: backend implementation / public-safe API / tests / project memory.

Commit-check mode: code.

Project-memory baseline remains: `PASS=620 WARN=28 FAIL=0`.

Remaining project-memory warnings are accepted as historical/archive/non-actionable continuity noise unless future checks prove otherwise.

## Current authorized implementation objective

Expose active serving units for an active canonical food through a narrow public-safe endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Purpose:

- allow Streamlit and QA to retrieve backend-approved serving-unit options for a selected canonical food;
- expose `serving_unit_id` without direct SQLite lookup;
- preserve backend ownership of serving-unit definitions and grams conversion;
- keep `POST /nutrition/{user_id}/log-serving` unchanged.

The endpoint must return active serving units only, public-safe fields only, deterministic ordering, and safe missing/inactive canonical food behavior.

No Streamlit UI changes or AI/provider changes are authorized in this milestone.



The current operating doctrine is:

> Bite by bite, just bigger bites.

Meaning:

- Larger objectives are allowed.
- Single patches stay narrow.
- Complexity determines process weight.
- Complex backend behavior requires diagnostic-first and test-first gates where practical.
- Real smoke failures become automated regression tests, diagnostic/coverage tests, documented limitations, or backlog items.
- Architecture defines v1/v2 scope before branches spiral.
- Backend must not blindly stack patches after repeated failures.
- QA validates the real user path, not only generic test-green status.
- Docs/project memory are first-class continuity artifacts and must be updated with every milestone.
- Feature implementation snapshots and canonical accepted snapshots must be distinguished.

## Snapshot Ownership / Main Acceptance Artifact Policy v1

Architecture has established the following snapshot ownership policy:

1. Backend owns:
   - implementation;
   - focused tests;
   - validation;
   - feature branch;
   - feature commit;
   - implementation handoff;
   - optional feature implementation snapshot.

2. Architecture / TPM / Project Memory owns:
   - accepted milestone state;
   - merge-to-main authorization;
   - canonical main commit tracking;
   - canonical accepted snapshot naming;
   - continuity artifact policy.

3. QA owns:
   - validation against the accepted implementation and/or accepted main state;
   - pass/fail evidence;
   - defect routing.

4. Feature snapshots:
   - may exist as implementation artifacts;
   - are not final accepted continuity snapshots unless explicitly designated;
   - may have hashes that differ from the main merge commit.

5. Canonical accepted snapshots:
   - should be created from `main` after Architecture acceptance / merge;
   - should use the accepted main commit hash in the filename;
   - should not be committed to the repo;
   - should be referenced in project memory.

6. Future handoffs must distinguish:
   - feature commit;
   - main merge commit;
   - feature snapshot, if any;
   - canonical accepted snapshot.

## Current accepted nutrition serving-unit backend state

Nutrition Serving Unit Logging Backend v1 is accepted and merged.

Accepted implementation state:

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

Accepted backend artifacts:

- Feature commit: `8b285c6 Add nutrition serving unit logging backend`
- Main merge commit: `2279665 Merge nutrition serving unit logging backend v1`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

Accepted backend behavior:

- endpoint: `POST /nutrition/{user_id}/log-serving`;
- companion provenance table: `nutrition_serving_unit_log_metadata`;
- backend-owned validation for canonical food, serving unit, active state, ownership, and positive quantity;
- backend-owned serving quantity to grams resolution;
- existing `food_entries` row insertion using resolved grams;
- companion provenance persistence;
- public-safe serving-unit logging response;
- existing raw/source `/nutrition/log` remains stable;
- existing canonical grams `/nutrition/{user_id}/log-canonical` remains stable;
- existing Target-vs-Actual actuals calculation remains grams-based;
- missing nutrients remain missing/unknown, not zero;
- no Streamlit behavior changed;
- no AI/provider/Ollama/CrewAI behavior changed.

## Current nutrition foundation state

Nutrition Serving Unit Data Model v1 is accepted and merged.

Accepted foundation:

- `canonical_food_serving_units` schema/service/model exists.
- Serving units are linked to canonical foods.
- Serving units include default grams, min/max gram ranges, confidence, source/source note, active state, and sort order.
- Confidence vocabulary for serving-unit rows is `Low`, `Moderate`, `High`.
- `Medium` normalizes to `Moderate`.
- Seed script is idempotent.
- Seed coverage: 18 active serving units across 12 canonical foods.
- Missing canonical foods from the starter seed: none.

Nutrition Serving Unit Logging Contract Design v1 is accepted and merged.

Project Memory Warning Review v1 is accepted and merged.

## Current serving-unit design decision baseline

Architecture accepted these directions for the implementation milestone:

1. Keep `food_entries` as the grams-based actuals bridge.
2. Add a companion serving-unit provenance table.
3. Use a dedicated endpoint: `POST /nutrition/{user_id}/log-serving`.
4. Persist resolved grams used at log time.
5. Preserve serving-unit provenance:
   - canonical food id;
   - serving unit id;
   - serving quantity;
   - resolved grams;
   - grams min/max;
   - confidence;
   - amount source;
   - original serving display.
6. Do not change Target-vs-Actual behavior.
7. Do not expose serving-unit internals to AI/provider.
8. Do not allow Streamlit to invent mappings.
9. Do not allow AI/provider to invent serving units, grams, conversions, macros, or actuals.
10. Treat serving-unit logging as a backend-owned convenience layer that resolves to grams.

## Scope still not implemented

- no Streamlit serving-unit logging UI exists yet;
- no Target-vs-Actual confidence display for serving estimates exists yet;
- no provider/Ollama/CrewAI serving-unit path exists;
- no serving-aware food suggestion behavior exists yet.

## Strict current non-goals

Canonical Serving Unit Discovery API v1 must not change:

- Streamlit UI behavior;
- serving-unit logging behavior;
- `POST /nutrition/{user_id}/log-serving`;
- Target-vs-Actual behavior/design;
- provider/Ollama/CrewAI behavior;
- nutrition explanation behavior;
- nutrition target formula behavior;
- food suggestions;
- meal planning;
- workout/recovery/report behavior;
- raw/source food import behavior;
- canonical food normalization redesign.

## Recent accepted nutrition milestones

### Nutrition Catalog + Serving Foundation Planning v1

Accepted and merged.

- Feature commit: `8c72f23`
- Main merge commit: `94dc8fd`
- Snapshot: `fitness_ai_snapshot_2026-06-26_8c72f23_plan-nutrition-catalog-and-serving-foundation.zip`

Accepted planning scope: two-layer food catalog doctrine, serving-unit confidence/range strategy, nutrition actuals confidence direction, deterministic suggestions before AI meal/snack generation, and provider boundary.

### Nutrition Catalog Diagnostic v1

Accepted and merged through diagnostic project-memory/code closeout.

- Feature implementation commit: `6765abb`
- Diagnostic code closeout commit: `9f1285f`
- Main merge commit: `8b2c4c3`

Accepted scope: diagnostic service, diagnostic CLI, focused tests, project-memory closeout, and no app/runtime behavior change.

Diagnostic conclusion: canonical food catalog coverage is strong enough for now; serving-unit/confidence infrastructure is the immediate blocker before practical household-measure logging or serving-aware suggestions.

### Nutrition Serving Unit Data Model v1

Accepted and merged.

- Feature commits: `3f0d9b6`, `e2c467d`
- Main merge commit: `9cb1d41`
- Snapshot: `fitness_ai_snapshot_2026-06-26_e2c467d_nutrition-serving-unit-data-model-v1.zip`

Accepted scope: backend serving-unit model/service/schema, idempotent seed script, deterministic lookup/conversion helpers, focused tests, and project-memory closeout.

### Nutrition Serving Unit Logging Contract Design v1

Accepted and merged.

- Feature commit: `68ca6c3`
- Main merge commit: `4abf453`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`

Accepted scope: docs-only backend contract for future serving-unit logging. No runtime behavior changed.

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

Accepted scope: backend service, endpoint, companion provenance table, tests, and project-memory updates for canonical-food serving-unit logging. No Streamlit or AI/provider behavior changed.

## Recommended next implementation milestone

Canonical Serving Unit Discovery API v1

Expected owner: Backend Development / Data Layer.

Goal:

Expose active serving units for an active canonical food through a public-safe backend endpoint so Streamlit can later build a serving-unit picker without direct database lookup or invented mappings.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Expected response:

- `success`;
- `canonical_food_id`;
- canonical food `display_name`;
- `serving_units` list:
  - `serving_unit_id`;
  - `display_name`;
  - `grams_default`;
  - `grams_min`;
  - `grams_max`;
  - `confidence`;
  - `amount_source`;
  - `sort_order` / display order if supported.

Rules:

- only active canonical foods;
- only active serving units;
- no raw source payloads;
- no raw SQL/debug output;
- no AI/provider involvement;
- no Streamlit mapping/inference;
- backend remains source of truth.

This should precede:

Nutrition Serving Unit Logging Streamlit UI v1

## Historical continuity anchors

These phrases are retained to keep the project-memory checker and future-agent continuity aligned:

- Project Memory Alignment + North Star Architecture v1
- `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1`
- reference-only
- No provider may run on normal Today page load
- Provider Narrative QA Matrix v2
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- `scripts/fitness_commands.ps1`
- Local Command Menu App Runtime Correction v1
- Linux is the canonical FastAPI + Streamlit runtime
- `wapp`
- Daily Coach Async Service Shell / No Worker v1
- service shell only
- no provider execution added

## Current final status target

Expected final proposed status after Architecture accepts this docs/process closeout:

`SNAPSHOT_OWNERSHIP_MAIN_ACCEPTANCE_ARTIFACT_POLICY_V1_ACCEPTED`
