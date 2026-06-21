# Async Daily Coach Narrative Design v1

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Proposed final status after review:

`ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED`

## Purpose

Document the future async Daily Coach Narrative architecture without changing runtime behavior.

The design covers when provider narratives may be generated, what backend-approved context is allowed, how async state should be represented, how validation and fallback should work, how Today UI should display pending/ready/failed states, how larger premium models fit without blocking page load, what may be persisted in future phases, what remains session-only, and how to migrate from manual Developer Preview to product-grade async generation.

## Scope

Approved:

- architecture design document
- async lifecycle design
- state machine design
- data contract proposal
- persistence proposal
- invalidation rules
- fallback rules
- UI state proposal
- provider/model lane proposal
- validation boundary proposal
- raw output policy
- operational/runtime constraints
- future milestone breakdown
- project memory updates
- project-memory/doc presence tests

Not approved:

- async runtime execution
- background worker
- task queue
- scheduler
- provider cache
- database schema changes
- report persistence changes
- provider calls on normal Today load
- automatic qwen3 generation
- automatic provider approval
- model promotion
- qwen3 bridge eligibility
- qwen2.5:7b bridge eligibility
- RAG/vector/MoE/MCP implementation
- frontend rewrite
- deployment infrastructure
- new external service
- paid tooling
- Aider/Headroom/Claude workflow
- `CLAUDE.md`

## Design outputs

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

Required review doc:

`docs/project_memory/reviews/async_daily_coach_narrative_design_v1.md`

Updated handoffs:

- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

## Boundary summary

- This is a design-only milestone.
- No async runtime behavior is implemented.
- No background worker is added.
- No queue is added.
- No scheduler is added.
- No database schema change is made.
- No provider cache table is added.
- No provider call occurs on normal Today load.
- No model is promoted.
- `qwen2.5:3b` remains bridge baseline only.
- qwen3 remains not bridge-enabled.
- `qwen3:32b` is documented only as a future premium async candidate.
- Deterministic fallback remains always available.
- Validation boundary is preserved.
- Raw/rejected output is not approved for normal UI.
- Persistence is proposed only, not implemented.

## Recommended next milestone

`Async Daily Coach Narrative Implementation Plan v1`

Purpose: break this accepted design into concrete, small implementation milestones without building all async behavior at once.
