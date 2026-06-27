# Project Memory Warning Review v1

Status: docs-only cleanup drafted / ready for validation.

Branch: `feature/project-memory-warning-review-v1`.

Source baseline: `main` at `4abf453`.

Milestone type: project memory / continuity / docs-only cleanup.

Commit-check mode: docs-only.

## Why this milestone exists

Nutrition Serving Unit Logging Contract Design v1 has been accepted and merged to main.

Before Backend starts Nutrition Serving Unit Logging Backend v1, the project-memory warning baseline should be reviewed.

Observed warning summary before cleanup:

```text
PASS=605 WARN=43 FAIL=0
```

Patched validation summary:

```text
PASS=620 WARN=28 FAIL=0
```

This is not a failing check. The cleanup resolved current/actionable stale state while leaving historical/archive warnings documented.

## Cleanup goal

Resolve stale/current references in canonical project-memory files and document remaining historical/archive warnings as accepted noise.

## Files intended for docs-only update

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `docs/project_memory/reviews/project_memory_warning_review_v1.md`
- `docs/project_memory/milestones/project_memory_warning_review_v1.md`

## Current canonical state after cleanup

- Nutrition Serving Unit Data Model v1: accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1: accepted and merged.
- Current main baseline: `4abf453`.
- Next implementation milestone: Nutrition Serving Unit Logging Backend v1.
- Serving-unit logging is not implemented yet.
- `food_entries` remains the grams-based actuals bridge.
- Future serving-unit logging should use backend-owned grams resolution and companion provenance.

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

## Recommended final status after Architecture acceptance

`PROJECT_MEMORY_WARNING_REVIEW_V1_ACCEPTED`

## Recommended next milestone

Nutrition Serving Unit Logging Backend v1.
