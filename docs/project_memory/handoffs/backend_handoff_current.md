# Current Handoff: Backend Development / AI Provider Integration

Project: AI Health Coach / fitness-ai

## Current active milestone

`Async Daily Coach Narrative Design v1`

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

## Backend meaning

This milestone documents a future async architecture. It does not authorize backend implementation.

Backend should not add:

- async provider execution
- background worker
- queue
- scheduler
- provider cache
- database table
- schema migration
- route behavior change
- normal Today provider call
- model routing change
- qwen3 bridge eligibility
- provider default change

## Future backend design concepts

The design proposes future concepts only:

- async narrative lifecycle
- context hash / identity
- validation gates
- stale output rejection
- optional future `daily_coach_narrative_jobs` table
- storing approved/sanitized narrative only if persistence is later approved
- sanitized failure classification instead of raw rejected output

## Current source of truth

Until a future implementation milestone is accepted:

- deterministic Today Coach Note remains immediate
- manual Developer Mode provider preview remains the only provider path
- explicit session approval remains session-only
- no provider text is persisted
- `qwen2.5:3b` remains bridge baseline only
- qwen3 remains not bridge-enabled
- `qwen3:32b` is not product default and not promoted

## Handoff to future backend implementers

Do not infer approval from the presence of the design document. Build only from a later accepted implementation plan.
