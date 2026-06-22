# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Developer Mode Persistence Inspection v1

## Latest accepted status

`DEVELOPER_MODE_PERSISTENCE_INSPECTION_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_df088f9_merge-developer-mode-persistence-inspection-closeout.zip`

Prior accepted milestone:

- Daily Coach Async Persistence Service Shell v1
- `DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED`

## Current authorized milestone

Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only

Status:

`AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION`

Codex:

`DO NOT USE BY DEFAULT`

Required implementation branch:

`feature/daily-coach-async-provider-runtime-prototype-v1`

Milestone type:

Developer Mode-only manual provider runtime prototype.

Expected validation type:

Focused provider runtime prototype tests, Streamlit Developer Mode provider tests, Developer Mode persistence inspection tests, persistence service shell tests, schema/contract tests, async narrative contract tests, project-memory checks, diff checks, focused Python compile, focused Ruff/Black checks, `scripts/dev_commit_check.ps1 -Mode code`, fsweep, Linux pull, and manual app smoke.

## Why this is current

Developer Mode Persistence Inspection v1 is accepted. The next safe layer is a manual Developer Mode-only provider runtime prototype that uses the accepted persistence schema, service shell, and inspection surface.

This milestone is intentionally narrow:

- Developer Mode-only
- manual trigger only
- provider disabled by default
- strict JSON parser
- safety validator before persistence
- approved public-safe narrative persistence only
- sanitized failure/fallback metadata only
- no normal Today behavior change
- no public async narrative display

## Recommended next milestone after acceptance

Daily Coach Async Provider Runtime QA Hardening v1

Status:

`NOT_AUTHORIZED_YET`

## Not authorized

- provider runtime outside Developer Mode
- provider call on page load
- normal Today provider call
- public async narrative display
- worker / queue / scheduler / polling
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- raw provider output persistence
- rejected provider output persistence
- full prompt/raw context/scratchpad persistence
- debug/provider metadata in normal UI

## Codex reminder

Codex do not use by default. This project uses chat-driven Backend implementation with apply scripts unless the user explicitly opts into a tightly bounded exceptional Codex task.
