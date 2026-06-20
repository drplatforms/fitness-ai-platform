# Current Handoff: Architecture

Project: AI Health Coach / fitness-ai

Source of truth:

- `docs/project_memory/current_state.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/future_architecture_ledger.md`
- relevant milestone/review docs

## Current accepted baseline

Accepted main includes deterministic daily product surfaces, provider-integrated Training and Nutrition report sections with strict fallback, workout substitution/count/daily lifecycle improvements, catalog foundations, Daily Coach Developer Preview Stabilization v1, and project-memory checks.

## Current active milestone

`Project Memory Alignment + North Star Architecture v1`

This is a docs/tooling alignment milestone. Do not change app runtime behavior.

## Next likely provider milestone

`Daily Coach Provider Preview Contract Reliability v1`, unless already accepted separately in a later handoff.

## Reference-only branch

`feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is not accepted and must not be merged. It remains useful only as a learning artifact.

## Non-negotiable boundaries

- Backend owns facts.
- Deterministic fallback remains the default.
- No provider call on normal Today load.
- No same-session approval unless explicitly reauthorized.
- No provider narrative persistence for Daily Coach.
- No qwen3 model is promoted.
- No raw/rejected provider output in normal UI.
- No schema/persistence/report/workout/nutrition/catalog changes unless scoped.
- No Aider, Headroom, Claude workflow, or `CLAUDE.md`.

## Team focus

Maintain boundaries, accept/reject milestones, protect deterministic truth, and keep project memory aligned with accepted status.
