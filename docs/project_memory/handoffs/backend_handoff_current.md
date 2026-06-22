## Backend Handoff — Daily Coach Async Provider Runtime QA Hardening v1

Status: `AUTHORIZED FOR BACKEND / QA IMPLEMENTATION`

Branch: `feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Scope: harden Developer Mode-only provider runtime failure behavior. Preserve manual trigger only, disabled by default, no provider call on page load, no normal Today provider call, no public async narrative display, no worker/queue/scheduler/polling, no qwen3/qwen3:32b promotion, and no raw/rejected output or prompt/context/scratchpad persistence/display.

## Current Implementation Update — Developer Mode Persistence Inspection v1

Status: `AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION`

Branch: `feature/developer-mode-persistence-inspection-v1`

Latest accepted milestone: `Daily Coach Async Persistence Service Shell v1`

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED`

This milestone adds Developer Mode-only read-only inspection of persisted Daily Coach async job and approved narrative state. It may show sanitized persistence metadata and displayable/public_safe approved narrative content inside Developer Mode only. It must not add provider runtime, worker/queue/scheduler/polling, automatic async job creation, normal Today provider calls, public async narrative display, raw provider output display, rejected provider output display, full prompt/raw context/scratchpad display, or debug/provider metadata in normal UI.

Codex do not use by default.

## Current Implementation Update — Daily Coach Async Persistence Service Shell v1

Status: `AUTHORIZED FOR BACKEND IMPLEMENTATION`

Branch: `feature/daily-coach-async-persistence-service-shell-v1`

Latest accepted milestone: `Daily Coach Async Persistence Contracts + Schema v1`

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

This milestone adds a bounded deterministic service/repository shell around the accepted `daily_coach_async_jobs` and `daily_coach_approved_narratives` schema. It is service/repository shell only: no provider runtime, no worker/queue/scheduler, no FastAPI behavior change, no Streamlit behavior change, no normal Today provider call, no public async narrative display, no raw provider output persistence, and no rejected provider output persistence.

Codex do not use by default.

# Backend Handoff Current

Current milestone: Daily Coach Async Persistence Contracts + Schema v1

Status: IMPLEMENTED / READY FOR BACKEND REVIEW

Branch: `feature/daily-coach-async-persistence-contracts-schema-v1`

Latest accepted milestone: Daily Coach Async Persistence Design v1

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## Backend scope

This is a schema/contracts foundation milestone.

Backend should review the SQLite schema and model constants only. This branch must not add repositories, services, API routes, provider runtime, workers, queues, schedulers, polling, Streamlit behavior, public async narrative display, or normal Today behavior changes.

## Files expected to change

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

## Validation expectation

Use focused code validation:

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

## Boundary reminder

No product/runtime behavior should change. No provider output, rejected provider output, full prompt, raw context, scratchpad, traceback, secrets, or environment values should be persisted.

Codex is implementation worker only and cannot merge, push main, snapshot, touch Linux, use `git add .`, or decide architecture.

---

## Daily Coach Async Provider Runtime Prototype v1

Status: AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION

Branch: `feature/daily-coach-async-provider-runtime-prototype-v1`

Developer Mode-only manual provider runtime prototype. Provider runtime is disabled by default, manual-trigger only, and must not run on normal Today render or page load. Approved public-safe narrative persistence is allowed only after strict JSON parse and safety validation. Failure paths may persist sanitized metadata only. No qwen3 bridge, qwen3 promotion, qwen3:32b promotion, worker, queue, scheduler, polling, public async narrative display, raw provider output persistence, rejected provider output persistence, full prompt/raw context/scratchpad persistence, or debug/provider metadata in normal UI. Codex do not use by default.
