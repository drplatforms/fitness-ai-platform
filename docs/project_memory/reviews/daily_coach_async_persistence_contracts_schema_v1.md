# Daily Coach Async Persistence Contracts + Schema v1

## Status

IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Proposed final status

`DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

## Summary

Daily Coach Async Persistence Contracts + Schema v1 implements the storage foundation for future async Daily Coach jobs and approved narratives.

The branch adds the `daily_coach_async_jobs` and `daily_coach_approved_narratives` SQLite tables through `database.initialize_database()`, updates the Daily Coach async job status contract with `expired`, adds persistence contract constants, and adds focused schema/contract tests.

No provider runtime, worker, queue, scheduler, polling, repository/service behavior, API behavior, Streamlit behavior, public async narrative display, normal Today behavior change, raw provider output persistence, or rejected provider output persistence is added.

## Files changed

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

## Validation

Expected validation:

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

- `daily_coach_async_jobs`: implemented
- `daily_coach_approved_narratives`: implemented
- `daily_coach_job_events`: deferred
- no provider runtime
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3 bridge
- no qwen3:32b promotion
- no worker
- no queue
- no scheduler
- no polling
- no API behavior change
- no Streamlit behavior change
- no normal Today behavior change
- no public async narrative display
- no raw provider output persistence
- no rejected provider output persistence
- no full prompt/raw context/scratchpad persistence
- deterministic fallback preserved
- model/provider policy preserved

## Architecture review request

Architecture should review the schema/contracts diff and confirm whether the branch may proceed to explicit staging, commit, push, snapshot, Linux pull, and the next handoff.

## Next recommended milestone

Daily Coach Async Persistence Service Shell v1
