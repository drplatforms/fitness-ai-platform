# Async Daily Coach Narrative Design v1 Review

Status: `READY FOR ARCHITECTURE REVIEW`

Proposed acceptance status:

`ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED`

## Review decision requested

Review the design-only documentation milestone for future async Daily Coach Narrative architecture.

The design preserves deterministic Today availability, keeps provider generation out of normal page load, defines model lanes, defines async state lifecycle, proposes invalidation rules, preserves validation boundaries, defines raw output policy, proposes UI display priority, and outlines persistence phases without implementing runtime behavior.

## Design summary

Primary document:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

Key design decisions proposed:

- deterministic lane remains always available and instant
- current `qwen2.5:3b` manual bridge remains session-only
- `qwen3:32b` is future premium async candidate only
- async provider generation must never block Today page load
- no output displays unless parse, schema, validation, context identity, staleness, and model eligibility checks pass
- raw or rejected output is not shown in normal UI
- persistence is split into future phases and not implemented here

## State machine reviewed

Suggested async states:

- `not_requested`
- `queued`
- `generating`
- `provider_succeeded_pending_validation`
- `approved`
- `rejected_validation`
- `rejected_parse`
- `provider_timeout`
- `provider_error`
- `stale`
- `fallback_available`

Deterministic fallback is available in every state.

## Display priority reviewed

Suggested priority:

1. Explicit session-approved note, if active and context-valid.
2. Async approved premium note, if available, context-valid, and display-eligible.
3. Deterministic Today Coach Note.

## Boundary confirmation

- Design-only milestone.
- No async runtime implemented.
- No background worker added.
- No queue added.
- No scheduler added.
- No DB schema change.
- No provider cache table.
- No provider call on normal Today load.
- No model promoted.
- `qwen2.5:3b` remains bridge baseline only.
- qwen3 remains not bridge-enabled.
- `qwen3:32b` documented only as future premium async candidate.
- Deterministic fallback remains always available.
- Validation boundary preserved.
- Raw/rejected output not approved for normal UI.
- Persistence only proposed, not implemented.
- Docs/project memory updated.
- No qa_artifacts committed.
- No snapshots committed.
- Workflow contract followed.
- Script safety addendum followed.

## Requested decision

Accept as:

`ASYNC_DAILY_COACH_NARRATIVE_DESIGN_V1_ACCEPTED`
