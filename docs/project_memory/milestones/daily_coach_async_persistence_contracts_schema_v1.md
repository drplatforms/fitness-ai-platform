# Daily Coach Async Persistence Contracts + Schema v1

## Status

AUTHORIZED / CODEX-ASSISTED IMPLEMENTATION

## Source baseline

Source branch: `main`

Expected source baseline:

`898abe0 Merge feature/daily-coach-async-persistence-design-v1`

Latest accepted milestone:

`Daily Coach Async Persistence Design v1`

Latest accepted status:

`DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## Branch

`feature/daily-coach-async-persistence-contracts-schema-v1`

## Goal

Implement the durable persistence schema/contracts for Daily Coach async jobs and approved narratives.

This milestone creates the storage foundation only.

## Scope

In scope:

- `daily_coach_async_jobs`
- `daily_coach_approved_narratives`
- Daily Coach async persistence table constants
- Daily Coach async required column constants
- Daily Coach async forbidden persistence field constants
- `expired` in the Daily Coach async job status contract
- focused schema/contract tests
- project-memory updates and checks

Deferred:

- daily_coach_job_events deferred
- Daily Coach Async Persistence Service Shell v1

## Files changed / expected files

- `database.py`
- `models/async_daily_coach_narrative_models.py`
- `tests/test_daily_coach_async_persistence_contracts_schema_v1.py`
- `tests/test_async_daily_coach_narrative_contracts_v1.py`
- `tests/test_project_memory_check.py`
- `tools/project_memory_check.py`
- `docs/project_memory/project_state.json`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `docs/project_memory/milestones/daily_coach_async_persistence_contracts_schema_v1.md`
- `docs/project_memory/reviews/daily_coach_async_persistence_contracts_schema_v1.md`

## Schema/contracts implemented

`daily_coach_async_jobs` stores durable async Daily Coach job lifecycle state, context identity/version, display safety state, fallback state, sanitized provider metadata, and timestamps.

`daily_coach_approved_narratives` stores approved public-safe Daily Coach async narrative payloads after parser/schema/claim validation only.

The schema must not include raw provider output, rejected provider output, full prompt, raw context, scratchpad, traceback, secrets, or environment values.

## Non-goals

- no provider runtime
- no direct_ollama calls
- no CrewAI calls
- no qwen3 bridge/promotion
- no qwen3:32b promotion
- no worker/queue/scheduler
- no polling
- no API/UI behavior change
- no normal Today behavior change
- no public async narrative display
- no raw provider output persistence
- no rejected provider output persistence
- no repository/service write behavior
- no migration framework

## Validation plan

Run:

- `git diff --check`
- `pytest tests/test_daily_coach_async_persistence_contracts_schema_v1.py -q`
- `pytest tests/test_async_daily_coach_narrative_contracts_v1.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- `python tools/project_memory_check.py`
- `python tools/dev_assistant.py continuity-brief`
- `scripts/dev_commit_check.ps1 -Mode code`
- focused `ruff check`
- focused `black --check`
- focused `python -m py_compile`
- `fsweep`

## Boundary confirmation

- Backend owns facts, calculations, validation, persistence, and fallback.
- AI/provider paths may explain backend-approved truth only.
- Deterministic fallback remains mandatory.
- Provider behavior remains gated, manual, opt-in, or debug-only unless a future Architecture milestone promotes it.
- qwen3 and qwen3:32b remain unpromoted.
- Normal Today behavior remains unchanged.
- raw provider output must not be persisted.
- rejected provider output must not be persisted.
- daily_coach_job_events deferred.

## Expected final status

`DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`
