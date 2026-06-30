# Platform North Star Reference

Canonical long-term platform vision and future technology stack:

```text
docs/project_memory/architecture/platform_north_star_and_future_stack.md
```

Use that file as the strategic source of truth for future-stack, SaaS, RAG, vector, agent, model-routing, and product-platform decisions. This ledger remains a historical/future-direction companion.

Current accepted baseline for this reference: `187e433 main_merge-platform-north-star-future-stack-canonicalization-v1`.

Backend Intelligence Foundation remains the prerequisite for advanced retrieval/orchestration candidates.

---

# Backend Intelligence Foundation prerequisite sequencing

Current accepted evidence at `23b5378` shows provider voice iteration should pause until backend intelligence improves.

Required sequencing:

```text
Backend Intelligence Foundation
→ Unified Health State Snapshot / source-data contracts
→ Prompt Lab / reviewer / renderer evaluation
→ Advanced retrieval / orchestration candidates
```

Rules:

- RAG does not happen until there is meaningful curated knowledge and backend intelligence to retrieve.
- Vector search does not happen until documents/data have stable metadata and retrieval use-cases.
- Multi-agent synthesis waits until specialist data layers can pass real evidence.
- Provider voice work is paused until richer source data and UI/renderer boundaries exist.
- Backend Intelligence Foundation includes Recovery Intelligence, Workout Set Intelligence, Trend Engine, Six-Month Seed Data, and Food Knowledge Expansion.

---

# Future Architecture Ledger

Last updated: 2026-06-20

## Purpose

This ledger preserves the long-term technical architecture north star for AI Health Coach.

It records future platform directions, dependencies, sequencing, and safety boundaries so future agents do not lose the architectural thread. It is intentionally future-facing and strict.

This ledger records direction. It does not authorize implementation.

Anything in this file still requires a scoped milestone, tests, validation, manual QA where appropriate, and Architecture acceptance before it becomes implementation scope.

## Non-authorization statement

This file does not approve:

- RAG implementation
- vector database implementation
- MoE or model routing implementation
- MCP or autonomous tool implementation
- frontend rewrite
- deployment rewrite
- provider persistence
- qwen3:32b production promotion
- same-session approval
- normal Today page provider calls
- database migrations
- schema changes
- report persistence changes

Current accepted behavior remains governed by `current_state.md`, `ai_boundaries.md`, accepted milestone reviews, and Architecture handoffs.

## Core doctrine

The future architecture must preserve the project doctrine:

- Backend owns truth.
- AI explains backend-approved truth.
- Validators gate AI output.
- Deterministic fallback always exists.
- Provider paths remain manual/developer-gated unless explicitly promoted.
- No model is production-approved without QA matrix evidence.
- `qwen3:32b` is a future premium voice candidate, not a current default.
- Raw or rejected provider output must not appear in normal UI.
- Model output must not write permanent truth without backend and user approval.
- Retrieved knowledge supports explanation, not authority.
- Vector hits are evidence candidates, not facts.
- RAG does not create truth.
- Model routing is backend-owned, not model-owned.
- MCP/tools expose safe backend APIs, not raw database freedom.
- User data and memory must be inspectable and correctable.
- Project memory docs are a first-class continuity layer.

## 1. Local-first foundation

### Current foundation

The current platform is local-first:

- Streamlit frontend shell
- FastAPI backend
- SQLite local data store
- deterministic service layer
- Pydantic-style contracts and explicit service boundaries
- report section registry
- validation-first provider architecture
- local Ollama experimentation
- Windows source-of-truth development flow
- Linux runtime/staging QA flow
- project-memory and stale-doc checks

### Why this came first

The local-first foundation came first because it supports:

- fast iteration
- low-cost experimentation
- inspectable failures
- deterministic fallback
- safe provider experimentation
- strong learning value
- no dependency on cloud services for core behavior
- easier snapshotting and handoffs
- strong boundaries around personal health data

The project needed deterministic truth before expanding AI features.

### Future direction

Local-first can evolve without being discarded:

- local server / LAN deployment
- Docker Compose
- service-managed FastAPI and Streamlit processes
- PostgreSQL when migration discipline is ready
- reverse proxy through Apache, Nginx, or Caddy
- model-serving separation
- observability services
- backup/restore tooling

No service split, deployment rewrite, or database migration is approved by this ledger alone.

## 2. Provider architecture

### Current doctrine

Provider behavior is validation-first:

1. backend builds approved context
2. provider/model proposes candidate text
3. response is parsed
4. parsed content is validated
5. approved content may be displayed only where the milestone allows
6. failed output falls back deterministically

Provider paths are opt-in and developer-gated unless explicitly promoted.

### Future provider architecture

Future provider architecture may include:

- explicit provider abstraction
- model capability registry
- provider QA matrix
- provider latency tracking
- parse/validation/fallback metrics
- manual preview lanes
- async/background generation
- approval workflows
- provider-job history
- approved narrative caching only after persistence design
- per-section provider policies

