# Open Questions

Last updated: 2026-06-22

This file separates active work from parked future ideas, resolved historical questions, and rejected/reference-only branches.

North-star docs preserve the larger platform direction:

- `docs/project_memory/future_architecture_ledger.md`
- `docs/project_memory/premium_platform_blueprint.md`

Future-only ideas in those files remain parked until scoped milestones approve implementation.

## Active current questions

### Daily Coach async persistence

Daily Coach Async Persistence Design v1 is authorized to answer:

- What should be persisted for future async jobs?
- What should be persisted for approved narratives?
- What must never be persisted?
- Should failed jobs persist only allowlisted metadata?
- How should stale, expired, and displayable states work?
- How should context hash/versioning determine whether a persisted approved narrative remains displayable?
- What may Developer Mode inspect?
- What must normal Today UI continue to hide?
- What implementation sequence should follow design acceptance?

Current architecture bias:

- raw provider output must never be persisted
- rejected provider output must never be persisted
- deterministic fallback remains mandatory
- normal Today provider call remains unauthorized
- public async narrative display remains unauthorized

Likely next implementation after design acceptance:

- Daily Coach Async Persistence Contracts + Schema v1

### Project memory and continuity

Project Continuity System v2 is accepted.

Open continuity questions:

- Should every future milestone update `project_state.json` as part of Definition of Done?
- Should `project_state.json` become a blocking check for milestone/status drift?
- How strict should automated stale-doc checks become before they start blocking commits?
- Which stale milestone phrases should be flagged in `tools/project_memory_check.py` without creating noisy false positives?
- Should each future merge require a short post-merge project-memory closeout note?

### Developer delivery workflow

Open workflow questions:

- Should project-memory checks eventually fail when current handoff docs do not match `project_state.json`?
- Should `tools/dev_assistant.py continuity-brief` become the first command every new project chat runs?
- Should the repo add a machine-readable milestone registry later?

### Daily Coach async provider runtime

Provider runtime remains not authorized.

Open questions before provider runtime implementation:

- Should provider execution use subprocess isolation or a separate local worker process?
- Should provider runtime wait until persistence schema/contracts are accepted?
- What timeout tier should be used for larger research models?
- What sanitized diagnostics are useful in Developer Mode without storing raw rejected output?
- What model quality bar should a premium async candidate meet before product UI surfacing?

### Premium voice

- What should the voice rubric require before qwen3:32b can move beyond research-only?
- Should premium async narrative be a replacement for Today Coach Note or a separate enhancement?
- How can the UI signal that richer coach voice is coming without exposing provider internals?

### Workout experience

- Does Workout Tab Performance Profiling v1 need to happen before more workout UI complexity?
- Should workout size preference become a persisted user preference later?
- Should stale workout lifecycle expiration eventually use persisted explicit expired status, or is read-time/session cleanup sufficient?

## Parked future architecture

### Global theme and frontend

- Global Visual Theme Cleanup v1 remains open for lingering garnet/gold styling.
- Should the Streamlit UI eventually be replaced by React, Vue, Svelte, or another frontend?
- What should the future frontend preserve from Streamlit Developer Mode diagnostics?

### RAG / vector / memory

- Which curated knowledge sources are safe enough for a first local RAG prototype?
- Should vector memory start with user history, curated knowledge, or report evidence?
- Which vector store is best for local-first development: Chroma, FAISS, LanceDB, SQLite vector extension, or Postgres/pgvector later?
- How will retrieved facts be tagged, bounded, and validated before user-facing use?

### MoE / model routing

- Which tasks belong to small local models versus larger qwen3 models?
- How should model routing be logged, tested, and gated?
- What QA matrix is required before any model lane is promoted beyond developer preview?

### MCP / tools

- Which backend services are safe to expose as future MCP/tool interfaces?
- How can tool calls remain backend-authoritative without giving agents raw database freedom?
- What human approval gates are required before any tool writes data?

### Deployment

- When should local development move toward a local server or LAN deployment model?
- Should Apache, nginx, Caddy, or another reverse proxy be used later?
- What authentication and backup strategy is needed before household/LAN use?

## Resolved historical questions

### Catalogs

- Catalog Import Pipeline v1 created deterministic staged import tooling.
- Catalog Source Evaluation v1 selected USDA/FDC as first food candidate source and manual curation as first exercise path.
- Food Catalog Import Batch v1 added the first reviewed food batch.
- Exercise Catalog Import Batch v1 added the first manually curated exercise batch.

### Workout state

- Workout Substitution UX v1 improved substitution interaction.
- Workout Exercise Count Preference v1 moved workouts away from a fixed 4-exercise feel.
- Workout Daily State Lifecycle v1 resolved stale prior-day uncompleted selected/active/substituted workout state while preserving completed history.

### Daily Coach stabilization

- Daily Coach Developer Preview Stabilization v1 fixed Developer Mode diagnostics rendering and clarified Coach's Read visibility.
- Daily Coach Same-Session Approved Preview Bridge v1 Retry was accepted as manual Developer Mode, session-only display only.
- Same-Session Bridge Runtime QA v1 passed and documented the manual bridge boundary.
- Daily Coach Narrative Product Voice Polish v1 improved qwen2.5:3b approved copy without widening provider authority.
- Daily Coach Narrative Product Voice Runtime QA v1 passed with PASS_WITH_NOTE: acceptable for the current manual bridge baseline, not premium.

### Provider boundaries

- Training and Nutrition report provider lanes remain opt-in/validated with deterministic fallback.
- Daily Coach provider work remains Developer Mode/manual preview only until further acceptance.
- Daily Coach Async Provider Runtime Design v1 is accepted as design only and does not authorize provider execution.
- Project Continuity System v2 is accepted as docs + tooling only and does not authorize product/runtime behavior.

## Rejected or reference-only branches

### feature/daily-coach-narrative-same-session-approved-preview-bridge-v1

Status: reference-only, not accepted, not merged.

Reason:

- attempted same-session approval before developer-preview and provider-preview diagnostics were stable
- exposed Streamlit diagnostics mixed-type rendering failure
- exposed provider preview contract reliability gaps
- could not complete manual approve/revert smoke

Lesson:

- stabilize the Developer Preview surface first
- make provider preview contract reliable second
- retry same-session approval third

## Explicitly not approved

- automatic same-session approval display without explicit Developer Mode action
- persistent Daily Coach provider narrative display
- Daily Coach provider narrative persistence implementation
- Daily Coach async persistence implementation before explicit schema milestone
- raw provider output persistence
- rejected provider output persistence
- normal Today provider calls
- public async narrative display
- qwen3 model promotion
- qwen3 bridge
- provider defaults changing away from deterministic
- hidden model memory
- RAG/vector/MoE/MCP implementation
- frontend rewrite
- schema migrations outside explicit scope
- paid tooling
- Aider
- Headroom reintroduction
- Claude workflow or `CLAUDE.md`
