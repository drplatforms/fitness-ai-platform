# Current Project State

Last updated: 2026-06-22

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`feature/daily-coach-async-persistence-design-v1`

## Current active milestone

`Daily Coach Async Persistence Design v1`

Status: `AUTHORIZED FOR ARCHITECTURE / DESIGN`

Purpose: define the durable persistence boundary for future Daily Coach async jobs and approved narratives before any provider runtime implementation begins.

This is design only. It does not implement tables, migrations, repositories, services, API routes, Streamlit behavior, provider runtime, workers, queues, schedulers, polling, or persistence code.

## Latest accepted baseline

Latest accepted milestone: `Project Continuity System v2`

Latest accepted status: `PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

Latest accepted feature commit: `4195f55 Add project continuity system v2`

Latest accepted main merge commit: `c30c833 Merge feature/project-continuity-system-v2`

Latest accepted main snapshot: `fitness_ai_snapshot_2026-06-22_c30c833_merge-feature-project-continuity-system-v2.zip`

## Current Accepted Milestone Stack

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

`docs/project_memory/project_state.json` is the compact machine-readable current-state control file.

`docs/project_memory/project_continuity_bootstrap.md` remains the project-wide continuity landing packet for future Architecture, Backend Development, QA, DevOps / Tooling, Product, and TPM-style coordination chats.

`docs/project_memory/current_workflow_contract.md` is the canonical phase-separated delivery workflow contract.

## Daily Coach Async Persistence Design v1 status

Daily Coach Async Persistence Design v1 is authorized on `feature/daily-coach-async-persistence-design-v1`.

Required deliverable:

- `docs/project_memory/designs/daily_coach_async_persistence_design_v1.md`

Required project-memory updates:

- `docs/project_memory/project_state.json`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/open_questions.md`
- current Architecture / Backend / QA handoffs
- project-memory checks if required

Design must define:

- what should be persisted
- what must never be persisted
- job lifecycle storage model
- approved narrative storage model
- rejected/raw provider output policy
- public-safe metadata policy
- stale/expired/displayable state handling
- context hash/versioning strategy
- cleanup/retention considerations
- migration sequencing
- Developer Mode vs normal Today boundary

Boundary preserved:

- design only
- no DB schema implementation
- no migrations
- no tables
- no repositories
- no services
- no API routes
- no Streamlit behavior changes
- no provider runtime
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3 bridge
- no qwen3:32b promotion
- no worker / queue / scheduler / polling
- no normal Today provider call
- no public async narrative display
- deterministic fallback remains mandatory
- raw provider output persistence is forbidden
- rejected provider output persistence is forbidden

## Daily Coach async current boundary

Current Daily Coach async boundary: contracts plus service shell plus Developer Mode-only manual lifecycle prototype plus provider runtime design. Persistence design is now authorized, but persistence implementation is not.

Normal Today behavior remains unchanged. There is still no provider runtime implementation, no worker, no queue, no scheduler, no DB persistence implementation, no normal Today provider call, no public Streamlit async display, no qwen3 promotion, and no qwen3 bridge.

## Project Continuity System v2 status

Project Continuity System v2 is accepted.

It added an active continuity/onboarding system for AI Health Coach / fitness_ai:

- `docs/project_memory/project_state.json`
- `docs/project_memory/role_bootstrap_architecture.md`
- `docs/project_memory/role_bootstrap_backend.md`
- `docs/project_memory/role_bootstrap_qa.md`
- `docs/project_memory/role_bootstrap_devops_tooling.md`
- `docs/project_memory/current_workflow_contract.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/chat_onboarding_test.md`
- `python tools/dev_assistant.py continuity-brief`
- strengthened project-memory checks

The continuity system is docs + tooling only. It did not change product/runtime behavior.

## Daily Coach Async Provider Runtime Design v1 status

Daily Coach Async Provider Runtime Design v1 is accepted as a design-only milestone.

The design defines provider input/output contracts, parser/validator/approval flow, timeout/failure behavior, deterministic fallback behavior, sanitized runtime metadata, Developer Mode diagnostics, public UI restrictions, model policy, persistence considerations, and future implementation sequencing.

It did not implement provider execution.

## Definition of Done update

Project memory is a first-class system component.

A feature branch or milestone is not done until the relevant project memory docs reflect:

- what changed
- what did not change
- what is accepted
- what remains parked
- what is explicitly not approved
- what future agents must not assume

Any meaningful commit that changes behavior, architecture boundaries, provider behavior, persistence, routing, UI, tests, accepted status, or project scope must update project memory in the same branch.

Memory drift is architecture drift.

## Developer Delivery Artifact Location Correction v1 status

Temporary patch/apply artifacts should be saved outside the repo, normally in `C:\projects`, while commands still run from `C:\projects\fitness_ai`.

Examples:

```powershell
cd C:\projects\fitness_ai

git apply --check ..\example.patch
git apply ..\example.patch
python ..\apply_example.py
```

Do not save temporary apply scripts in the repo root when clean-tree guards are used. The untracked script correctly makes the tree dirty and should stop the apply phase.

## Local Developer Command Menu Audit + Repo-Owned Commands v1 status

Local helper commands now live in `scripts/fitness_commands.ps1`, with optional profile installation through `scripts/install_fitness_commands_profile.ps1`.

The command menu is documented in `docs/project_memory/local_developer_command_menu.md`.

`app` is the canonical Linux runtime launcher. `wapp` is Windows-local only. `fports` is Windows-side visibility only.

## Historical notes

Older accepted and reference-only milestones remain documented in milestone/review/runtime QA files under `docs/project_memory/`.

The prior `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` branch remains reference-only and is not accepted.

Provider Narrative QA Matrix v2 is developer-only QA tooling and project memory. It characterizes model behavior through the existing manual Developer Mode provider-preview debug route and does not affect normal Today behavior.
