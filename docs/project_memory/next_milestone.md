# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Provider Runtime QA Hardening v1

## Latest accepted status

`DAILY_COACH_ASYNC_PROVIDER_RUNTIME_QA_HARDENING_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge commit:

`3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_3765314_merge-feature-daily-coach-async-provider-runtime-qa-hardening-v1.zip`

## Current authorized milestone

Daily Coach Async Approved Preview Bridge Design v1

Status:

`AUTHORIZED FOR DESIGN / BACKEND ARCHITECTURE SUPPORT`

Codex:

`DO NOT USE BY DEFAULT`

Required branch:

`feature/daily-coach-async-approved-preview-bridge-design-v1`

Milestone type:

Design/docs-only architecture support milestone.

Expected validation type:

Docs-only validation, project-memory checks, project-memory test, continuity brief, `scripts/dev_commit_check.ps1 -Mode docs-only`, and fsweep. Runtime restart is not required.

## Why this is current

Daily Coach Async Provider Runtime QA Hardening v1 is accepted. The next safe layer is not turning provider output on in Today. The next safe layer is defining strict bridge rules for how an already-approved, already-validated, already-persisted async narrative could eventually appear as a controlled Today preview.

## Recommended next milestone after acceptance

Daily Coach Async Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default

Status:

`NOT_AUTHORIZED_YET`

## Not authorized

- Today preview bridge implementation before this design is accepted
- normal Today provider call
- provider execution on Today render
- provider execution on page load
- automatic async job generation
- public/default async narrative display
- worker / queue / scheduler / polling
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- raw provider output display or persistence
- rejected provider output display or persistence
- full prompt/raw context/scratchpad display or persistence
- debug/provider metadata in normal UI

## Codex reminder

Codex do not use by default. This project uses chat-driven Backend implementation with apply scripts/patches unless the user explicitly opts into a tightly bounded exceptional Codex task.
