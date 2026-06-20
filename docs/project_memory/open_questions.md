# Open Questions

Last updated: 2026-06-20

This file separates active work from parked future ideas, resolved historical questions, and rejected/reference-only branches.

North-star docs now preserve the larger platform direction:
- `docs/project_memory/future_architecture_ledger.md`
- `docs/project_memory/premium_platform_blueprint.md`
Future-only ideas in those files remain parked until scoped milestones approve implementation.

## Active current questions

### Project memory and continuity

- How strict should automated stale-doc checks become before they start blocking commits?
- Which stale milestone phrases should be flagged in `tools/project_memory_check.py` without creating noisy false positives?
- Should each future merge require a short post-merge project-memory closeout note?

### Daily Coach provider preview

- After docs alignment, which local provider lane should be treated as the first known-good contract reliability baseline?
- Should `qwen2.5:3b` remain the baseline for JSON/contract reliability even if its copy quality is plain?
- Which qwen3 model should be evaluated first for voice quality once the preview contract is reliable?
- What manual smoke evidence is required before retrying same-session approval?

### Today product loop

- How should the app visually balance Daily Next Action, Today Coach Note, Coach's Read, and Daily Grounded Recommendation?
- Should Coach's Read remain deterministic-only until a provider persistence design exists?
- What should be the first user-facing sign that richer coach voice is coming without exposing provider internals?

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
- The same-session approval bridge was not accepted and should not be treated as current behavior.

### Provider boundaries

- Training and Nutrition report provider lanes remain opt-in/validated with deterministic fallback.
- Daily Coach provider work remains Developer Mode/manual preview only until further acceptance.

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

- same-session approval display in normal Today UI
- Daily Coach provider narrative persistence
- normal Today provider calls
- qwen3 model promotion
- provider defaults changing away from deterministic
- hidden model memory
- RAG/vector/MoE/MCP implementation
- frontend rewrite
- schema migrations outside explicit scope
- paid tooling
- Aider
- Headroom reintroduction
- Claude workflow or `CLAUDE.md`
