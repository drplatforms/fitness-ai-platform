# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Project Continuity System v2

## Latest accepted status

`PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_c30c833_merge-feature-project-continuity-system-v2.zip`

## Current authorized milestone

Daily Coach Async Persistence Design v1

Status:

`AUTHORIZED_FOR_ARCHITECTURE_DESIGN`

Required starting branch:

`feature/daily-coach-async-persistence-design-v1`

Milestone type:

Design-only / persistence architecture

Expected recipient:

Architecture / Backend Development

Expected validation type:

Docs-only validation plus project-memory checks. Targeted Python tooling checks only if project-memory tooling changes.

## Recommended next milestone after Daily Coach Async Persistence Design v1

Daily Coach Async Persistence Contracts + Schema v1

## Why this is next

The accepted Daily Coach Async Provider Runtime Design v1 raised the sequencing question: provider runtime should not proceed until durable async job/narrative storage boundaries are designed.

This persistence design milestone answers what should be persisted, what must never be persisted, stale/expired/displayable behavior, context hash/versioning, Developer Mode inspection boundaries, and normal Today restrictions.

After this design is accepted, the next safest implementation step is schema/contracts only, not provider runtime.

## Not authorized yet

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler / polling
- DB persistence implementation before design acceptance
- `daily_coach_async_jobs` table implementation before explicit schema milestone
- `daily_coach_approved_narratives` table implementation before explicit schema milestone
- repositories / services
- API routes
- Streamlit behavior changes
- normal Today provider call
- public async narrative display
- raw provider output persistence
- rejected provider output persistence
- debug/provider metadata in normal UI