### Required boundaries

Future provider work must keep these boundaries:

- no provider call on normal Today load unless explicitly approved later
- no raw or rejected provider output in normal UI
- no provider persistence without explicit design
- no model promotion without QA evidence
- no provider output changing Daily Next Action or backend-owned decisions
- deterministic fallback remains available
- provider diagnostics stay developer-only and sanitized

## 3. `qwen3:32b` premium coach voice lane

### Future role

`qwen3:32b` is a future premium narrative candidate. It may eventually support:

- richer Today Coach Note language
- premium Coach's Read variants
- report narrative polish
- weekly review synthesis
- monthly review synthesis
- motivational but bounded coaching language
- more natural transitions between nutrition, workout, and recovery context

### Required operating model

A future `qwen3:32b` lane should likely be:

- async/precomputed
- not page-load blocking
- not enabled by default
- manually evaluated first
- gated by parser and validator
- operated only on backend-approved context
- compared against smaller baselines in a QA matrix
- blocked from changing truth, targets, decisions, CTA, or persistence

### Current status

`qwen3:32b` is not production-promoted.

Other local model roles may remain:

- `qwen2.5:3b`: reliable JSON/contract baseline candidate
- `qwen3:8b`: practical voice/quality probe
- `qwen3:14b`: intermediate probe candidate
- `qwen3:30b-a3b`: optional experimental candidate where locally available

No model may promote itself. The backend owns provider selection policy.

## 4. RAG / curated knowledge base

### Future role

A future RAG layer could help the coach explain approved context using curated knowledge. It may support:

- exercise technique explanations
- nutrition basics
- recovery principles
- habit coaching
- app-specific help docs
- report explanations
- user education mode
- explain-why controls
- source-tagged coaching context

### Source strategy

Preferred order:

1. curated local project knowledge
2. user-approved educational content
3. vetted exercise/nutrition references
4. later, broader retrieval only with source trust rules

### Strict boundary

RAG does not decide.

RAG does not create truth.

RAG does not override backend calculations.

Retrieved chunks must be source-tagged. Medical, nutrition, and exercise safety rules are required. Retrieval may provide explanatory evidence, but backend services and validators remain final authority.

## 5. Vector database / embeddings

### Future uses

Vector search may eventually support semantic retrieval over:

- user history
- workout logs
- food logs
- reports
- approved coaching facts
- Coach's Read history
- curated knowledge base content
- similar meals
- similar workouts
- similar prior adherence patterns
- user feedback
- project documentation

### Candidate tools

Possible tools include:

- PostgreSQL with `pgvector`
- LanceDB
- Chroma
- FAISS
- SQLite vector extensions if practical

No candidate is approved yet.

### Strict boundary

Vector hits are evidence candidates, not truth.

All conclusions derived from vector search must pass through deterministic backend services and validators. Retrieved personal history must be bounded by user, date, data quality, and context. Memory retrieval must be inspectable.

## 6. Long-term coach memory

### Future memory types

Long-term coach memory may eventually store:

- facts
- preferences
- goals
- constraints
- equipment
- food preferences
- training preferences
- schedule patterns
- recurring barriers
- user feedback
- coaching observations
- resolved historical notes

### Memory rules

Memory must be:

- inspectable
- editable
- exportable
- correctable
- scoped by source and confidence
- separated by memory type
- stale-aware

Inferred memory must be labeled as inferred. AI cannot silently create permanent memory. Memory writes require backend and/or user approval. Hidden model memory is not acceptable.

## 7. Unified Health State Snapshot

### Future role

A future Unified Health State Snapshot should be the canonical daily state object consumed by Today, reports, provider context, memory, and recommendations.

It may include:

- target date
- user profile facts
- nutrition status
- workout status
- recovery status
- recent history
- data quality
- confidence gates
- current Daily Next Action
- approved limitations
- current user preferences
- active constraints
- provider-safe context projection

### Sequencing

Unified Health State Snapshot likely comes before advanced RAG, long-term memory, async provider display, and premium coach voice. It should be deterministic and testable first.

## 8. MoE / model routing

### Future model routing

A future model routing layer may assign tasks to different model classes:

- deterministic services for decisions
- small local model for JSON/contract tasks
- larger local model for premium narrative
- specialized extraction/classification models if useful
- fallback renderers for failures
- latency-aware route selection
- quality-aware route selection

### Strict boundary

The model router is backend-owned.

No model chooses its own authority. No task is routed to a model without explicit approval. A model capability registry and QA matrix are required before promotion. Model routing must be logged and inspectable.

## 9. MCP / tool interface architecture

### Future idea

MCP-style or tool-based interfaces may eventually expose approved backend capabilities to agents or models.

Possible tools:

- food catalog lookup
- exercise catalog lookup
- report builder
- workout planner
- trend analyzer
- memory retriever
- validation service
- recommendation context builder
- provider preview runner
- QA artifact generator

### Strict boundary

