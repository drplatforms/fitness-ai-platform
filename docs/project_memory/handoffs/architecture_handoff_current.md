# Architecture Handoff Current

Milestone: Project Memory Warning Review v1

Status: docs-only cleanup drafted / ready for Architecture review after validation.

Source baseline: `main` at `4abf453`.

Branch: `feature/project-memory-warning-review-v1`.

Milestone type: project memory / continuity / docs-only cleanup.

## Review focus

Architecture should review whether current canonical project-memory state is aligned after Nutrition Serving Unit Logging Contract Design v1 merged to main.

Primary review decisions:

1. Confirm Nutrition Serving Unit Logging Contract Design v1 is represented as accepted and merged.
2. Confirm current main baseline is `4abf453`.
3. Confirm current warning review does not imply runtime scope.
4. Confirm next implementation milestone is Nutrition Serving Unit Logging Backend v1.
5. Confirm remaining project-memory warnings are documented as historical/archive noise where they are not actionable.

## Current serving-unit contract baseline

Accepted design baseline:

```text
canonical_food_id + serving_unit_id + serving_quantity
-> backend validates canonical food and serving unit
-> backend resolves grams
-> backend writes resolved grams to food_entries
-> backend writes serving-unit provenance to companion table
-> Target-vs-Actual reads grams exactly as it does today
```

Preferred future endpoint:

- `POST /nutrition/{user_id}/log-serving`

Preferred future persistence:

- `food_entries` grams bridge plus companion serving-unit provenance table

## Warning baseline

Observed before cleanup:

```text
PASS=605 WARN=43 FAIL=0
```

This is not a failing check. Remaining warnings in historical milestone/review/design files are acceptable if current canonical docs are accurate and the warnings are documented.

## Scope preserved

The docs-only cleanup does not:

- implement serving-unit logging;
- add API endpoints;
- change schema/code;
- modify `/nutrition/log`;
- modify `/nutrition/{user_id}/log-canonical`;
- modify Target-vs-Actual;
- modify Streamlit;
- modify provider/Ollama/CrewAI behavior;
- change food suggestions, meal planning, workouts, recovery, or reports.

## Recommended final Architecture decision

Accept Project Memory Warning Review v1.

Recommended final status:

`PROJECT_MEMORY_WARNING_REVIEW_V1_ACCEPTED`

## Recommended next milestone

Nutrition Serving Unit Logging Backend v1.

Recommended owner: Backend Development / Data Layer.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
