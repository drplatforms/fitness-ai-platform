# Next Milestone

Current maintenance milestone in progress: Project Memory Warning Review v1.

Recommended branch: `feature/project-memory-warning-review-v1`.

Source branch: `main`.

Required source main commit: `4abf453`.

Milestone type: project memory / continuity / docs-only cleanup.

Commit-check mode: docs-only.

## Objective

Review and clean current canonical project-memory state after Nutrition Serving Unit Logging Contract Design v1 merged to main.

The recurring project-memory warning summary is not failing:

```text
PASS=605 WARN=43 FAIL=0
```

This milestone should resolve current/actionable stale references and document remaining warnings as accepted historical/archive noise where they are not actionable.

## Current canonical state to preserve

- Nutrition Serving Unit Data Model v1: accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1: accepted and merged.
- Current main baseline: `4abf453`.
- Latest contract-design feature commit: `68ca6c3`.
- Latest contract-design snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`.
- Serving-unit logging is not implemented yet.
- `food_entries` remains the grams-based actuals bridge.
- Future serving-unit logging direction remains backend-owned grams resolution with companion provenance.

## Expected next implementation milestone

Nutrition Serving Unit Logging Backend v1.

Expected owner: Backend Development / Data Layer.

Expected milestone type: backend implementation / service / endpoint / tests / project memory.

Expected future scope:

- add backend service/endpoint for `canonical_food_id` + `serving_unit_id` + quantity;
- resolve serving-unit quantity to grams using backend-owned serving-unit metadata;
- persist `food_entries` grams row for actuals compatibility;
- persist companion serving-unit provenance metadata;
- preserve existing raw/canonical grams logging behavior;
- keep Target-vs-Actual behavior stable;
- no Streamlit changes until backend is accepted;
- no AI/provider involvement.

## Accepted serving-unit contract baseline

Architecture accepted these directions for the next implementation milestone:

1. Keep `food_entries` as the grams-based actuals bridge.
2. Prefer a companion serving-unit provenance table for future implementation.
3. Prefer a dedicated future endpoint: `POST /nutrition/{user_id}/log-serving`.
4. Persist resolved grams used at log time.
5. Preserve serving-unit provenance:
   - `canonical_food_id`;
   - `serving_unit_id`;
   - serving quantity;
   - resolved grams;
   - `grams_min`;
   - `grams_max`;
   - confidence;
   - amount source;
   - original serving display.
6. Do not change Target-vs-Actual immediately.
7. Do not expose serving-unit internals to AI/provider yet.
8. Do not allow Streamlit to invent mappings.
9. Do not allow AI/provider to invent serving units, grams, conversions, macros, or actuals.
10. Treat serving-unit logging as a backend-owned convenience layer that resolves to grams.

## Strict non-goals for Project Memory Warning Review v1

Do not implement serving-unit logging.

Do not modify `/nutrition/log`.

Do not modify `/nutrition/{user_id}/log-canonical`.

Do not add a new API endpoint.

Do not modify schema/code migrations.

Do not modify Target-vs-Actual behavior.

Do not modify Streamlit.

Do not modify nutrition actuals math.

Do not modify AI/provider behavior.

Do not modify CrewAI/Ollama behavior.

Do not add meal planning.

Do not add food suggestion changes.

Do not add nutrition explanation changes.

Do not change canonical food search.

Do not expand serving-unit seed coverage.

Do not import USDA/source data.

Do not add barcode scanning.

Do not change workout generation.

Do not change recovery logic.

Do not add dependencies.

Do not commit snapshots, qa_artifacts, runtime JSON, patch scripts, or temp files.

Do not use `git add .`.

Do not run broad formatters for docs-only work.

## Validation

```powershell
git diff --check

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q

scripts/dev_commit_check.ps1 -Mode docs-only

. .\scripts\fitness_commands.ps1
fsweep

git status --short
```

Expected changed files are docs/project-memory files only.

If Python/runtime/API/Streamlit/test files appear in `git status`, stop and correct scope before commit.

## Historical authorization anchors

The following historical phrases remain required project-memory continuity anchors, not active scope for this milestone:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- `feature/daily-coach-async-persistence-contracts-schema-v1`
- schema/contracts
- NOT_AUTHORIZED_YET
