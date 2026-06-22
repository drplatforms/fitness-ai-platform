# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Persistence Service Shell v1

## Latest accepted status

`DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_469750c_merge-feature-daily-coach-async-persistence-service-shell-v1.zip`

Prior accepted milestone:

- Daily Coach Async Persistence Contracts + Schema v1
- `DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

## Current authorized milestone

Developer Mode Persistence Inspection v1

Status:

`AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION`

Codex:

`DO NOT USE BY DEFAULT`

Required implementation branch:

`feature/developer-mode-persistence-inspection-v1`

Milestone type:

Developer Mode-only read-only inspection.

Expected recipient:

Backend Development and Streamlit UI.

Expected validation type:

Focused Developer Mode inspection tests, Streamlit developer panel tests, persistence service shell tests, schema/contract tests, async narrative contract tests, project-memory checks, diff checks, focused Python compile, focused Ruff/Black checks, and `scripts/dev_commit_check.ps1 -Mode code`.

## Why this is current

Daily Coach Async Persistence Service Shell v1 is accepted. The next bounded step is to expose sanitized persisted Daily Coach async job and approved narrative state inside Developer Mode only, without introducing provider runtime, worker, queue, scheduler, polling, automatic async job creation, normal Today provider calls, or public async narrative display.

This milestone is intentionally narrow:

- Developer Mode-only inspection
- read-only persisted job inspection
- read-only approved narrative inspection
- sanitized metadata only
- display approved narrative content only when displayable and public_safe
- empty/error states are safe and clear
- update project memory

## Recommended next milestone after acceptance

Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only

Status:

`NOT_AUTHORIZED_YET`

The provider runtime prototype should remain blocked until Developer Mode Persistence Inspection v1 is reviewed and accepted.

## Not authorized yet

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- FastAPI provider execution routes
- normal Today provider call
- public async narrative display
- raw provider output display
- rejected provider output display
- full prompt/raw context/scratchpad display
- debug/provider metadata in normal UI

## Codex reminder

Codex do not use by default. This project has returned to chat-driven Backend implementation unless the user explicitly opts into a tightly bounded exceptional Codex task.
