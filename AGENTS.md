# AI Health Coach Agent Instructions

This file is the repo-level instruction source for ChatGPT, Codex-style OpenAI coding helpers, Aider-style patch tools, GitHub Copilot, and human contributors.

## Source of truth

Read project memory before making changes:

1. `docs/project_memory/current_state.md`
2. `docs/project_memory/product_vision.md`
3. `docs/project_memory/architecture_principles.md`
4. `docs/project_memory/backend_truth_contract.md`
5. `docs/project_memory/ai_boundaries.md`
6. `docs/project_memory/section_registry_summary.md`
7. `docs/project_memory/development_workflow.md`
8. `docs/project_memory/open_questions.md`
9. `docs/project_memory/future_architecture_ledger.md`
10. `docs/project_memory/premium_platform_blueprint.md`
11. Milestone-specific docs under `docs/project_memory/milestones/`, `reviews/`, `runtime_qa/`, and `architecture/`

When project memory and a pasted prompt disagree, stop and ask for the latest source-of-truth snapshot or Architecture handoff.

## Architecture doctrine

- Backend owns facts, calculations, constraints, validation, persistence, and fallback.
- AI/provider paths may explain or phrase backend-approved truth only.
- Validators enforce reality and must not be loosened without explicit Architecture approval.
- Deterministic fallback remains the default unless a milestone explicitly changes that boundary.
- Provider behavior remains gated, manual, opt-in, or debug-only unless Architecture explicitly promotes it.
- Do not change provider defaults.
- Do not promote qwen3 or any local model to production-approved status.
- Do not alter nutrition, training, recovery, or report semantics unless the milestone scope explicitly says to do so.
- Do not introduce RAG, embeddings, scraping, runtime agent orchestration, vector databases, or app memory unless explicitly authorized.

## Tool roles

- ChatGPT: Architecture, TPM, QA review, handoff generation, milestone planning, and product/architecture reasoning.
- User: project owner, command runner, final approver, merge owner, and snapshot owner.
- Codex/OpenAI coding helpers: optional scoped implementation workers only. They do not own architecture or milestone boundaries.
- Aider-style tools: optional surgical patch or failing-test helpers.
- GitHub Copilot: IDE autocomplete/helper only.
- Dev Assistant: local project cockpit for repo state, project-memory checks, prompt/context-pack generation, validation guidance, and snapshot commands.
- Headroom: future developer-workflow context compression spike only, not runtime product logic.

Claude-specific workflow files and commands are intentionally out of scope. Do not add `CLAUDE.md`.

## Implementation boundaries

Before editing, identify:

- current branch
- latest commit
- source-of-truth snapshot/handoff
- exact milestone
- approved scope
- strict non-goals
- expected files
- validation commands

Prefer narrow patches. Do not invent endpoints, models, services, schemas, or UI surfaces that are not scoped.

## Artifact and staging rules

Do not stage:

- `*.zip` snapshots
- `*.patch` files
- `artifacts/`
- `qa_artifacts/`
- runtime output
- local database copies
- scratch files
- temporary review folders

Use `git status --short` and `git diff --cached --name-only` before every commit.

## Windows / Linux workflow split

Windows is the source-of-truth development environment:

- patches
- source edits
- tests/checks
- commits
- pushes
- snapshots

Linux is staging/runtime QA:

- FastAPI runtime
- Streamlit runtime
- SQLite runtime checks
- Ollama-connected provider-lane QA

Do not commit separately from Linux unless the workflow explicitly calls for it.

## Provider-lane restart rule

Linux FastAPI may need `OLLAMA_BASE_URL` set to reach Windows-hosted Ollama for manual Developer Mode provider-lane testing.

Setting `OLLAMA_BASE_URL` only tells FastAPI where Ollama lives. It does not make provider output the default.

Deterministic-safe restarts should unset provider-selection env vars unless intentionally testing provider defaults, while still allowing:

```bash
export OLLAMA_BASE_URL=http://<WINDOWS_IP>:11434
```

Provider-selection env vars such as `RECOMMENDATION_CANDIDATE_PROVIDER` and `NUTRITION_EXPLANATION_PROVIDER` should remain unset unless a milestone explicitly says to test provider defaults.

## Project memory update requirement

Every meaningful milestone or feature branch that changes user-visible behavior, backend behavior, architecture boundaries, provider behavior, persistence, routes, UI, tests, project scope, or accepted status must update project memory in the same branch.

A milestone is not done if project memory still describes older project truth.
