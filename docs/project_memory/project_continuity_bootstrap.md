# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Current source baseline: `main` at `d74ddec` after Project Memory Warning Review v1 was accepted and merged.

Current authorized milestone: Nutrition Serving Unit Logging Backend v1.

Milestone type: backend implementation / service / endpoint / tests / project memory.

Backend is authorized to add the narrow serving-unit logging path. Streamlit UI, provider/Ollama/CrewAI behavior, Target-vs-Actual behavior/design, nutrition targets, food suggestions, meal planning, workout generation, recovery behavior, and report behavior remain out of scope.

## What Future Chats Must Do First

1. Read this bootstrap.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/project_state.json`.
4. Read `docs/project_memory/next_milestone.md`.
5. Read the current Backend, Architecture, and QA handoffs.
6. Confirm the active branch and source baseline before proposing implementation.
7. Do not infer project rules from memory alone.

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
- Snapshot: `fitness_ai_snapshot_2026-06-26_68ca6c3_nutrition-serving-unit-logging-contract-design-v1.zip`

Accepted contract baseline:

- keep `food_entries` as the grams-based actuals bridge;
- use a future companion serving-unit provenance table;
- prefer `POST /nutrition/{user_id}/log-serving`;
- backend owns grams resolution;
- Target-vs-Actual remains unchanged initially;
- Streamlit must not invent mappings;
- AI/provider must not invent serving units, grams, conversions, macros, or actuals.


### Project Memory Warning Review v1

Accepted and merged.

- Feature commit: `b395e0a`
- Main merge commit: `d74ddec`
- Snapshot: `fitness_ai_snapshot_2026-06-26_b395e0a_review-project-memory-warning-baseline.zip`

Accepted scope: docs-only current project-memory cleanup. Current warning baseline after review: `PASS=620 WARN=28 FAIL=0`. Remaining warnings are accepted as historical/archive/non-actionable continuity noise unless future checks prove otherwise.

## Current implementation milestone

Nutrition Serving Unit Logging Backend v1.

Expected owner: Backend Development / Data Layer.

Expected scope:

- add backend service/endpoint for `canonical_food_id` + `serving_unit_id` + quantity;
- resolve serving-unit quantity to grams using backend-owned serving-unit metadata;
- persist `food_entries` grams row for actuals compatibility;
- persist companion serving-unit provenance metadata;
- preserve existing raw/canonical grams logging behavior;
- keep Target-vs-Actual behavior stable;
- add focused service/API/actuals regression tests;
- no Streamlit changes until backend is accepted;
- no AI/provider involvement.

## Core doctrine

Backend owns truth.

AI/provider may propose or explain only inside validated contracts.

Backend validates and approves.

User sees only approved output.

Deterministic fallback always works.

Sound right and be right.

## Bite by bite, just bigger bites

The permanent development doctrine is:

> Bigger milestone is okay. Bigger single patch is not okay.

Large objectives may be authorized only when internally phased. Single patches remain narrow and tied to a specific diagnostic, test, implementation, or documented process change.

## Complex Backend Quality Gate

For complex features involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior:

1. Diagnose current behavior before patching.
2. Identify the exact failing, missing, or underperforming user path.
3. Add a failing regression test, diagnostic test, or coverage test that captures the real path where practical.
4. Confirm the test fails or exposes the gap before implementation.
5. Apply the smallest safe implementation change.
6. Prove the new test passes.
7. Re-run prior milestone regression tests.
8. Re-run the original manual/browser smoke path.
9. Update project memory.
10. Only then request Architecture acceptance.

## Patch stacking stop conditions

Patch stacking is not the goal.

Backend must stop and return to Architecture if the same bug survives two implementation patches, browser smoke fails after tests pass, Linux smoke fails after Windows green, candidate pools or data shape are unclear, scope expands beyond approval, or the branch begins accumulating unrelated fixes.

## Provider / AI-specific rule

No provider output is accepted unless it is schema-valid, validator-approved, fact-grounded, fallback-safe, and free of invented numbers, invented foods, invented exercises, unsupported health claims, and hidden raw provider output in normal UI.

Provider may propose. Backend validates. User sees only approved output.

No provider may run on normal Today page load.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

The `app` command launches Linux runtime and is now the canonical Linux runtime launcher.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.

## Delivery style

Dustin runs the commands.

Assistants provide copy/paste-ready PowerShell and bash command blocks.

Long handoffs must be one copy/paste-ready code block.

Do not use `git add .`.

Do not commit snapshots, `qa_artifacts`, runtime artifacts, patch files, or temp scripts.

Temporary apply scripts and patch files live outside the repo.

Temporary patch/apply artifacts live outside the repo, normally in `C:\projects`.

Use `python ..\<script>.py` for outside-repo scripts when applicable.

Use `git apply --check ..\<patch>.patch` before applying outside-repo patches.

Windows repo: `C:\projects\fitness_ai`.

Linux runtime repo: `~/projects/fitness-ai-platform`.

Architecture owns merges to `main`.

Backend owns feature-branch implementation, validation, push, snapshot, and handoff.
