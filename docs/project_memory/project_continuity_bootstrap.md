# Project Continuity Bootstrap

Last updated: 2026-06-22

## 1. Purpose

This file is the project-wide continuity landing packet for future AI Health Coach chats.

Use it before making Architecture, Backend Development, QA, DevOps / Tooling, Product, or TPM-style decisions. It exists so future chats can rehydrate from repo truth instead of scattered transcript memory.

This is not an Architecture-only bootstrap file. Do not create or rely on `docs/project_memory/handoffs/new_architecture_chat_bootstrap.md` for project-wide state.

## 2. Latest Accepted Baseline

Current accepted implementation baseline:

`Daily Coach Async Service Shell / No Worker v1`

Baseline commit/snapshot at transition time:

- Commit: `69fbccc Merge feature/daily-coach-async-service-shell-no-worker-v1`
- Snapshot: `fitness_ai_snapshot_2026-06-21_69fbccc_merge-feature-daily-coach-async-service-shell-no-worker-v1.zip`

Accepted status:

`DAILY_COACH_ASYNC_SERVICE_SHELL_NO_WORKER_V1_ACCEPTED`

The accepted baseline before the current branch is a service shell only. The current implementation branch adds a Developer Mode-only manual lifecycle prototype. It still does not authorize provider runtime, public UI display, persistence, worker execution, model promotion, or normal Today provider calls.

## 3. Current Accepted Milestone Stack

Accepted Daily Coach async / runtime-control stack:

1. Local Developer Command Menu App Runtime Correction v1
2. Async Daily Coach Narrative Design v1
3. Async Daily Coach Narrative Implementation Plan v1
4. Daily Coach Async Contracts + Data Model v1
5. Daily Coach Async Service Shell / No Worker v1

The latest accepted implementation baseline before the current branch is Daily Coach Async Service Shell / No Worker v1. Daily Coach Async Developer-Only Prototype v1 is implemented for review on the current feature branch and is not a provider runtime milestone.

## 4. Current Product Vision

AI Health Coach is a backend-truth, validation-first, premium coaching platform.

It is not a generic AI fitness chatbot. It is not a CRUD tracker with AI sprinkled on top. It is a structured coaching system where backend truth, deterministic constraints, validation, fallback, and provider-polished language work together.

Core product doctrine:

`Sound right and be right.`

System doctrine:

Backend owns:

- facts
- health state
- recovery state
- nutrition targets
- logged actuals
- macro gaps
- workout constraints
- training evidence
- food suggestions
- validation
- persistence
- fallback

Provider / AI owns:

- natural language
- tone
- synthesis
- explanation
- premium-feeling coaching copy

Validator owns:

- what is safe to show

Public UI owns:

- rendering approved fields
- hiding debug/runtime/provider internals unless explicitly in Developer Mode

Current architecture pattern:

```text
User data
→ backend-derived health/recovery/nutrition/training state
→ deterministic targets, constraints, evidence, and approved context
→ optional AI/provider candidate
→ strict parser
→ validator
→ approved coaching output or deterministic fallback
→ public-safe UI
```

## 5. Current Runtime Split

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

Canonical paths and URLs:

- Windows repo: `C:\projects\fitness_ai`
- Linux repo: `~/projects/fitness-ai-platform`
- Windows Ollama: `http://127.0.0.1:11434`
- Linux-to-Windows Ollama: `OLLAMA_BASE_URL=http://192.168.1.104:11434`
- Linux Streamlit canonical URL: `http://itsAlwaysDNS:8501`, or the configured Linux Streamlit URL from the command menu
- Windows-local Streamlit escape hatch: `http://127.0.0.1:8510` through `wapp` only

Do not change this runtime split without an explicit DevOps / Architecture milestone.

## 6. Current Command Menu Truth

`app`:

- launches / manages the canonical Linux FastAPI + Streamlit runtime
- uses Linux tmux sessions `fitness-api` and `fitness-ui`
- opens the Linux-hosted Streamlit URL from Windows

`wapp`:

- Windows-local only
- explicit local escape hatch
- not the canonical runtime

`fports`:

- Windows-side port visibility only
- use `lstatus` for Linux app health

`fsweep`:

- must remain clean
- must not allow committed snapshots
- must not allow committed `qa_artifacts`

Project workflow:

Feature branch:

```text
commit -> snapshot -> push -> Linux pull feature
```

Main:

```text
merge -> main snapshot -> push -> Linux pull main
```

Snapshot creation must happen only after commit succeeds, push succeeds, expected HEAD is verified, and the working tree is clean.

## 7. Current Model / Provider Policy

Current policy:

- `qwen2.5:3b` is the bridge baseline only.
- `qwen3:32b` is promising but research / premium async candidate only.
- qwen3 is not bridge-enabled.
- no model is promoted without Architecture approval.
- deterministic fallback remains mandatory.
- backend owns truth.
- provider proposes language.
- validator decides what is display-safe.

Do not:

- promote qwen3
- enable qwen3 bridge behavior
- make qwen3 part of normal Today behavior
- loosen validation to make a model pass
- treat provider output as truth
- expose raw/rejected provider output in normal UI

## 8. Current Daily Coach Async Boundary

Current state after Daily Coach Async Developer-Only Prototype v1 implementation branch:

- accepted service shell remains the core lifecycle boundary
- Developer Mode-only manual route/panel can create and inspect in-memory job shell state
- Developer Mode-only manual simulation can mark stale/expired or approve deterministic test payloads
- normal Today behavior remains unchanged
- no provider runtime yet
- no direct Ollama runtime
- no CrewAI runtime
- no qwen3 call
- no worker
- no queue
- no scheduler
- no polling
- no DB persistence
- no `daily_coach_narrative_jobs` table
- no provider cache table
- no normal Today provider call
- no public Streamlit async display
- no qwen3 promotion
- no qwen3 bridge
- no public async narrative display

