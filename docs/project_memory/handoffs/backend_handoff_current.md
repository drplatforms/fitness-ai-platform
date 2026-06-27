# Backend Handoff Current

Milestone: Project Memory Warning Review v1

Status: authorized / docs-only cleanup in progress.

Source baseline: `main` at `4abf453`.

Branch: `feature/project-memory-warning-review-v1`.

Milestone type: project memory / continuity / docs-only cleanup.

Commit-check mode: docs-only.

## Why this exists

Nutrition Serving Unit Logging Contract Design v1 has been accepted and merged to main.

Before starting Nutrition Serving Unit Logging Backend v1, Backend should review the recurring project-memory warning summary:

```text
PASS=605 WARN=43 FAIL=0
```

This is not a failing check. The purpose is to clean current canonical project-memory files and document remaining historical/archive warnings as accepted noise.

## Current canonical state

- Nutrition Serving Unit Data Model v1: accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1: accepted and merged.
- Current main baseline: `4abf453`.
- Latest feature commit: `68ca6c3`.
- Latest snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`.
- Current cleanup branch: `feature/project-memory-warning-review-v1`.
- Next implementation milestone: Nutrition Serving Unit Logging Backend v1.

## Current task

Review and update current project-memory files only.

Allowed files are current docs/project-memory state, handoffs, continuity bootstrap, project state, and optional review/milestone notes.

Do not implement serving-unit logging.

## Strict scope

No Python/runtime/API/Streamlit/schema/test/provider changes.

No `/nutrition/log` changes.

No `/nutrition/{user_id}/log-canonical` changes.

No Target-vs-Actual changes.

No food suggestion, meal planning, workout, recovery, or report changes.

No snapshots, qa_artifacts, runtime JSON, logs, patch files, or temp scripts committed.

Do not use `git add .`.

## Next implementation milestone after this cleanup

Nutrition Serving Unit Logging Backend v1.

Expected future scope:

- add backend service/endpoint for `canonical_food_id` + `serving_unit_id` + quantity;
- resolve serving-unit quantity to grams using backend-owned serving-unit metadata;
- persist `food_entries` grams row for actuals compatibility;
- persist companion serving-unit provenance metadata;
- preserve existing raw/canonical grams logging behavior;
- keep Target-vs-Actual behavior stable;
- no Streamlit changes until backend is accepted;
- no AI/provider involvement.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
