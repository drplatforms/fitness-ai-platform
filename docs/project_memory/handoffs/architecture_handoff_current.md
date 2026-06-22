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

# Architecture Handoff Current

Current milestone: Daily Coach Async Persistence Contracts + Schema v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: `DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

Branch: `feature/daily-coach-async-persistence-contracts-schema-v1`

Latest accepted milestone: Daily Coach Async Persistence Design v1

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## Summary

Daily Coach Async Persistence Contracts + Schema v1 implements the storage foundation authorized by the accepted persistence design.

This milestone creates schema/contracts only. It does not implement provider runtime, workers, queues, schedulers, polling, repositories, services, API routes, Streamlit behavior, public async narrative display, or normal Today behavior changes.

## Deliverables

- `daily_coach_async_jobs` table in `database.initialize_database()`
- `daily_coach_approved_narratives` table in `database.initialize_database()`
- `daily_coach_job_events` deferred
- Daily Coach async persistence table/column/forbidden-field contract constants
- focused schema/contract tests
- project-memory updates and checks

## Architecture review focus

Confirm that the schema/contracts correctly preserve:

- no provider runtime
- no direct_ollama Daily Coach async runtime
- no CrewAI Daily Coach async runtime
- no qwen3 bridge
- no qwen3 or qwen3:32b promotion
- no worker / queue / scheduler / polling
- no API or Streamlit behavior change
- no normal Today behavior change
- no raw provider output persistence
- no rejected provider output persistence
- no full prompt/raw context/scratchpad persistence
- deterministic fallback
- model/provider policy

## Boundary confirmation

- schema/contracts only: CONFIRMED
- `daily_coach_async_jobs` implemented: CONFIRMED
- `daily_coach_approved_narratives` implemented: CONFIRMED
- `daily_coach_job_events` deferred: CONFIRMED
- no provider runtime implemented: CONFIRMED
- no direct_ollama call added: CONFIRMED
- no CrewAI call added: CONFIRMED
- no qwen3 call added: CONFIRMED
- no qwen3 bridge added: CONFIRMED
- no qwen3:32b promotion: CONFIRMED
- no worker / queue / scheduler / polling added: CONFIRMED
- no normal Today provider call added: CONFIRMED
- no public async narrative display added: CONFIRMED
- deterministic fallback preserved: CONFIRMED
- model/provider policy preserved: CONFIRMED
- raw provider output persistence forbidden: CONFIRMED
- rejected provider output persistence forbidden: CONFIRMED

## Recommended next milestone after acceptance

Daily Coach Async Persistence Service Shell v1.
