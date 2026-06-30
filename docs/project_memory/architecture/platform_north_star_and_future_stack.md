# Platform North Star + Future Stack

**Status:** Strategic architecture compass / non-authorizing future-stack reference
**Baseline:** `123d115 main_merge-daily-coach-workout-set-intelligence-v1`
**Baseline snapshot:** `fitness_ai_snapshot_2026-06-30_123d115_main_merge-daily-coach-workout-set-intelligence-v1.zip`
**Milestone:** Platform North Star + Future Stack Canonicalization v1
**Accepted in:** `187e433 main_merge-platform-north-star-future-stack-canonicalization-v1`

This file is the durable strategic north star for Fitness AI Platform. It preserves the big dream while keeping implementation sequencing disciplined.

This file records direction. It does not authorize implementation by itself.

## One-Sentence North Star

Fitness AI Platform is a private, data-grounded AI fitness operating system designed to evolve from deterministic local coaching into a serious adaptive coaching platform with backend intelligence, rich user context, cost-aware AI, multimodal input, mobile-first UX, and eventually advanced retrieval/orchestration.

## What This Platform Is Not

Fitness AI Platform is not:

- just a workout tracker
- just a macro tracker
- just a chatbot
- just a report generator
- a prompt demo
- a provider-wrapper
- an agent demo

The goal is a serious coaching platform where structured facts, deterministic intelligence, user context, and safe AI synthesis work together.

## Architecture Doctrine

- Backend owns truth.
- Deterministic logic comes first.
- AI/provider output is optional, gated, audited, and never truth.
- Retrieved/RAG content is context, not truth.
- Agents may assist later, but cannot own authority.
- Docs/project memory are part of Definition of Done.
- Cost, safety, provenance, confidence, and rollback paths are architecture concerns.
- User-facing coach identity is product identity, not an incidental prompt detail.

## Sequencing Doctrine

Huge dream. Strong sequencing. No random feature explosion.

Build the product brain first. Then build the advanced AI nervous system.

Do not use RAG, vector search, agents, frontier-model workflows, or fancy orchestration to compensate for weak backend intelligence.

Every future platform move still needs:

- Architecture-scoped milestone
- team handoff
- explicit non-goals
- tests
- validation
- project-memory update
- QA classification
- Architecture acceptance
- merge, push, and snapshot when authorized

## Backend Intelligence Foundation

Backend Intelligence Foundation is the prerequisite for advanced AI.

Core layers:

- Recovery Intelligence
- Workout Set Intelligence
- Cross-Domain Trend Engine
- Six-Month Seed Data
- Food Knowledge Expansion
- Unified Daily Coach Intelligence Snapshot
- user profile / preferences / constraints
- provenance and confidence models
- data-quality indicators
- scenario QA framework
- deterministic recommendation engine
- rules / policy layer

These layers must provide stable, inspectable source-data contracts before advanced retrieval, orchestration, or multi-model systems become useful.

Current accepted state at this baseline:

- Recovery Intelligence v1 is implemented.
- Workout Set Intelligence v1 is implemented.
- Daily Coach Intelligence Snapshot v2 carries recovery and workout-set intelligence.
- Provider voice iteration remains paused.
- Recovery Intelligence v2 is the expected next Backend Intelligence Foundation planning target after this docs-only milestone is accepted and a new Architecture chat is onboarded.

## Product Intelligence Vision

Future product capabilities may include:

- Daily Command Center
- adaptive training
- progression forecasting
- recovery-aware training adjustment
- nutrition adherence trends
- macro target adaptation
- meal planning / meal prep
- grocery list generation
- What-If simulator
- weekly/monthly coach review
- coach memory
- preference learning
- schedule-aware recommendations
- friction/adherence modeling
- confidence/provenance everywhere

These are product architecture goals, not automatic implementation approval.

## Core App / Backend Stack

Candidate technologies:

- Python
- FastAPI
- Pydantic
- SQLAlchemy / SQLModel
- Alembic
- PostgreSQL
- SQLite for local/dev
- Pytest
- Ruff
- Black
- Mypy or Pyright
- Pre-commit
- GitHub Actions
- Docker
- Docker Compose

## Data / Analytics Stack

Candidate technologies:

- PostgreSQL
- pgvector
- Redis
- DuckDB
- Parquet
- Polars
- Pandas
- dbt later if analytics grows
- Great Expectations or Pandera for data validation
- S3-compatible object storage / MinIO
- structured event/audit tables

## Retrieval / RAG / Knowledge Systems

Candidate future technologies and patterns:

- embeddings
- hybrid retrieval: keyword + vector
- BM25 / full-text search
- pgvector for integrated Postgres retrieval
- Qdrant if a dedicated vector DB becomes justified
- rerankers
- RAG over exercise knowledge
- RAG over food knowledge
- RAG over user history
- RAG over project docs
- RAG over coaching rules
- RAG over wearable explanations
- RAG over product education content

Boundary:

```text
RAG does not decide.
Retrieved content is context, not truth.
Backend facts and deterministic policy remain authoritative.
```

## AI / Model Stack

Candidate future technologies and practices:

- OpenAI provider adapter
- Anthropic provider adapter
- Gemini provider adapter
- local Ollama provider adapter
- vLLM or llama.cpp later for local serving
- LiteLLM-style model routing
- Prompt Lab
- model capability registry
- cost-aware model routing
- structured output validation
- provider fallback rules
- token/cost telemetry
- model comparison harness
- golden-output evals
- coach voice evals

## Agent / Orchestration Stack

Candidate future technologies and practices:

