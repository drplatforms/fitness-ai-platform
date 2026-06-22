# Current Project State

Last updated: 2026-06-22

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`feature/daily-coach-async-provider-runtime-design-v1`

## Current active milestone

`Daily Coach Async Provider Runtime Design v1`

Status: `AUTHORIZED / DESIGNED FOR REVIEW`

Purpose: define the safe future provider runtime boundary for Daily Coach async narrative generation before any implementation begins.

Current accepted implementation baseline before this branch: `Daily Coach Async Developer-Only Prototype v1`.

Continuity landing packet: `docs/project_memory/project_continuity_bootstrap.md`.

## Current Accepted Milestone Stack

Accepted Daily Coach async / runtime-control stack:

1. Local Developer Command Menu App Runtime Correction v1
2. Async Daily Coach Narrative Design v1
3. Async Daily Coach Narrative Implementation Plan v1
4. Daily Coach Async Contracts + Data Model v1
5. Daily Coach Async Service Shell / No Worker v1
6. Project Memory Transition Packet v1
7. Daily Coach Async Developer-Only Prototype v1

Latest accepted implementation baseline: `Daily Coach Async Developer-Only Prototype v1`.

`docs/project_memory/project_continuity_bootstrap.md` is the project-wide continuity landing packet for future Architecture, Backend Development, QA, DevOps / Tooling, Product, and TPM-style coordination chats.

Current Daily Coach async boundary: service shell plus a Developer Mode-only manual lifecycle prototype. Normal Today behavior remains unchanged. There is still no provider runtime, no worker, no queue, no scheduler, no DB persistence, no normal Today provider call, no public Streamlit async display, no qwen3 promotion, and no qwen3 bridge.

## Daily Coach Async Provider Runtime Design v1 status

Daily Coach Async Provider Runtime Design v1 is a design-only milestone on `feature/daily-coach-async-provider-runtime-design-v1`.

Design deliverable:

`docs/project_memory/designs/daily_coach_async_provider_runtime_design_v1.md`

The design defines:

- recommended provider execution model
- future async job lifecycle statuses and transitions
- provider input contract
- provider output contract
- parser / schema / validation / approval flow
- timeout and failure handling
- deterministic fallback behavior
- sanitized runtime metadata
- Developer Mode vs normal Today UI boundary
- model/provider policy
- persistence considerations and recommended sequencing

Boundary preserved:

- design only
- no provider execution
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3:32b call
- no background worker
- no queue
- no scheduler
- no polling
- no DB schema or persistence
- no `daily_coach_narrative_jobs` table
- no provider cache
- no normal Today provider call
- no public async narrative display
- no model promotion
- qwen3 remains not bridge-enabled
- deterministic Daily Next Action and Today Coach Note remain primary

## Recommended next milestone after design acceptance

Recommended next milestone: `Daily Coach Async Persistence Design v1`.

Reason: the provider runtime design recommends resolving durable job/narrative storage before implementing a provider runtime that could outlive a single Developer Mode session.

Alternative future options remain parked until Architecture authorizes them:

- Daily Coach Async Provider Runtime Prototype v1
- Daily Coach Narrative Premium Voice Research v1

## Latest accepted main baseline

The accepted main baseline includes:

- Project Memory Transition Packet v1
- Daily Coach Async Developer-Only Prototype v1
- Local Developer Command Menu App Runtime Correction v1
- Async Daily Coach Narrative Design v1
- Async Daily Coach Narrative Implementation Plan v1
- Daily Coach Async Contracts + Data Model v1
- Daily Coach Async Service Shell / No Worker v1
- Supercharger / session-brief developer tooling
- Catalog Import Pipeline v1
- Catalog Source Evaluation v1
- Food Catalog Import Batch v1
- Exercise Catalog Import Batch v1
- Daily Next Action deterministic service
- Coach's Read / Daily Coach Synthesis
- Today Coach Note deterministic path
- Today UX Polish v1, with global theme cleanup still parked
- Workout Substitution UX v1
- Workout Exercise Count Preference v1
- Workout Daily State Lifecycle v1
- Daily Coach Developer Preview Stabilization v1
- Daily Coach Provider Preview Contract Reliability v1
- Project Memory Alignment + North Star Architecture v1
- Future Architecture Ledger
- Premium Platform Blueprint
- Provider Narrative QA Matrix v2 runtime results
- Developer Delivery Workflow Contract v1
- Developer Delivery Workflow Script Safety Addendum v1
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1 results
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1 results
- Local Developer Command Menu Audit + Repo-Owned Commands v1

The prior same-session approval bridge branch is not accepted and is reference-only.

Provider Narrative QA Matrix v2 is implemented as developer-only QA tooling and project memory. It characterizes model behavior through the existing manual Developer Mode provider-preview debug route and does not affect normal Today behavior.

## Definition of Done update

Project memory is now a first-class system component.

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

Runtime truth encoded by the command menu:

- Windows source repo: `C:\projects\fitness_ai`
- Linux mirror repo: `~/projects/fitness-ai-platform`
- Windows Ollama: `http://127.0.0.1:11434`
- Linux-to-Windows Ollama: `OLLAMA_BASE_URL=http://192.168.1.104:11434`
- Windows Streamlit default: `http://127.0.0.1:8510`

## Current product surfaces

### Today

The Today flow contains distinct surfaces:

- Daily Next Action: deterministic backend decision and CTA.
- Today Coach Note: deterministic, short, user-facing note based on the Daily Next Action.
- Coach's Read / Daily Coach Synthesis: deterministic explanatory layer.
- Developer Mode panels: manual/debug-only tools that must not imply normal Today provider behavior.

Normal Today must not trigger Daily Coach async provider execution.

### Daily Coach async

Current Daily Coach async state is design/prototype-only:

- contracts exist
- service shell exists
- Developer Mode lifecycle prototype exists
- provider runtime design exists for review
- provider execution does not exist
- persistence does not exist
- public async narrative display does not exist

### Runtime and command menu

- Linux is the canonical FastAPI + Streamlit runtime.
- `app` starts/restarts Linux FastAPI + Streamlit.
- `wapp` is Windows-local only.
- `fports` is Windows-side ports only.

## Current model policy

- `qwen2.5:3b` is a bridge baseline only.
- `qwen3:32b` is a research / future premium async candidate only.
- qwen3 is not bridge-enabled.
- No model is promoted without Architecture approval.
- Deterministic fallback remains mandatory.
- Validation must not be loosened to make a model pass.
