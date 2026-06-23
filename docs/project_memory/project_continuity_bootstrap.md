# Project Continuity Bootstrap

Last updated: 2026-06-22

## 1. Purpose

This file is the project-wide continuity landing packet for future AI Health Coach chats.

Use it before making Architecture, Backend Development, QA, DevOps / Tooling, Product, or TPM-style decisions. It exists so future chats can rehydrate from repo truth instead of scattered transcript memory.

## 2. Latest accepted baseline

Current accepted baseline:

`Daily Coach Async Provider Runtime QA Hardening v1`

Accepted status:

`DAILY_COACH_ASYNC_PROVIDER_RUNTIME_QA_HARDENING_V1_ACCEPTED`

Accepted commit/snapshot:

- Main merge commit: `3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`
- Main snapshot: `fitness_ai_snapshot_2026-06-22_3765314_merge-feature-daily-coach-async-provider-runtime-qa-hardening-v1.zip`

QA Hardening accepted that the Developer Mode-only provider runtime remains disabled by default, manual-trigger only, sanitized on failure, and isolated from normal Today behavior.

## 3. Current authorized milestone

`Daily Coach Async Approved Preview Bridge Design v1`

Status:

`AUTHORIZED FOR DESIGN / BACKEND ARCHITECTURE SUPPORT`

Required branch:

`feature/daily-coach-async-approved-preview-bridge-design-v1`

Required deliverable:

- `docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md`

This milestone is design only. It must not implement Today preview, normal Today provider calls, public async narrative display, automatic async job generation, worker/queue/scheduler/polling, qwen3 bridge/promotion, qwen3:32b promotion, raw/rejected output display, or debug/provider metadata in normal UI.

## 4. Current Accepted Milestone Stack

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
11. Daily Coach Async Persistence Contracts + Schema v1
12. Daily Coach Async Persistence Service Shell v1
13. Developer Mode Persistence Inspection v1
14. Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only
15. Daily Coach Async Provider Runtime QA Hardening v1

## 5. Current product vision

AI Health Coach is a backend-truth, validation-first, premium coaching platform.

Core product doctrine:

`Sound right and be right.`

Backend owns facts, health state, recovery state, nutrition targets, logged actuals, macro gaps, workout constraints, training evidence, food suggestions, validation, persistence, and fallback.

Provider / AI owns natural language, tone, synthesis, explanation, and premium-feeling coaching copy.

Validator owns what is safe to show.

Public UI owns rendering approved fields and hiding debug/runtime/provider internals unless explicitly in Developer Mode.

## 6. Runtime split

Windows:

- source-of-truth repo/control machine
- Git / merge / snapshot / orchestration
- Ollama host
- `app` is a Windows PowerShell command that talks to Linux over SSH and restarts FastAPI + Streamlit there

Linux:

- canonical FastAPI + Streamlit runtime
- tmux sessions `fitness-api` and `fitness-ui`
- Linux runtime uses Windows Ollama over LAN

Canonical paths:

- Windows repo: `C:\projectsitness_ai`
- Linux repo: `~/projects/fitness-ai-platform`

The `app` command launches Linux runtime from Windows PowerShell. `wapp` is Windows-local only.

## 7. Command and workflow truth

Feature branch flow:

```text
commit -> push -> snapshot -> Linux pull feature
```

Main flow:

```text
merge -> validate -> push -> snapshot -> Linux pull main
```

Temporary apply scripts and raw patches live outside the repo, normally in `C:\projects`, and are run from repo root as:

```powershell
python ..pply_example.py
git apply --check ..\example.patch
git apply ..\example.patch
```

Never use `git add .`.

Do not run broad formatters for docs-only work.

Long handoffs must be in one copy/paste-ready code block.

## 8. Current model / provider policy

Current policy:

- `qwen2.5:3b` is the bridge baseline only.
- `qwen3:32b` is research / future premium async candidate only.
- qwen3 is not bridge-enabled.
- no model is promoted without Architecture approval.
- deterministic fallback remains mandatory.
- backend owns truth.
- provider proposes language.
- validator decides what is display-safe.

Do not promote qwen3, enable qwen3 bridge behavior, make qwen3 part of normal Today behavior, loosen validation to make a model pass, treat provider output as truth, expose raw/rejected provider output in normal UI, or persist raw/rejected provider output.

## 9. Current Daily Coach async boundary

Current state:

- accepted contracts/data model
- accepted service shell / no worker
- accepted Developer Mode-only manual lifecycle prototype
- accepted provider runtime design
- accepted persistence design/schema/service shell
- accepted Developer Mode persistence inspection
- accepted Developer Mode-only provider runtime prototype
- accepted provider runtime QA hardening
- authorized approved preview bridge design

Current design focus:

- define future approved preview eligibility gates
- define Today preview boundary
- define provider execution boundary
- define fallback behavior
- define normal UI vs Developer Mode metadata boundary
- define feature flag strategy
- define QA gates before implementation

Deferred / not authorized:

- provider execution from Today
- provider execution on page load
- automatic async job generation
- public/default async narrative display
- worker / queue / scheduler / polling
- qwen3 bridge / qwen3 promotion / qwen3:32b promotion

Historic phrase note: older continuity checks may mention "no provider runtime yet" for early service-shell milestones. Current truth is narrower: Developer Mode-only provider runtime prototype exists, but normal Today provider runtime remains unauthorized.

## 10. What Future Chats Must Do First

1. Read `docs/project_memory/project_state.json`.
2. Read `docs/project_memory/next_milestone.md`.
3. Read `docs/project_memory/current_state.md`.
4. Read the current milestone design, milestone, and review docs.
5. Respect phase-separated delivery.
6. Do not use Codex by default.
7. Do not implement beyond the current authorized milestone.
