# Current Handoff: Architecture

Project: AI Health Coach / fitness-ai

Source of truth:

- `docs/project_memory/current_state.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/future_architecture_ledger.md`
- `docs/project_memory/developer_delivery_workflow_contract.md`
- relevant milestone/review docs

## Current accepted baseline

Accepted main includes deterministic daily product surfaces, provider-integrated Training and Nutrition report sections with strict fallback, workout substitution/count/daily lifecycle improvements, catalog foundations, Daily Coach Developer Preview Stabilization v1, Daily Coach Provider Preview Contract Reliability v1, Provider Narrative QA Matrix v2 results, north-star project memory docs, and project-memory checks.

## Current active milestone

`Developer Delivery Workflow Contract v1`

This is a docs/tooling workflow-stability milestone. Do not change app runtime behavior.

## Next likely provider milestone

`Daily Coach Same-Session Approved Preview Bridge v1 Retry`, only after Architecture accepts the provider QA matrix and confirms qwen2.5:3b as the bridge baseline candidate.

## Reference-only branch

`feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is not accepted and must not be merged. It remains useful only as a learning artifact.


## Delivery workflow requirement

All implementation handoffs must follow `docs/project_memory/developer_delivery_workflow_contract.md`:

- patch-first delivery is the default
- snapshot restore is fallback only
- Windows source repo is `C:\projects\fitness_ai`
- Linux mirror repo is `~/projects/fitness-ai-platform`
- Linux pull is provided immediately after every snapshot filename
- Ollama runs on Windows by default
- Linux provider runtime uses `OLLAMA_BASE_URL=http://192.168.1.104:11434` when reaching Windows Ollama

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

Maintain boundaries, accept/reject milestones, protect deterministic truth, and keep project memory plus developer delivery workflow aligned with accepted status.
