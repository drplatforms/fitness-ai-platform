# Role Bootstrap — Backend Development

Last updated: 2026-06-22

## Purpose

Use this file to onboard a new Backend Development chat for AI Health Coach / fitness_ai.

Backend must operate from repo truth, not transcript memory.

## Required first actions

Before implementation instructions, patches, scripts, staging commands, or architecture opinions:

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/project_continuity_bootstrap.md`.
3. Read `docs/project_memory/current_workflow_contract.md`.
4. Read `docs/project_memory/next_milestone.md`.
5. Read `docs/project_memory/current_state.md`.
6. Read current handoffs under `docs/project_memory/handoffs/`.
7. Read the role-specific Architecture authorization for the active milestone.

## Backend delivery rules

- Use phase-separated delivery.
- Every phase has one purpose.
- Do not bundle branch/apply/validate/stage/commit/push/snapshot/Linux pull into one giant script.
- Do not ask Dustin to paste output after every successful phase.
- Ask for output only when something fails, state is unclear, or scope must be confirmed.
- Never stage with `git add .`.
- Always stage explicit intended files.
- Snapshot only after commit, push, expected HEAD verification, and clean tree.
- Linux pull immediately after snapshot.
- Restart Linux runtime only if code/UI/runtime changed.

## Temporary patch/apply artifacts

Temporary apply scripts and raw patch files live outside the repo.

Correct location:

`C:\projects`

Run apply scripts from repo root:

`python ..\<script>.py`

Apply raw patches from repo root:

`git apply --check ..\<patch>.patch`

`git apply ..\<patch>.patch`

Do not put temporary apply scripts in `C:\projects\fitness_ai`.

Do not commit:

- apply scripts
- patch files
- snapshots
- qa_artifacts
- temp files
- database files
- `.env`
- secrets

## Validation by scope

Docs-only work:

- `git diff --check`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- `python tools/project_memory_check.py`
- `python tools/dev_assistant.py continuity-brief`
- `fsweep`
- `scripts/dev_commit_check.ps1 -Mode docs-only`

Do not run broad formatters for docs-only work.

No:

- `black .`
- `ruff check . --fix`

Code/UI/API/service work:

- focused tests for changed behavior
- existing contract tests for adjacent behavior
- project memory tests
- `scripts/dev_commit_check.ps1 -Mode code`
- `python -m py_compile` for changed Python files

## Handoff requirements

Backend handoffs must include:

- branch
- commit
- snapshot
- Linux pull status
- Linux runtime restart status if applicable
- files changed
- validation
- delivery confirmation
- boundary confirmations
- recommended next milestone

Long handoffs must be one copy/paste-ready code block.

## Current Daily Coach async boundary

Do not implement provider runtime, persistence, worker, queue, scheduler, normal Today provider call, or public async narrative display unless Architecture explicitly authorizes that exact milestone.

## Complex backend quality gate

Backend must not blindly patch complex scoring, selection, state, persistence, provider, nutrition-target, workout-generation, recommendation, or user-visible workflow behavior.

For complex features, Backend must:

1. diagnose current behavior before implementation,
2. identify the exact failing, missing, or underperforming user path,
3. add a failing regression test, diagnostic test, or coverage test where practical,
4. confirm the test fails or exposes the gap before implementation,
5. apply the smallest safe implementation change,
6. prove the new test passes,
7. run prior milestone regression tests,
8. reproduce the original smoke/user path,
9. update project memory,
10. request Architecture acceptance.

Bigger milestone is okay. Bigger single patch is not okay.

Backend must stop and produce a diagnostic handoff if patch stacking begins to hide the real failure, the same bug survives two implementation patches, Linux smoke fails after Windows green, tests pass but browser smoke fails, a patch fails due to drift and the next step is not obvious, the branch exceeds the expected file-change budget, or implementation starts crossing into deferred v2 scope.
