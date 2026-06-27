# Project Memory Warning Review v1

Status: docs-only cleanup drafted.

Branch: `feature/project-memory-warning-review-v1`.

Source baseline: `main` at `4abf453`.

Milestone type: project memory / continuity / docs-only cleanup.

## Purpose

Review the recurring project-memory warning output after Nutrition Serving Unit Logging Contract Design v1 merged to main.

The warning baseline before cleanup is not failing:

```text
PASS=605 WARN=43 FAIL=0
```

Local validation against the patched project-memory state showed:

```text
PASS=620 WARN=28 FAIL=0
```

Net result: 15 warnings resolved or converted to passing checks, with no failures introduced.

The goal is not to erase historical context. The goal is to make current canonical project-memory files accurate before Nutrition Serving Unit Logging Backend v1 begins.

## Current canonical state confirmed

- Nutrition Serving Unit Data Model v1 is accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1 is accepted and merged.
- Current main baseline is `4abf453`.
- Latest contract-design feature commit is `68ca6c3`.
- Latest contract-design snapshot is `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`.
- Next implementation milestone is Nutrition Serving Unit Logging Backend v1.

## Actionable/current warning cleanup

Current canonical files were updated to remove stale active-state references to the contract-design branch and milestone.

Updated canonical areas include:

- current accepted milestone;
- current main baseline;
- active maintenance milestone;
- next implementation milestone;
- current Backend/Architecture/QA handoffs;
- project continuity bootstrap;
- project state JSON;
- open questions resolved by the accepted contract.

## Warnings intentionally left alone

Warnings in old milestone, review, design, role-bootstrap, workflow-contract, or archived continuity files are accepted historical/archive noise unless they contradict the current canonical files or are explicitly selected for a future targeted cleanup.

Examples include warnings tied to older Daily Coach async/provider, Weekly Coach, and historical review documents. Those files preserve historical milestone context and should not be rewritten only to satisfy phrase checks.

## Serving-unit implementation remains deferred

This review does not implement serving-unit logging.

The accepted future design remains:

```text
canonical_food_id + serving_unit_id + serving_quantity
-> backend resolves grams
-> backend writes resolved grams to food_entries
-> backend writes companion provenance metadata
-> Target-vs-Actual remains grams-based
```

## Scope confirmation

No runtime behavior should change in this milestone.

No Python, API, Streamlit, schema, provider, Target-vs-Actual, food suggestion, meal planning, workout, recovery, or report files should be changed.

## Recommended next milestone

Nutrition Serving Unit Logging Backend v1.

Expected owner: Backend Development / Data Layer.

Expected future scope:

- add backend service/endpoint for `canonical_food_id` + `serving_unit_id` + quantity;
- resolve serving-unit quantity to grams using backend-owned serving-unit metadata;
- persist `food_entries` grams row for actuals compatibility;
- persist companion serving-unit provenance metadata;
- preserve existing raw/canonical grams logging behavior;
- keep Target-vs-Actual behavior stable;
- no Streamlit changes until backend is accepted;
- no AI/provider involvement.
