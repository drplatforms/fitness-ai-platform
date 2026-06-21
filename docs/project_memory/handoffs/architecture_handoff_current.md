# Current Handoff: Architecture

Project: AI Health Coach / fitness-ai

Source of truth:

- `docs/project_memory/current_state.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/future_architecture_ledger.md`
- `docs/project_memory/developer_delivery_workflow_contract.md`
- relevant milestone/review docs

## Current active milestone

`Async Daily Coach Narrative Design v1`

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

## Review focus

Architecture should review whether the proposed async Daily Coach Narrative design correctly preserves deterministic Today availability while defining a safe path for future slow premium model narratives.

Review these areas:

- async lifecycle
- state machine
- context identity and invalidation
- validation gates
- raw output policy
- model lanes
- UI display priority
- persistence phases
- implementation milestone breakdown

## Key boundary

This is design-only. Do not treat it as approval for async runtime, background workers, queues, scheduler behavior, database tables, provider cache, qwen3 bridge eligibility, model promotion, or normal Today provider calls.

## Current accepted baseline

Accepted main includes deterministic daily product surfaces, provider-integrated Training and Nutrition report sections with strict fallback, workout substitution/count/daily lifecycle improvements, catalog foundations, Daily Coach Developer Preview Stabilization v1, Daily Coach Provider Preview Contract Reliability v1, Provider Narrative QA Matrix v2 results, Daily Coach Same-Session Approved Preview Bridge v1 Retry, Same-Session Bridge Runtime QA v1, Daily Coach Narrative Product Voice Runtime QA v1, Local Developer Command Menu Audit + Repo-Owned Commands v1, north-star project memory docs, and project-memory checks.

## Non-negotiable boundaries

- Backend owns facts.
- Deterministic fallback remains the default.
- No provider call on normal Today load.
- Current provider preview remains Developer Mode/manual only.
- Same-session approval remains explicit and session-only.
- No provider narrative persistence for Daily Coach is approved by this milestone.
- `qwen2.5:3b` remains bridge baseline only.
- qwen3 remains not bridge-enabled.
- `qwen3:32b` remains future premium async candidate only.
- No model is promoted.
- No raw/rejected provider output in normal UI.
- No schema/persistence/report/workout/nutrition/catalog changes.
- No Aider, Headroom, Claude workflow, or `CLAUDE.md`.

## Delivery workflow requirement

All implementation handoffs must follow `docs/project_memory/developer_delivery_workflow_contract.md` and `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md`.
