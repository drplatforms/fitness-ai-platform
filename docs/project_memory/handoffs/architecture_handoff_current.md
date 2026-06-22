# Architecture Handoff Current

Current milestone: Project Memory Transition Packet v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: PROJECT_MEMORY_TRANSITION_PACKET_V1_ACCEPTED

Baseline accepted before this milestone: Daily Coach Async Service Shell / No Worker v1

Baseline commit: 69fbccc Merge feature/daily-coach-async-service-shell-no-worker-v1

## Summary

Project Memory Transition Packet v1 adds a project-wide continuity/bootstrap packet and corrects stale current-state wording so future Architecture, Backend Development, QA, DevOps / Tooling, Product, and TPM-style coordination chats can rehydrate from repo truth.

Primary new continuity file:

`docs/project_memory/project_continuity_bootstrap.md`

This is not an Architecture-only bootstrap. Do not create `docs/project_memory/handoffs/new_architecture_chat_bootstrap.md` for project-wide continuity.

## Implemented

- Added project-wide continuity bootstrap packet.
- Added/refreshed Current Accepted Milestone Stack in `current_state.md`.
- Corrected stale active-milestone summary that still pointed at Async Daily Coach Narrative Design v1.
- Confirmed Local Command Menu App Runtime Correction v1 as accepted.
- Confirmed Daily Coach Async Service Shell / No Worker v1 as the latest accepted implementation baseline.
- Preserved current runtime split, command menu truth, model/provider policy, async boundary, non-goals, and next recommended milestone.

## Current Accepted Milestone Stack

1. Local Developer Command Menu App Runtime Correction v1
2. Async Daily Coach Narrative Design v1
3. Async Daily Coach Narrative Implementation Plan v1
4. Daily Coach Async Contracts + Data Model v1
5. Daily Coach Async Service Shell / No Worker v1

## Daily Coach async boundary confirmation

- service shell only
- no async runtime implemented
- no provider execution added
- no direct_ollama call added
- no CrewAI call added
- no background worker added
- no queue added
- no scheduler added
- no DB schema change
- no daily_coach_narrative_jobs table created
- no provider cache table
- no FastAPI route added
- no provider call on normal Today load
- no Streamlit async display behavior changed
- no model promoted
- qwen2.5:3b remains bridge baseline only
- qwen3 remains not bridge-enabled
- qwen3:32b remains future premium async candidate / research-only
- deterministic fallback remains always available
- validation boundary preserved
- raw/rejected output not approved for normal UI

## Runtime hotfix continuity

- Local Command Menu App Runtime Correction v1 remains intact.
- `app` is now the canonical Linux runtime launcher.
- `app` means Linux canonical app runtime.
- Linux is the canonical FastAPI + Streamlit app runtime.
- wapp remains the explicit Windows-local escape hatch.
- fports remains Windows-side port visibility only.

## Model/provider policy preserved

- `qwen2.5:3b` is bridge baseline only.
- qwen3 remains not bridge-enabled.
- `qwen3:32b` remains research / future premium async candidate only.
- No model is promoted.
- No validation loosening was introduced.

## Non-goals preserved

- no backend behavior changes
- no FastAPI route changes
- no Streamlit changes
- no async provider runtime
- no worker / queue / scheduler
- no DB persistence
- no normal Today provider call
- no Daily Coach async UI
- no direct Ollama async runtime
- no CrewAI runtime changes
- no model promotion
- no qwen3 bridge
- no report/nutrition/workout changes

## Recommended next milestone after acceptance

Daily Coach Async Developer-Only Prototype v1.

That milestone is not authorized by this docs cleanup.
