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

# Current Project State

Last updated: 2026-06-22

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`feature/daily-coach-async-persistence-contracts-schema-v1`

## Current active milestone

`Daily Coach Async Persistence Contracts + Schema v1`

Status: `AUTHORIZED / CODEX-ASSISTED IMPLEMENTATION`

Purpose: implement the durable schema/contracts foundation for future Daily Coach async jobs and approved narratives.

This milestone is schema/contracts only. It does not implement provider runtime, workers, queues, schedulers, polling, repositories, services, API routes, Streamlit behavior, public async narrative display, or normal Today behavior changes.

## Latest accepted baseline

Latest accepted milestone: `Daily Coach Async Persistence Design v1`

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

Latest accepted main merge commit: `898abe0 Merge feature/daily-coach-async-persistence-design-v1`

Latest accepted main snapshot: `fitness_ai_snapshot_2026-06-22_898abe0_merge-feature-daily-coach-async-persistence-design-v1.zip`

Prior accepted milestone: `Project Continuity System v2`

Prior accepted status: `PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

## Current Accepted Milestone Stack

Accepted Daily Coach async / runtime-control / continuity stack:

1. Local Developer Command Menu App Runtime Correction v1
2. Async Daily Coach Narrative Design v1
3. Async Daily Coach Narrative Implementation Plan v1
4. Daily Coach Async Contracts + Data Model v1
5. Daily Coach Async Service Shell / No Worker v1
6. Project Memory Transition Packet v1
7. Daily Coach Async Developer-Only Prototype v1
8. Daily Coach Async Provider Runtime Design v1
9. Project Continuity System v2
10. Daily Coach Async Persistence Design v1

`docs/project_memory/project_state.json` is the compact machine-readable current-state control file.

`docs/project_memory/project_continuity_bootstrap.md` remains the project-wide continuity landing packet for future Architecture, Backend Development, QA, DevOps / Tooling, Product, and TPM-style coordination chats.

`docs/project_memory/current_workflow_contract.md` is the canonical phase-separated delivery workflow contract.

## Daily Coach Async Persistence Design v1 status

Daily Coach Async Persistence Design v1 is accepted.

Accepted outcome:

- durable async job persistence boundary defined
- approved narrative persistence boundary defined
- raw provider output persistence forbidden
- rejected provider output persistence forbidden
- public-safe metadata policy defined
- stale/expired/displayable state handling designed
- context hash/versioning strategy designed
- Developer Mode vs normal Today boundary preserved

Design-only boundary preserved:

- no DB schema implemented in the design milestone
- no provider runtime implemented
- no direct_ollama call added
- no CrewAI call added
- no qwen3 call or bridge added
- no qwen3:32b promotion
- no worker / queue / scheduler / polling added
- no normal Today provider call
- no public async narrative display

## Daily Coach Async Persistence Contracts + Schema v1 status

Daily Coach Async Persistence Contracts + Schema v1 is authorized on:

`feature/daily-coach-async-persistence-contracts-schema-v1`

Scope:

- create `daily_coach_async_jobs`
- create `daily_coach_approved_narratives`
- defer `daily_coach_job_events`
- update Daily Coach async persistence contract constants
- add focused schema/contract tests
- update project memory and project-memory checks

This creates storage foundation only. It must not write/read production rows outside tests and must not add repositories, services, API behavior, Streamlit behavior, provider runtime, workers, queues, schedulers, or polling.

## Daily Coach async current boundary

Current Daily Coach async boundary: contracts plus service shell plus Developer Mode-only manual lifecycle prototype plus provider runtime design plus accepted persistence design plus authorized schema/contracts foundation.

Normal Today behavior remains unchanged. There is still no provider runtime implementation, no worker, no queue, no scheduler, no repository/service write behavior, no normal Today provider call, no public Streamlit async display, no qwen3 promotion, and no qwen3 bridge.

## Explicitly not authorized

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- repositories / services
- API routes
- Streamlit behavior changes
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence
- debug/provider metadata in normal UI

## Codex-assisted implementation boundary

Codex is implementation worker only.

Codex cannot:

- decide architecture
- broaden milestone scope
- merge
- push main
- snapshot
- touch Linux
- use `git add .`

Backend/user owns review, validation, explicit staging, commit, push, snapshot, Linux pull, and Architecture handoff after Codex finishes.

## Next after this milestone

If Daily Coach Async Persistence Contracts + Schema v1 is accepted, the recommended next milestone is:

`Daily Coach Async Persistence Service Shell v1`

Status: `NOT_AUTHORIZED_YET`

## Definition of Done update

Project memory is a first-class system component.

A feature branch or milestone is not done until the relevant project memory docs reflect:

- what changed
- what did not change
- what is accepted
- what remains parked
- what is explicitly not approved
- what future agents must not assume

Any meaningful commit that changes behavior, architecture boundaries, provider behavior, persistence, routing, UI, tests, accepted status, or project scope must update project memory in the same branch.

Memory drift is architecture drift.

## Historical notes

Older accepted and reference-only milestones remain documented in milestone/review/runtime QA files under `docs/project_memory/`.

The prior `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` branch remains reference-only and not accepted.

Provider Narrative QA Matrix v2 is developer-only QA tooling and project memory. It characterizes model behavior through the existing manual Developer Mode provider-preview debug route and does not affect normal Today behavior.
