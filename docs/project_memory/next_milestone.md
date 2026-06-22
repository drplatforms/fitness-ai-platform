# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Persistence Contracts + Schema v1

## Latest accepted status

`DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_45522b1_merge-feature-daily-coach-async-persistence-contracts-schema-v1.zip`

Prior accepted milestone:

- Daily Coach Async Persistence Design v1
- `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## Current authorized milestone

Daily Coach Async Persistence Service Shell v1

Status:

`AUTHORIZED FOR BACKEND IMPLEMENTATION`

Codex:

`DO NOT USE BY DEFAULT`

Required implementation branch:

`feature/daily-coach-async-persistence-service-shell-v1`

Milestone type:

service/repository shell only

Expected recipient:

Backend Development.

Expected validation type:

Focused service-shell tests, schema/contract tests, async narrative contract tests, project-memory checks, diff checks, focused Python compile, focused Ruff/Black checks, and `scripts/dev_commit_check.ps1 -Mode code`.

## Why this is current

Daily Coach Async Persistence Contracts + Schema v1 is accepted. The next bounded step is to exercise the durable storage foundation through deterministic backend-owned persistence methods, without implementing provider runtime, worker, queue, scheduler, API behavior, Streamlit behavior, normal Today provider calls, or public async narrative display.

This milestone is intentionally narrow:

- create/read `daily_coach_async_jobs`
- update allowed lifecycle/status fields
- mark stale/expired/displayable/public_safe state explicitly
- record sanitized fallback/failure/provider metadata
- create/read `daily_coach_approved_narratives`
- reject raw provider output persistence
- reject rejected provider output persistence
- update project memory

## Recommended next milestone after acceptance

Developer Mode Persistence Inspection v1

Status:

`NOT_AUTHORIZED_YET`

The Developer Mode inspection milestone should remain blocked until Daily Coach Async Persistence Service Shell v1 is reviewed and accepted.

## Not authorized yet

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- FastAPI provider execution routes
- Streamlit behavior changes
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence
- debug/provider metadata in normal UI

## Codex reminder

Codex do not use by default. This project has returned to chat-driven Backend implementation unless the user explicitly opts into a tightly bounded exceptional Codex task.
