# Architecture Handoff Current

Current milestone: Daily Coach Async Persistence Design v1

Status: DESIGNED / READY FOR ARCHITECTURE REVIEW

Proposed final status: `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

Branch: `feature/daily-coach-async-persistence-design-v1`

Previous accepted milestone: Project Continuity System v2

Previous final status: `PROJECT_CONTINUITY_SYSTEM_V2_ACCEPTED`

## Summary

Daily Coach Async Persistence Design v1 defines the durable persistence boundary for future Daily Coach async jobs and approved narratives.

This milestone is design only. It does not implement product/runtime behavior.

## Deliverable

- `docs/project_memory/designs/daily_coach_async_persistence_design_v1.md`

## Design covers

- persistence goals and non-goals
- proposed future data boundaries
- job lifecycle storage model
- approved narrative storage model
- data that must never be persisted
- rejection/failure metadata policy
- stale/expired/displayable policy
- context hash/versioning strategy
- Developer Mode boundary
- normal Today UI boundary
- cleanup/retention considerations
- migration sequencing
- validation gates before implementation

## Architecture review focus

Confirm that the design correctly preserves:

- no raw provider output persistence
- no rejected provider output persistence
- deterministic fallback
- current model/provider policy
- Developer Mode vs normal Today separation
- no provider runtime implementation
- no schema/migration implementation
- no normal Today behavior change

## Boundary confirmation

- design only: CONFIRMED
- no DB schema implemented: CONFIRMED
- no migrations added: CONFIRMED
- no tables created: CONFIRMED
- no repositories added: CONFIRMED
- no services added: CONFIRMED
- no API routes added: CONFIRMED
- no Streamlit behavior changed: CONFIRMED
- no provider runtime implemented: CONFIRMED
- no direct_ollama call added: CONFIRMED
- no CrewAI call added: CONFIRMED
- no qwen3 call added: CONFIRMED
- no qwen3 bridge added: CONFIRMED
- no qwen3:32b promotion: CONFIRMED
- no worker / queue / scheduler / polling added: CONFIRMED
- no normal Today provider call added: CONFIRMED
- no public async narrative display added: CONFIRMED
- deterministic fallback preserved: CONFIRMED
- model/provider policy preserved: CONFIRMED
- raw provider output persistence forbidden: CONFIRMED
- rejected provider output persistence forbidden: CONFIRMED

## Recommended next milestone after acceptance

Daily Coach Async Persistence Contracts + Schema v1.
