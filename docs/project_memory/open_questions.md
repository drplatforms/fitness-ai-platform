# Open Questions

Last updated: 2026-06-21

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

### Developer delivery workflow

- Local Developer Command Menu Audit + Repo-Owned Commands v1 addresses the prior tooling command-menu docs cleanup backlog by moving `fitness`, `app`, `lstop`, `lrestart`, and `lupdate` into repo-owned tooling.
- Should project-memory checks eventually fail when `docs/project_memory/developer_delivery_workflow_contract.md` is missing or stale? Initial enforcement requires the doc to exist and be referenced by future agents.
- Should future handoff templates include an explicit "delivery workflow used" line?
- Should high-risk provider/UI milestones include an optional snapshot fallback artifact, while still keeping patch-first as the default?

### Daily Coach provider preview

- Daily Coach Provider Preview Contract Reliability v1 is accepted on main; `qwen2.5:3b` reached `parse_success=true`, `validation_success=true`, and `approved_narrative_returned=true` in manual preview runtime smoke.
- Provider Narrative QA Matrix v2 must characterize `qwen2.5:3b`, qwen3 probes, latency, safe rejection behavior, and voice quality before same-session approval is retried.
- Same-Session Approved Preview Bridge v1 Retry is accepted as a manual Developer Mode, session-only bridge using `qwen2.5:3b` only.
- Same-Session Bridge Runtime QA v1 is PASS; no broader model/provider promotion is implied.
- Daily Coach Narrative Product Voice Runtime QA v1 is PASS_WITH_NOTE: qwen2.5:3b copy is acceptable for the manual bridge baseline but not yet premium.
- Which qwen3 model, if any, is promising enough for a future premium async voice lane?


### Local developer command menu

- Should `scripts/fitness_commands.ps1` eventually gain a lightweight self-test command after manual QA confirms the first repo-owned command set?
- Resolved by Local Command Menu Linux tmux runtime correction: Linux Streamlit defaults to `8501`; Windows-local Streamlit remains `8510` under `wapp`.

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
- Daily Coach Same-Session Approved Preview Bridge v1 Retry was accepted as manual Developer Mode, session-only display only.
- Same-Session Bridge Runtime QA v1 passed and documented the manual bridge boundary.
- Daily Coach Narrative Product Voice Polish v1 improved qwen2.5:3b approved copy without widening provider authority.
- Daily Coach Narrative Product Voice Runtime QA v1 passed with PASS_WITH_NOTE: acceptable for the current manual bridge baseline, not premium.

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

- automatic same-session approval display without explicit Developer Mode action
- persistent Daily Coach provider narrative display
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

## Async Daily Coach Narrative open questions

These questions are intentionally left for a future implementation-planning milestone. Async Daily Coach Narrative Design v1 does not implement runtime behavior.

- Should Phase 1 remain session/dev-only, or should the first implementation introduce persisted jobs?
- Should `daily_coach_narrative_jobs` be created in SQLite, or should persistence wait until provider behavior is more stable?
- What exact expiration policy should apply to approved async narratives?
- Should explicit session-approved notes outrank async approved premium notes in all cases?
- What timeout tier should be used for `qwen3:32b` on the Windows Ollama host?
- What sanitized diagnostics are useful in Developer Mode without storing raw rejected output?
- What model quality bar should a premium async candidate meet before product UI surfacing?

<!-- START ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
## Async Daily Coach Narrative Open Questions

Date: 2026-06-21

Open questions carried forward from the implementation plan:

- Should the first runtime prototype use in-process background tasks, a simple polling service, or wait for an external queue?
- When should SQLite persistence be authorized?
- How long should approved async narratives live?
- Should generation be user-triggered, scheduled, or opportunistic?
- Should qwen3:32b voice research happen before the service shell or after the service shell?
- How should persona versions be named and validated?
- Should the premium async note replace the standard note or sit as an expandable enhancement?
- What is the minimum product-quality voice rubric for coach persona acceptance?
<!-- END ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->

## Local Command Menu App Runtime Correction v1

Resolved by hotfix implementation for review:

- `app` should mean canonical Linux app runtime.
- `wapp` should be the explicit Windows-local escape hatch.
- `fports` should be documented as Windows-side visibility only.

Remaining QA confirmation:

- Manual smoke should confirm `app` restarts Linux FastAPI + Streamlit and opens the Linux-hosted Streamlit URL.
- Manual smoke should confirm `wapp` still starts Windows-local FastAPI + Streamlit only when explicitly requested.

<!-- START DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1 -->
## Daily Coach Async Contracts + Data Model v1 Open Questions

Date: 2026-06-21

Open questions carried forward:

- Should the next service-shell milestone remain fully in-memory, or should it include a repository abstraction without schema changes?
- Should stale/latest job behavior be implemented before any Developer Mode trigger exists?
- Should premium voice research happen before the service shell or after the service shell?
- What exact persona/versioning rubric should be used before qwen3:32b advances beyond research-only?
<!-- END DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1 -->

## Daily Coach Async Service Shell / No Worker v1 Open Questions

Resolved by this milestone:

- Service shell can create/read jobs without provider execution.
- Latest displayable job selection is deterministic.
- Stale, expired, rejected, timeout, error, queued, and generating jobs are not displayable.
- Context hash, target date, next action, workflow target, provider/model, prompt contract, and validator mismatches are rejected for displayability.
- No FastAPI route, Streamlit display behavior, provider runtime, worker, queue, scheduler, DB schema, or provider cache is introduced.

Still open for future milestones:

- Developer-only async prototype trigger design.
- Future async runtime execution boundary.
- Future persistence decision for async jobs.
- Future validated async result surface.
- Premium voice/model research lane.
