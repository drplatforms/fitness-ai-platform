# Current State

Latest accepted milestone: Nutrition Serving Unit Logging Contract Design v1.

Latest accepted feature commit: `68ca6c3`.

Latest main merge commit: `4abf453`.

Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`.

Current maintenance milestone: Project Memory Warning Review v1.

Current branch: `feature/project-memory-warning-review-v1`.

Source baseline: `main` at `4abf453`.

Milestone type: project memory / continuity / docs-only cleanup.

Commit-check mode: docs-only.

Next implementation milestone: Nutrition Serving Unit Logging Backend v1.

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

Nutrition Serving Unit Logging Contract Design v1 is also accepted and merged.

Accepted contract baseline:

- keep `food_entries` as the grams-based actuals bridge;
- prefer a companion serving-unit provenance table for future implementation;
- prefer a dedicated future endpoint: `POST /nutrition/{user_id}/log-serving`;
- persist resolved grams used at log time;
- preserve serving-unit provenance: canonical food id, serving unit id, serving quantity, resolved grams, gram range, confidence, amount source, and original serving display;
- keep Target-vs-Actual unchanged in the first serving-unit logging implementation;
- keep Streamlit as a renderer/selector of backend-approved fields only;
- keep AI/provider away from serving-unit conversion and raw serving-unit internals.

Scope still not implemented:

- no serving-unit logging endpoint exists yet;
- no companion provenance table exists yet;
- no Streamlit serving-unit logging UI exists yet;
- no Target-vs-Actual confidence display for serving estimates exists yet;
- no provider/Ollama/CrewAI serving-unit path exists.

## Current maintenance milestone

Project Memory Warning Review v1 is authorized from `main` at `4abf453`.

Purpose:

Review the recurring project-memory warning summary and clean current canonical project-memory files after Nutrition Serving Unit Logging Contract Design v1 merged to main.

The warning baseline is not a failing check. Current observed summary before this cleanup remains:

```text
PASS=605 WARN=43 FAIL=0
```

The goal is to resolve current/actionable stale state and document remaining warnings as accepted historical/archive noise where appropriate.

## Current serving-unit design decision baseline

Architecture accepted these directions for the next implementation milestone:

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

The warning-review milestone must not implement runtime behavior.

Do not change:

- Python/runtime files;
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

### Nutrition Serving Unit Logging Contract Design v1

Accepted and merged.

- Feature commit: `68ca6c3`
- Main merge commit: `4abf453`
- Snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`

Accepted scope: docs-only backend contract for future serving-unit logging. No runtime behavior changed.

## Recommended next milestone after this warning review

Nutrition Serving Unit Logging Backend v1

Expected scope:

- add backend service/endpoint for serving-unit logging;
- resolve serving-unit quantity to grams;
- persist grams to `food_entries`;
- persist serving-unit provenance in a companion table;
- preserve existing Target-vs-Actual behavior;
- preserve existing grams/canonical logging;
- no Streamlit change until backend path is stable;
- no AI/provider involvement.

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

Expected final proposed status after Architecture accepts this docs-only warning review:

`PROJECT_MEMORY_WARNING_REVIEW_V1_ACCEPTED`
