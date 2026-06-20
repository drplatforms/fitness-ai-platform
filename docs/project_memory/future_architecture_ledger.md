# Future Architecture Ledger

Last updated: 2026-06-20

## Purpose

This ledger preserves the long-term technical north star without authorizing future-only implementation.

Future ideas in this file are recorded so agents do not lose the dream, but they are not approved scope unless a later milestone explicitly authorizes them.

## 1. Local-first foundation

Current foundation: Streamlit UI, FastAPI backend, SQLite data layer, local deterministic services, local Ollama provider experiments, Windows source-of-truth development, and Linux staging/runtime QA.

Why this came first: fast iteration, inspectable failures, safe deterministic fallback, portfolio-friendly architecture, local privacy/control, and easier learning/debugging.

Local-first remains valuable even if a future frontend/deployment architecture is added.

## 2. Provider architecture

Provider doctrine: deterministic default, manual/developer-gated preview lanes first, parse before validate, validate before display, deterministic fallback always available, no raw/rejected output in normal UI, and no provider authority over truth.

Future provider architecture may include async/background generation, approved narrative cache after validation, provider QA matrices, explicit model routing, and developer diagnostics dashboards.

No provider cache/persistence is approved yet for Daily Coach narrative.

## 3. qwen3:32b premium coach lane

Long-term target: richer coach voice, premium synthesis language, motivational framing, and more human-feeling daily explanation.

Current status: future candidate only, not production-promoted, not default, not page-load blocking, and not allowed to bypass validators.

Likely future shape: async generation, precomputed after backend context is ready, validated before display, cached only after explicit persistence design, deterministic fallback immediately visible.

## 4. RAG / curated knowledge base

Future support areas: exercise explanations, nutrition education, coaching rationale, form cues, recovery education, and meal/snack idea explanation.

Rules: retrieval explains approved context, retrieval does not create truth, retrieved facts must be source-tagged, medical/nutrition safety boundaries are required, curated/local knowledge should come before broad web retrieval, and backend validators remain final authority.

No RAG implementation is approved yet.

## 5. Vector database / embeddings

Future semantic search may cover user history, workout logs, nutrition logs, reports, approved coaching facts, curated knowledge, preferences, and constraints.

Candidate stores: Chroma, SQLite vector extensions, FAISS, LanceDB, or Postgres/pgvector later.

Rules: vector hits are evidence candidates, not truth; retrieval must be bounded; retrieved evidence must be inspectable; backend services decide what is approved.

No vector database is approved yet.

## 6. Long-term coach memory

Memory should be deterministic and inspectable first.

Future memory should separate facts, preferences, goals, constraints, coach observations, and model-generated suggestions.

Rules: avoid hidden model memory, allow user inspection/editing later, recognize trends only from verified data, and never turn model suggestions into facts without backend acceptance.

## 7. MoE / model routing

Future routing may assign tasks by model strength: small local model for JSON/contract tasks, larger qwen3 model for premium narrative, deterministic services for decisions, and specialized extraction/classification models only if justified.

Rules: the router must be explicit, router decisions must be logged, no model chooses its own authority, no automatic promotion without QA matrix, and deterministic fallback remains default.

No MoE router is approved yet.

## 8. MCP / tool interface architecture

Future tool surfaces may include food catalog lookup, exercise catalog lookup, report builder, workout planner, trend analyzer, memory retriever, and validation service.

Rules: tools expose approved backend APIs rather than raw database freedom, tool calls go through backend authority, no autonomous writes happen without user/backend approval, and tool outputs remain validate-before-display when user-facing.

No MCP implementation is approved yet.

## 9. Better frontend / deployment

Streamlit is the current learning/product shell.

Future frontend candidates include React, Vue, Svelte, or another web frontend over FastAPI.

Future deployment candidates include local server, LAN dashboard, Dockerized services, systemd services, and Apache/nginx/Caddy reverse proxy.

Future frontend must preserve Today, Workout, Nutrition, Reports, Developer Mode, and traceable diagnostics.

No frontend rewrite is approved yet.

## 10. Deployment architecture

Current deployment is local development.

Future deployment work should address local service startup, reverse proxy, authentication, backup strategy, log/artifact strategy, database migration discipline, model serving separation, and LAN access constraints.

No production deployment is approved yet.

## 11. Data architecture

Current data architecture: SQLite, deterministic seed scripts, canonical food/exercise catalogs, user logs, report persistence, and local-only QA artifacts.

Future possibilities: Postgres, vector store, object/file storage for artifacts, explicit migrations, and backup/restore tooling.

Migration discipline: no schema change without explicit Architecture approval, preserve history, test migrations, and document persistence boundaries.

## 12. Agent engineering

Current agent pattern: ChatGPT acts as Architecture/TPM/QA/product reasoning partner, Backend implementation happens through scoped branches and scripts, Dev Assistant provides local checks and session briefs, and Codex may be used later in scoped workflows.

Boundaries: no Aider unless explicitly reapproved, no Headroom reintroduction, no Claude workflow, no `CLAUDE.md`, agents must obey project memory, and agents must not broaden scope silently.

## 13. Safety doctrine

Safety rules: backend owns truth, AI explains truth, validators gate AI, deterministic fallback always exists, no raw/rejected output in normal UI, no unsupported medical claims, no unsupported nutrition/workout claims, no hidden persistence of provider text, and no model authority over decisions.

## 14. Roadmap phases

Phase 1: deterministic truth foundation.

Phase 2: validated report sections.

Phase 3: daily product loop.

Phase 4: developer preview stability.

Phase 5: provider contract reliability.

Phase 6: same-session approved display.

Phase 7: async narrative generation.

Phase 8: unified health state snapshot.

Phase 9: RAG/vector memory.

Phase 10: production frontend/deployment.

## Final reminder

This ledger records direction. It does not authorize implementation.