- LangGraph
- state-machine orchestration
- LlamaIndex workflows
- CrewAI as experimental/limited-use reference only
- custom job table first
- background job scheduler
- human-in-the-loop review
- agent audit logs
- agent trace artifacts
- tool permission boundaries
- policy-gated tool execution

Boundary:

```text
Multi-agent coaching waits until backend intelligence and service contracts are stable enough to give agents real evidence.
```

## Frontend / UX Stack

Candidate technologies and direction:

- Streamlit now
- React
- Next.js
- TypeScript
- Tailwind
- shadcn/ui
- TanStack Query
- Recharts / ECharts / Plotly
- PWA
- React Native / Expo later
- mobile-first Daily Command Center
- offline-friendly logging
- push notifications
- voice input later
- photo capture flows
- barcode scanning UX

## Multimodal Input

Future possibilities:

- barcode scanning
- nutrition label OCR
- photo-assisted food logging
- restaurant/menu parsing
- receipt/grocery import
- voice check-ins
- workout form video review eventually
- document parsing for plans/reports

## Wearables / Integrations

Future possibilities:

- Apple HealthKit
- Google Health Connect
- Fitbit
- Garmin
- Oura
- Whoop
- Strava
- smart scales
- calendar integration
- notification integrations
- grocery/recipe APIs later
- USDA FoodData Central
- Open Food Facts

## Observability / Operations

Candidate technologies:

- OpenTelemetry
- Prometheus
- Grafana
- Loki
- Sentry
- structured logs
- trace IDs
- provider telemetry
- token/cost dashboards
- usage dashboards
- model latency tracking
- background job monitoring
- data-quality dashboards

## SaaS / Platform Infrastructure

Future platform possibilities:

- auth
- OAuth/OIDC
- passkeys
- RBAC
- user accounts
- subscriptions
- Stripe
- billing portal
- rate limits
- quota limits
- data export
- data deletion
- audit logs
- secrets management
- encryption at rest/in transit
- backups/restore
- cloud deployment
- Docker Compose first
- AWS/GCP/Azure later
- Terraform/OpenTofu later
- Kubernetes only if truly needed

## SaaS Viability / Model Cost Doctrine

Frontier-model multi-call workflows are not the default SaaS path.

Default SaaS architecture should bias toward deterministic backend intelligence plus smaller/cost-efficient model phrasing.

Big models are better reserved for:

- evals
- premium flows
- hard cases
- internal QA
- limited high-value analysis

The coach voice is product identity. The product/user owner must be involved in prompt and coach-tone decisions. Prompt/voice work is not just backend implementation.

## Team Routing

Canonical visible team lanes:

- Architecture
- Backend Development
- QA
- Agent Engineering
- Streamlit UI / UX
- Portfolio Packaging
- DevOps & Tooling

Project Memory / All Future Agents is not a visible team lane. It is a repo continuity concern that every team must respect.

## What This File Does Not Authorize

This file does not authorize immediate implementation of:

- RAG
- embeddings
- pgvector
- Qdrant
- vector DB setup
- LangGraph
- CrewAI
- LlamaIndex
- multi-agent runtime
- custom GPT build
- OpenAI/default provider changes
- production provider coach
- Streamlit rewrite
- React migration
- mobile app
- wearable integration
- billing/SaaS infrastructure
- schema migration
- cloud deployment

All future work still requires:

```text
Architecture-scoped milestone
team handoff
tests
validation
project-memory update
QA classification
Architecture acceptance
merge/push/snapshot
```

## Suggested ChatGPT Project Instructions

```text
You are operating inside the Fitness AI Platform project.

This project is building a private, data-grounded AI fitness operating system, not a toy chatbot or simple tracker. The long-term goal is a serious adaptive coaching platform that understands training, nutrition, recovery, readiness, equipment, preferences, history, trends, adherence, friction, goals, uncertainty, provenance, and user context.

Use the seven team lanes correctly: Architecture, Backend Development, QA, Agent Engineering, Streamlit UI / UX, Portfolio Packaging, and DevOps & Tooling.

Repo documentation is the canonical source of truth. Chat memory is helpful but not authoritative. When project state, architecture direction, team routing, or milestone status is unclear, inspect the latest snapshot/docs before steering.

Core doctrine: Backend owns facts, validation, persistence, provenance, confidence, safety boundaries, and deterministic fallback. AI may explain, summarize, propose, personalize, or generate candidates only inside backend-approved contracts. AI/provider output is not truth.

Keep the huge future vision alive: backend intelligence, adaptive coaching, long-term user memory, Prompt Lab discipline, cost-aware model routing, multimodal input, wearables, mobile-first UX, rich dashboards, RAG/vector search, agent orchestration, observability, cloud deployment, and SaaS-grade engineering are all part of the long-term dream.

Sequence hard. Do not use RAG, vector search, agents, frontier-model workflows, or fancy orchestration to compensate for weak backend intelligence. Build the product brain first, then the advanced AI nervous system.

Push back when the project drifts, skips foundation work, overuses the wrong team, chases shiny technology too early, or lets stale docs/chat memory override current repo truth.

For major milestones, prefer team-specific handoffs, explicit non-goals, validation requirements, project-memory updates, and post-merge snapshots.
```

## Continuation Rule After This Milestone

After this docs-only milestone is merged, pushed, and snapshotted:

```text
Archive the current Architecture chat.
Onboard a new Architecture chat from the latest accepted snapshot, current project memory, this north-star file, team_routing_contract.md, and backend_intelligence_foundation_v1.md.
Then resume Backend Intelligence Foundation planning.
```

## End