Tools must call approved backend service APIs.

Tools must not expose raw database freedom. Autonomous writes are not allowed without explicit approval. Tool permissions must be explicit. Tool calls must be logged. Model output still requires validation.

## 10. Async / background orchestration

### Future needs

Large model work and recurring product workflows should not block page load. Future background orchestration may support:

- provider narrative jobs
- report generation jobs
- catalog ingestion jobs
- embedding jobs
- RAG ingestion jobs
- weekly review generation
- monthly review generation
- stale-state cleanup jobs
- backup jobs

### Candidate tools

Potential tools:

- Celery + Redis
- Prefect
- APScheduler for lightweight scheduling
- a custom job table first

### State model

Any job system should expose states such as:

- pending
- running
- succeeded
- failed
- retrying
- cancelled

Jobs should be inspectable and safe to retry.

## 11. Data architecture

### Current state

SQLite is the current local data store.

### Future path

Future data architecture may include:

- PostgreSQL
- Alembic migrations
- `pgvector`
- audit tables
- job tables
- canonical catalog tables
- staged import tables
- report persistence tables
- memory ledger
- embedding metadata
- backup/restore process
- export/import support
- data quality checks
- data retention policy

No migration is approved yet.

## 12. Observability / diagnostics

### Future premium backend needs

A premium platform will need:

- structured logs
- request IDs
- provider trace IDs
- OpenTelemetry
- Prometheus
- Grafana
- log aggregation
- fallback-rate metrics
- parse-failure metrics
- validation-failure metrics
- provider latency dashboards
- provider quality dashboards
- health endpoints
- QA artifact generation
- smoke-test reports

Observability should make fallback and validator behavior visible without exposing raw or unsafe model output in normal UI.

## 13. Better frontend / deployment

### Current frontend

Streamlit is the current learning/product shell. It is useful for local iteration and Developer Mode diagnostics.

### Future frontend options

Future frontend directions may include:

- React / Next.js / TypeScript
- generated API client from FastAPI OpenAPI
- Tailwind or shadcn-style component system
- real design system
- mobile-friendly UI
- PWA
- charts and trends
- active workout experience
- Playwright E2E tests

### Future deployment candidates

Deployment may evolve toward:

- Docker Compose
- Apache reverse proxy
- Nginx or Caddy alternatives
- systemd services
- local LAN deployment
- TLS later
- Kubernetes only much later if useful for learning or scale

No frontend rewrite or deployment rewrite is approved yet.

## 14. Agent engineering

### Current doctrine

Agent workflows are bounded:

- ChatGPT acts as Architecture / TPM / QA brain
- Backend implements scoped changes
- Codex is optional and scoped later
- no Aider unless explicitly reapproved
- no Headroom
- no Claude workflow
- no `CLAUDE.md`

### Future agent infrastructure

Future agent engineering may include:

- tool registry
- handoff templates
- project-memory checks
- session briefs
- architecture decision records
- agent permission rules
- code maps
- dependency maps
- branch-risk profiles
- QA checklist generation
- possible MCP integration

Agents must obey project memory and milestone boundaries.

## 15. Safety doctrine

Future architecture must continue to enforce:

- backend owns truth
- AI explains truth
- validators gate AI
- deterministic fallback always available
- no unsupported medical claims
- no unsupported nutrition claims
- no unsupported workout claims
- no raw or rejected output in normal UI
- no hidden persistence of model text
- provider output must be inspectable and bounded
- user data must be handled conservatively
- confidence gates must protect numeric targets and claims

Safety is not a later bolt-on. It is the architecture.

## 16. Roadmap phases

The long-term architecture can be thought of in phases:

1. Deterministic backend truth
2. Validated report sections
3. Daily product loop
4. Developer preview stability
5. Provider preview contract reliability
6. Same-session approved provider display
7. Async provider narrative generation
8. Unified Health State Snapshot
9. Long-term memory ledger
10. RAG / curated knowledge base
11. Vector search over knowledge and user history
12. Model routing / MoE
13. MCP / tool interface architecture
14. Real frontend / deployment architecture
15. Observability and premium operations

Each phase must still be implemented through a scoped milestone.

## Closing boundary

This ledger records direction. It does not authorize implementation.

Future systems must be promoted through explicit Architecture approval, tests, validation, QA, project-memory updates, and user acceptance.

<!-- START ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
## Async Daily Coach Narrative Roadmap

Date: 2026-06-21

Accepted design direction:
The Daily Coach Narrative premium lane should move toward async generation so larger models can be explored without blocking Today page load.

Current planned sequence:

1. Implementation Plan v1
2. Async Contracts + Data Model v1
3. Async Service Shell / No Worker v1
4. Developer-Only Async Prototype v1
5. Validated Async Result Surface v1
6. Premium Model Research Lane v1
7. Product Eligibility Review v1

Architecture rule:
No model promotion or normal-load provider generation happens without explicit Architecture acceptance.
<!-- END ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
