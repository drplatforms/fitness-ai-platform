# Team Quickstarts — AI Health Coach / fitness_ai

**Current accepted main:** `187e433 main_merge-platform-north-star-future-stack-canonicalization-v1`
**Next architecture planning target:** Recovery Intelligence v2 Architecture Planning v1
**Canonical north-star file:** `docs/project_memory/architecture/platform_north_star_and_future_stack.md`
**Next after this docs-only milestone:** Archive current Architecture chat, onboard new Architecture chat, then resume Backend Intelligence Foundation planning.

Read this first when starting a fresh project chat.

## Shared First Reads

All teams should read `AGENTS.md`, `readme.md`, `docs/project_memory/current_state.md`, `docs/project_memory/project_state.json`, `docs/project_memory/next_milestone.md`, `docs/project_memory/team_routing_contract.md`, and their role bootstrap/current handoff.

## Architecture Quickstart

Owns product/system architecture, sequencing, acceptance, scope boundaries, roadmap discipline, and cross-team routing. Does not own routine implementation after scope is accepted.

Current state: Platform North Star + Future Stack Canonicalization v1 is accepted at `187e433`; Workout Set Intelligence v1 remains the latest Backend Intelligence Foundation implementation slice at `123d115`; provider voice iteration is paused; Backend Intelligence Foundation planning resumes with Recovery Intelligence v2 Architecture Planning v1 unless Architecture changes course.

Return format: architecture decision, accepted/rejected status, next owner, required docs updates, non-goals.

Common mistakes: treating Project Memory as a visible team lane; routing general product/platform logic to DevOps & Tooling; jumping to RAG/agents before backend intelligence exists.

## Backend Development Quickstart

Owns backend services, deterministic logic, data models, provider/service seams, persistence/API work when authorized, and repo-doc patches when Architecture routes docs work. Does not own final product acceptance, provider promotion, Streamlit layout, or portfolio narrative.

Return format: branch, commit, baseline commit/snapshot, files changed, validation counts, boundaries preserved, final status.

Common mistakes: broad formatters on docs-only work, skipping project-memory updates, creating snapshots without Architecture authorization.

## QA Quickstart

Owns validation evidence, runtime checks, artifact inspection, pass/fail classification, and user-path validation. Does not rewrite architecture decisions.

Current QA focus: post-north-star project-memory consistency at `187e433` and preserving the `docs/project_memory/architecture/platform_north_star_and_future_stack.md` boundary; known baseline drift remains in `tests/test_daily_narrative_rich_day_service.py`.

Return format: commands run, pass/fail counts, artifact paths, classification, known warnings/drift.

## Agent Engineering Quickstart

Owns provider lab methods, Prompt Lab support, future model/tool workflow design, and future orchestration planning after Architecture scopes it. Does not start RAG, embeddings, vector search, LangGraph, CrewAI, LlamaIndex, or multi-agent runtime without Architecture approval.

Current state: provider voice iteration is paused; backend intelligence must come before serious orchestration.

## Streamlit UI / UX Quickstart

Owns Today/Workout/Nutrition UI, developer panels, user-facing layout, cards/tables/rendering, and copy placement. Does not own backend truth, provider promotion, schema decisions, or core acceptance.

Current state: no UI work is authorized by the docs refresh milestone.

## Portfolio Packaging Quickstart

Owns GitHub/LinkedIn/resume/portfolio assets, screenshots, public narrative, and demo framing. Low-frequency lane. Does not own core product architecture, backend implementation, or QA acceptance.

## DevOps & Tooling Quickstart

Owns helper commands, command menu, environment setup, Windows/Linux workflow support, snapshots/tooling mechanics, and runtime diagnostics. Narrow/low-frequency lane. Does not own general platform/product direction, backend product logic, provider decisions, or UI work.
