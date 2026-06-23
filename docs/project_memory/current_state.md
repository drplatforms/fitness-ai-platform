# Current Project State

Last updated: 2026-06-22

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`feature/daily-coach-async-approved-preview-bridge-design-v1`

## Current active milestone

`Daily Coach Async Approved Preview Bridge Design v1`

Status: `AUTHORIZED FOR DESIGN / BACKEND ARCHITECTURE SUPPORT`

Codex: `DO NOT USE BY DEFAULT`

## Latest accepted baseline

Latest accepted milestone: `Daily Coach Async Provider Runtime QA Hardening v1`

Latest accepted status: `DAILY_COACH_ASYNC_PROVIDER_RUNTIME_QA_HARDENING_V1_ACCEPTED`

Latest accepted main merge commit: `3765314 Merge feature/daily-coach-async-provider-runtime-qa-hardening-v1`

Latest accepted main snapshot: `fitness_ai_snapshot_2026-06-22_3765314_merge-feature-daily-coach-async-provider-runtime-qa-hardening-v1.zip`

## Current accepted Daily Coach async stack

1. Async Daily Coach Narrative Design v1
2. Async Daily Coach Narrative Implementation Plan v1
3. Daily Coach Async Contracts + Data Model v1
4. Daily Coach Async Service Shell / No Worker v1
5. Project Memory Transition Packet v1
6. Daily Coach Async Developer-Only Prototype v1
7. Daily Coach Async Provider Runtime Design v1
8. Project Continuity System v2
9. Daily Coach Async Persistence Design v1
10. Daily Coach Async Persistence Contracts + Schema v1
11. Daily Coach Async Persistence Service Shell v1
12. Developer Mode Persistence Inspection v1
13. Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only
14. Daily Coach Async Provider Runtime QA Hardening v1

## Current design milestone

Daily Coach Async Approved Preview Bridge Design v1 is design only.

Required deliverable:

`docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md`

The design defines a future controlled bridge from Developer Mode-only approved async narratives into a possible Today preview path.

The design must answer:

- what qualifies a persisted async narrative as approved for preview
- what display gates are required
- where a future preview could appear
- how deterministic Daily Next Action remains primary
- what fallback behavior remains visible
- what normal UI must still hide
- what Developer Mode diagnostics may continue to show
- what feature flag is required
- what QA gates must pass before implementation
- what remains explicitly unauthorized

## Current Daily Coach async boundary

Normal Today behavior remains unchanged.

Deterministic Daily Next Action remains primary.

Developer Mode-only provider runtime exists and is QA hardened, but normal Today still does not call providers.

The current milestone is docs/design only. It does not implement a Today preview bridge.

## Explicitly not authorized

- Today preview bridge implementation before design acceptance
- provider execution from Today
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
- deterministic Daily Next Action replacement
- app/wapp command behavior changes

## Historical reference phrases for continuity checks

Project Memory Alignment + North Star Architecture v1 remains reference-only.

The old feature branch `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is reference-only.

No provider may run on normal Today page load.

Provider Narrative QA Matrix v2, Daily Coach Same-Session Approved Preview Bridge v1 Retry, Same-Session Bridge Runtime QA v1, Daily Coach Narrative Product Voice Polish v1, and Daily Coach Narrative Product Voice Runtime QA v1 remain historical local-provider learning milestones. PASS_WITH_NOTE and "sound right and be right" remain product-voice references, not authorization for unvalidated public provider output.

Local Developer Command Menu Audit + Repo-Owned Commands v1 created `scripts/fitness_commands.ps1`. Local Command Menu App Runtime Correction v1 confirmed Linux is the canonical runtime and `wapp` is Windows-local.

Daily Coach Async Service Shell / No Worker v1 remains service shell only and no provider execution added in that milestone.

## Recommended next after acceptance

`Daily Coach Async Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default`

Status: `NOT_AUTHORIZED_YET`

Implementation should only happen after Architecture accepts this design.

## Definition of Done reminder

Project memory is a first-class system component. A milestone is not done until current state, next milestone, project_state.json, continuity bootstrap, handoffs, milestone docs, and review docs reflect the actual accepted/authorized boundary.
