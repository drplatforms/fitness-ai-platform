# Project Continuity Bootstrap

Last updated: 2026-06-22

## 1. Purpose

This file is the project-wide continuity landing packet for future AI Health Coach chats.

Use it before making Architecture, Backend Development, QA, DevOps / Tooling, Product, or TPM-style decisions. It exists so future chats can rehydrate from repo truth instead of scattered transcript memory.

Project Continuity System v2 adds an active continuity control layer around this packet:

- `docs/project_memory/project_state.json`
- `docs/project_memory/current_workflow_contract.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/chat_onboarding_test.md`
- role-specific bootstrap files for Architecture, Backend, QA, and DevOps / Tooling
- `python tools/dev_assistant.py continuity-brief`

## 2. Latest accepted baseline

Current accepted baseline:

`Project Continuity System v2`

Accepted status:

`PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

Accepted commit/snapshot:

- Feature commit: `4195f55 Add project continuity system v2`
- Main merge commit: `c30c833 Merge feature/project-continuity-system-v2`
- Main snapshot: `fitness_ai_snapshot_2026-06-22_c30c833_merge-feature-project-continuity-system-v2.zip`

Project Continuity System v2 is docs + tooling only. It did not implement provider runtime, persistence, public UI display, worker execution, model promotion, or normal Today provider calls.

## 3. Current authorized milestone

`Daily Coach Async Persistence Design v1`

Status:

`AUTHORIZED FOR ARCHITECTURE / DESIGN`

Required branch:

`feature/daily-coach-async-persistence-design-v1`

Required deliverable:

- `docs/project_memory/designs/daily_coach_async_persistence_design_v1.md`

This milestone must define durable async job/narrative storage boundaries before any provider runtime implementation begins.

It must not implement DB schema, migrations, tables, repositories, services, API routes, Streamlit behavior, provider runtime, worker/queue/scheduler/polling, or model changes.

## 4. Current accepted milestone stack

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

## 5. Current product vision

AI Health Coach is a backend-truth, validation-first, premium coaching platform.

Core product doctrine:

`Sound right and be right.`

System doctrine:

Backend owns facts, health state, recovery state, nutrition targets, logged actuals, macro gaps, workout constraints, training evidence, food suggestions, validation, persistence, and fallback.

Provider / AI owns natural language, tone, synthesis, explanation, and premium-feeling coaching copy.

Validator owns what is safe to show.

Public UI owns rendering approved fields and hiding debug/runtime/provider internals unless explicitly in Developer Mode.

## 6. Runtime split

Windows:

- source-of-truth repo/control machine
- Git / merge / snapshot / orchestration
- Ollama host

Linux:

- canonical FastAPI + Streamlit runtime
- tmux sessions `fitness-api` and `fitness-ui`
- `app` command launches Linux runtime
- `wapp` is Windows-local only
- Linux runtime uses Windows Ollama over LAN

Canonical paths:

- Windows repo: `C:\projects\fitness_ai`
- Linux repo: `~/projects/fitness-ai-platform`

Do not change this runtime split without an explicit DevOps / Architecture milestone.

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
python ..\apply_example.py
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
- Project Continuity System v2 accepted
- persistence design authorized

Not implemented / not authorized:

- provider runtime implementation
- direct Ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 call or qwen3 bridge
- worker
- queue
- scheduler
- polling
- DB persistence implementation
- `daily_coach_async_jobs` table
- `daily_coach_approved_narratives` table
- provider cache table
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence

## 10. What future chats must do first

Every new chat should read:

1. `docs/project_memory/project_state.json`
2. `docs/project_memory/project_continuity_bootstrap.md`
3. `docs/project_memory/current_workflow_contract.md`
4. `docs/project_memory/next_milestone.md`
5. the relevant role bootstrap
6. `docs/project_memory/current_state.md`
7. `docs/project_memory/open_questions.md`

Then answer the self-test in `docs/project_memory/chat_onboarding_test.md` before authorizing work or producing patches.
