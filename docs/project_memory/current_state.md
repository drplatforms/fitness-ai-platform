# Current State

Latest accepted milestone: Nutrition Serving Unit Data Model v1.

Latest accepted feature commit: `e2c467d`.

Latest main merge commit: `9cb1d41`.

Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_e2c467d_nutrition-serving-unit-data-model-v1.zip`.

Current implementation milestone: Nutrition Serving Unit Logging Contract Design v1.

Current branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Source baseline: `main` at `9cb1d41`.

Milestone type: backend design / contract / project memory only.

Commit-check mode: docs-only.

## Current process doctrine

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

Scope preserved by the accepted data-model milestone:

- no food logging behavior change;
- no serving-unit logging endpoint;
- no Streamlit UI change;
- no Target-vs-Actual behavior change;
- no nutrition target/formula change;
- no Daily Coach synthesis change;
- no provider/Ollama/CrewAI change;
- no AI serving inference;
- no meal planning;
- no workout or recovery change.

## Current milestone

Nutrition Serving Unit Logging Contract Design v1 is authorized.

Purpose:

Design how backend-owned serving-unit metadata should enter future food logging without corrupting existing grams-based actuals.

Approved deliverable:

- `docs/nutrition_serving_unit_logging_contract_design.md`

Approved project-memory updates:

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/milestones/nutrition_serving_unit_logging_contract_design_v1.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

## Current design decision baseline

Architecture authorized Backend to proceed with this docs-only contract using these preliminary decisions:

1. Keep `food_entries` as the grams-based actuals bridge.
2. Prefer a companion serving-unit provenance table for future implementation.
3. Prefer a dedicated future endpoint: `POST /nutrition/{user_id}/log-serving`.
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
6. Do not change Target-vs-Actual immediately.
7. Do not expose serving-unit internals to AI/provider yet.
8. Do not allow Streamlit to invent mappings.
9. Do not allow AI/provider to invent serving units, grams, conversions, macros, or actuals.
10. Treat serving-unit logging as a backend-owned convenience layer that resolves to grams.

## Strict current non-goals

The active contract milestone must not implement runtime behavior.

Do not change:

- API routes;
- schema/migrations/code;
- `/nutrition/log`;
- `/nutrition/{user_id}/log-canonical`;
- Streamlit;
- Target-vs-Actual;
- provider/Ollama/CrewAI behavior;
- food suggestions;
- meal planning;
- workout/recovery/report behavior.

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

## Recommended next milestone after this contract

If Architecture accepts Nutrition Serving Unit Logging Contract Design v1, the recommended next milestone is:

Nutrition Serving Unit Logging Backend v1

Expected scope:

- add backend service/endpoint for serving-unit logging;
- resolve serving-unit quantity to grams;
- persist grams to `food_entries`;
- persist serving-unit provenance in a companion table;
- preserve existing Target-vs-Actual behavior;
- preserve existing grams/canonical logging;
- no Streamlit change until backend path is stable.

Likely follow-up:

Nutrition Actuals Confidence Model v1

Purpose:

- define confidence semantics for weighed grams vs grams-entered vs serving-unit estimates;
- define display-safe language for estimated actuals.

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

Expected final proposed status after Architecture accepts this docs-only contract:

`NUTRITION_SERVING_UNIT_LOGGING_CONTRACT_DESIGN_V1_ACCEPTED`
