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

# Project Continuity Bootstrap

Last updated: 2026-06-22

## 1. Purpose

This file is the project-wide continuity landing packet for future AI Health Coach chats.

Use it before making Architecture, Backend Development, QA, DevOps / Tooling, Product, or TPM-style decisions. It exists so future chats can rehydrate from repo truth instead of scattered transcript memory.

Project Continuity System v2 added an active continuity control layer around this packet:

- `docs/project_memory/project_state.json`
- `docs/project_memory/current_workflow_contract.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/chat_onboarding_test.md`
- role-specific bootstrap files for Architecture, Backend, QA, and DevOps / Tooling
- `python tools/dev_assistant.py continuity-brief`

## 2. Latest accepted baseline

Current accepted baseline:

`Daily Coach Async Persistence Design v1`

Accepted status:

`DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

Accepted commit/snapshot:

- Main merge commit: `898abe0 Merge feature/daily-coach-async-persistence-design-v1`
- Main snapshot: `fitness_ai_snapshot_2026-06-22_898abe0_merge-feature-daily-coach-async-persistence-design-v1.zip`

Daily Coach Async Persistence Design v1 is design only. It did not implement provider runtime, DB schema, repositories, services, API routes, Streamlit behavior, worker execution, model promotion, public async narrative display, or normal Today provider calls.

## 3. Current authorized milestone

`Daily Coach Async Persistence Contracts + Schema v1`

Status:

`AUTHORIZED / CODEX-ASSISTED IMPLEMENTATION`

Required branch:

`feature/daily-coach-async-persistence-contracts-schema-v1`

Required deliverables:

- `daily_coach_async_jobs`
- `daily_coach_approved_narratives`
- `daily_coach_job_events` deferred
- Daily Coach async persistence contract constants
- focused schema/contract tests
- project-memory updates and checks

This milestone creates storage foundation only. It must not implement provider runtime, repositories/services, workers, queues, schedulers, polling, API behavior, Streamlit behavior, public async narrative display, or normal Today behavior changes.

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
- Daily Coach Async Persistence Design v1 accepted
- Daily Coach Async Persistence Contracts + Schema v1 authorized

In current scope:

- `daily_coach_async_jobs` schema
- `daily_coach_approved_narratives` schema
- persistence contract constants
- schema/contract tests
- project-memory updates

Deferred / not implemented:

- `daily_coach_job_events`
- provider runtime implementation
- direct Ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 call or qwen3 bridge
- qwen3:32b promotion
- worker
- queue
- scheduler
- polling
- repositories
- services
- API route behavior
- Streamlit behavior
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence

## 10. Codex-assisted implementation boundary

Codex is implementation worker only.

Codex cannot decide architecture, merge, push main, snapshot, touch Linux, use `git add .`, or broaden scope.

Backend/user owns review, validation, explicit staging, commit, push, snapshot, Linux pull, and final Architecture handoff.

## 11. What Future Chats Must Do First

Every new chat should read:

1. `docs/project_memory/project_state.json`
2. `docs/project_memory/project_continuity_bootstrap.md`
3. `docs/project_memory/current_workflow_contract.md`
4. `docs/project_memory/next_milestone.md`
5. the relevant role bootstrap
6. `docs/project_memory/current_state.md`
7. `docs/project_memory/open_questions.md`

Then answer the self-test in `docs/project_memory/chat_onboarding_test.md` before authorizing work or producing patches.

---

## Daily Coach Async Provider Runtime Prototype v1

Status: AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION

Branch: `feature/daily-coach-async-provider-runtime-prototype-v1`

Developer Mode-only manual provider runtime prototype. Provider runtime is disabled by default, manual-trigger only, and must not run on normal Today render or page load. Approved public-safe narrative persistence is allowed only after strict JSON parse and safety validation. Failure paths may persist sanitized metadata only. No qwen3 bridge, qwen3 promotion, qwen3:32b promotion, worker, queue, scheduler, polling, public async narrative display, raw provider output persistence, rejected provider output persistence, full prompt/raw context/scratchpad persistence, or debug/provider metadata in normal UI. Codex do not use by default.