The service shell and Developer Mode prototype can create/read/list jobs and evaluate latest/displayable candidates through deterministic service-layer logic. They are not a provider runtime execution system.

## 9. Current Development Doctrine

Docs are first-class architecture.

`docs/project_memory` is part of Definition of Done. Every accepted milestone must preserve:

- architecture boundary
- backend ownership of truth
- deterministic fallback
- parser/validator safety
- QA validation
- clean project memory
- clean working tree
- no committed snapshots
- no committed `qa_artifacts`

Patch-first delivery remains preferred. Snapshot restore is fallback only.

Phase separation is mandatory:

- preflight / branch
- apply only
- validate only
- stage only
- commit only
- push only
- snapshot only
- Linux pull after snapshot

Do not bundle apply, validate, stage, commit, push, and snapshot into one giant script.

## 10. Project Memory / Definition of Done Rules

A milestone is not complete until the relevant project memory docs reflect:

- what changed
- what did not change
- what is accepted
- what remains parked
- what is explicitly not approved
- what future agents must not assume

Commonly updated docs include:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- milestone docs under `docs/project_memory/milestones/`
- review docs under `docs/project_memory/reviews/`
- runtime/command docs when behavior changes

Do not modify accepted historical milestone/review docs unless explicitly authorized by Architecture.

Memory drift is architecture drift.

## 11. Snapshot / Git / Linux Pull Rules

Never commit:

- snapshots
- `qa_artifacts`
- database files
- `.env`
- secrets
- patch files
- apply scripts
- backup files
- temp files
- `.venv`
- raw ChatGPT/file citation residue
- generated artifacts unless explicitly intended

Snapshot must never be in the same script as commit.

After a snapshot is created or received, provide the Linux pull command immediately before long handoff text.

Temporary patch/apply artifacts should be saved outside the repo, normally under:

```text
C:\projects
```

Run apply commands from `C:\projects\fitness_ai`, but reference artifacts outside the repo, for example `..\example.patch` or `..\apply_example.py`. Do not leave temporary apply scripts, patch files, or changed-file zips in the repo root.

Expected snapshot naming pattern:

```text
fitness_ai_snapshot_YYYY-MM-DD_<commit>_<safe-commit-message>.zip
```

Feature branch flow:

```text
commit -> snapshot -> push -> Linux pull feature
```

Main flow:

```text
merge -> main snapshot -> push -> Linux pull main
```

## 12. Current Ownership Lanes

Architecture:

- product/system design
- implementation plans
- milestone boundaries
- acceptance decisions
- non-goal enforcement

Backend Development:

- implementation after Architecture authorization
- services/models/API/tests
- handoff back with validation

QA:

- manual behavior validation
- regression testing
- boundary preservation
- model/provider runtime QA when authorized

DevOps / Tooling:

- command menu
- runtime workflow
- environment
- Windows/Linux split
- Linux pull verification
- `fsweep` / project hygiene

Product / Project Memory:

- continuity docs
- current state
- accepted milestone stack
- handoff clarity
- user-facing product doctrine

## 13. Known Pitfalls / Contradiction Sweep Checklist

Future chats must check for:

1. Windows vs Linux runtime contradictions
2. `app` vs `wapp` confusion
3. qwen3 promotion ambiguity
4. qwen3 bridge ambiguity
5. async runtime implied before it is authorized
6. docs saying implemented when something is only planned
7. stale handoff docs
8. stale `current_state.md` top-summary text
9. old Windows Streamlit `8510` references being treated as canonical runtime
10. snapshots accidentally committed
11. `qa_artifacts` accidentally committed
12. provider output being treated as truth
13. provider/debug/runtime metadata leaking into normal UI
14. deterministic fallback being weakened
15. AI/provider work proceeding without parser + validator boundary

## 14. Current Non-Goals / Not Authorized

This continuity milestone does not authorize:

- backend behavior changes
- FastAPI route changes
- Streamlit changes
- async provider runtime
- worker
- queue
- scheduler
- DB persistence
- normal Today provider call
- Streamlit async display
- Daily Coach async UI
- direct Ollama async runtime
- CrewAI runtime changes
- model promotion
- qwen3 bridge
- report changes
- nutrition changes
- workout changes
- command-menu behavior changes unless a docs contradiction is found
- committed snapshots
- committed `qa_artifacts`

## 15. Recommended Next Milestone

After Project Memory Transition Packet v1 passes and is accepted, the recommended next milestone is:

`Daily Coach Async Developer-Only Prototype v1`

That milestone is not authorized by this file.

Expected future direction:

- developer-only async trigger / preview path
- no normal Today provider call
- no public Streamlit async display
- no qwen3 promotion
- no qwen3 bridge
- no scheduler
- no queue unless separately authorized
- no durable persistence unless separately designed and approved

Architecture should authorize the next milestone only after this continuity cleanup is accepted.

## 16. What Future Chats Must Do First

Before giving implementation instructions, patches, scripts, staging commands, or architectural opinions, future chats must:

1. Read this file.
2. Read `docs/project_memory/current_state.md`.
3. Read `docs/project_memory/open_questions.md`.
4. Read the current Architecture, Backend, and QA handoffs.
5. Read the milestone/review docs relevant to the requested lane.
6. Inspect source files relevant to the requested backend/UI/runtime lane.
7. Produce a short readback covering:
   - current branch / expected branch
   - current milestone
   - accepted constraints
   - files likely in scope
   - files explicitly out of scope
   - validation commands
   - whether the task is safe to proceed

If docs appear contradictory, stop and resolve the contradiction before implementation.
