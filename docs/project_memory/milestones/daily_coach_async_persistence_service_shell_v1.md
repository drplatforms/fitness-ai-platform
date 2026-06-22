# Daily Coach Async Persistence Service Shell v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Source baseline: `45522b1 Merge feature-daily-coach-async-persistence-contracts-schema-v1`

Branch: `feature/daily-coach-async-persistence-service-shell-v1`

Expected final status: `DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED`

## Goal

Implement a bounded deterministic persistence service/repository shell around the accepted Daily Coach async job and approved narrative schema.

## Scope

In scope:

- create and read `daily_coach_async_jobs`
- update allowed lifecycle/status fields
- mark jobs stale, expired, displayable, and public-safe through explicit backend methods
- record sanitized fallback/failure/provider metadata
- create and read `daily_coach_approved_narratives`
- require approved narrative input to be public-safe
- reject raw provider output persistence
- reject rejected provider output persistence
- focused service-shell tests

## Service shell implemented

`services/daily_coach_async_persistence_service.py`

The service shell is deterministic persistence code only. It does not start provider execution, schedule work, call a model, expose an API route, or display anything in Streamlit.

## Non-goals

- no provider runtime
- no direct_ollama Daily Coach async runtime
- no CrewAI Daily Coach async runtime
- no qwen3 bridge
- no qwen3 promotion
- no qwen3:32b promotion
- no worker
- no queue
- no scheduler
- no polling
- no FastAPI behavior change
- no Streamlit behavior change
- no normal Today behavior change
- no public async narrative display
- no raw provider output persistence
- no rejected provider output persistence
- no full prompt/raw context/scratchpad persistence
- no job event/history persistence

## Validation plan

- `git diff --check`
- `pytest tests/test_daily_coach_async_persistence_service_shell_v1.py -q`
- `pytest tests/test_daily_coach_async_persistence_contracts_schema_v1.py -q`
- `pytest tests/test_async_daily_coach_narrative_contracts_v1.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
- `python tools/project_memory_check.py`
- `python tools/dev_assistant.py continuity-brief`
- `scripts/dev_commit_check.ps1 -Mode code`
- focused Ruff/Black/py_compile
- `fsweep`

## Boundary confirmation

- service/repository shell only
- no provider runtime
- no raw provider output persistence
- no rejected provider output persistence
- deterministic fallback remains mandatory
- model/provider policy preserved
- Codex do not use by default
