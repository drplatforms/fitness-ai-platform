# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only

## Latest accepted status

`DAILY_COACH_ASYNC_PROVIDER_RUNTIME_PROTOTYPE_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_ea3f93f_fix-provider-runtime-config-default-isolation.zip`

## Current authorized milestone

Daily Coach Async Provider Runtime QA Hardening v1

Status:

`AUTHORIZED FOR BACKEND / QA IMPLEMENTATION`

Codex:

`DO NOT USE BY DEFAULT`

Required implementation branch:

`feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Milestone type:

Developer Mode-only provider runtime QA hardening.

Expected validation type:

Focused QA hardening tests, provider runtime prototype tests, Streamlit Developer Mode provider tests, Developer Mode persistence inspection tests, persistence service shell tests, schema/contract tests, async narrative contract tests, project-memory checks, diff checks, focused Python compile, focused Ruff/Black checks, `scripts/dev_commit_check.ps1 -Mode code`, fsweep, Linux pull, and manual app smoke only if Developer Mode display changes.

## Why this is current

Daily Coach Async Provider Runtime Prototype v1 is accepted. The next safe layer is hardening failure behavior before any live provider-enabled workflow is promoted or any Today preview bridge is designed.

This milestone is intentionally narrow:

- QA hardening only
- Developer Mode-only runtime remains gated
- manual trigger only remains preserved
- provider disabled by default
- deterministic sanitized failure result objects
- no normal Today behavior change
- no public async narrative display

## Recommended next milestone after acceptance

Daily Coach Async Approved Preview Bridge Design v1

Status:

`NOT_AUTHORIZED_YET`

## Not authorized

- provider runtime outside Developer Mode
- provider call on page load
- normal Today provider call
- public async narrative display
- automatic async job creation outside Developer Mode
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
