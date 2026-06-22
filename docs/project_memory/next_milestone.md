# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Persistence Design v1

## Latest accepted status

`DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_898abe0_merge-feature-daily-coach-async-persistence-design-v1.zip`

Prior accepted milestone:

- Project Continuity System v2
- `PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

## Current authorized milestone

Daily Coach Async Persistence Contracts + Schema v1

Status:

`AUTHORIZED / CODEX-ASSISTED IMPLEMENTATION`

Required implementation branch:

`feature/daily-coach-async-persistence-contracts-schema-v1`

Milestone type:

schema/contracts foundation only

Expected recipient:

Codex implementation worker, then Backend Development review, then Architecture review.

Expected validation type:

Focused schema/contract tests, project-memory checks, diff checks, focused Python compile, focused Ruff/Black checks, and `scripts/dev_commit_check.ps1 -Mode code`.

## Why this is current

Daily Coach Async Persistence Design v1 is accepted. The next bounded step is to create the durable storage foundation for future async Daily Coach jobs and approved narratives, without implementing any provider runtime, worker, queue, scheduler, repository/service behavior, API behavior, Streamlit behavior, or normal Today behavior.

This milestone is intentionally narrow:

- add `daily_coach_async_jobs`
- add `daily_coach_approved_narratives`
- keep `daily_coach_job_events` deferred
- add persistence contract constants
- add schema/contract tests
- update project memory

## Recommended next milestone after acceptance

Daily Coach Async Persistence Service Shell v1

Status:

`NOT_AUTHORIZED_YET`

The service shell milestone should remain blocked until Daily Coach Async Persistence Contracts + Schema v1 is reviewed and accepted.

## Not authorized yet

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- repository/service write behavior
- API routes
- Streamlit behavior changes
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence
- debug/provider metadata in normal UI

## Codex-assisted flow reminder

Codex is implementation worker only. Codex cannot decide architecture, merge, push main, snapshot, touch Linux, use `git add .`, or broaden scope beyond the implementation packet.
