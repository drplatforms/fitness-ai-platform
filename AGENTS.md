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
8. `docs/project_memory/developer_delivery_workflow_contract.md`
9. `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md`
10. `docs/project_memory/local_developer_command_menu.md`
11. `docs/project_memory/open_questions.md`
11. `docs/project_memory/future_architecture_ledger.md`
12. `docs/project_memory/premium_platform_blueprint.md`
13. Milestone-specific docs under `docs/project_memory/milestones/`, `reviews/`, `runtime_qa/`, and `architecture/`

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


## Developer delivery workflow contract

All future implementation handoffs must follow `docs/project_memory/developer_delivery_workflow_contract.md`.

Required defaults:

- Patch-first delivery is the normal implementation path.
- Snapshot restore is fallback only when patch application or branch state fails.
- Commands must verify branch/path state before applying changes.
- Validation must run before commit.
- Staging must be explicit.
- After Dustin provides a snapshot filename, the next assistant response must provide the Linux pull command first.
- Windows source repo is `C:\projects\fitness_ai`.
- Linux mirror repo is `~/projects/fitness-ai-platform`.
- Ollama runs on Windows by default; Linux provider runtime must use `OLLAMA_BASE_URL=http://192.168.1.104:11434` unless Dustin says otherwise.

Script safety addendum requirements from `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md` are also mandatory:

- Generated scripts should be phase-separated: preflight, apply patch, validate, stage, commit, push, Architecture review, merge after acceptance, snapshot, Linux pull.
- Scripts must stop on branch/base/path assumption failures.
- Merge scripts must verify the accepted final feature commit is an ancestor of `main` after merge with `git merge-base --is-ancestor <accepted-final-feature-commit> main` before push, snapshot, or Linux pull.
- A clean working tree is not proof that the correct milestone was merged.


## Repo-owned local commands

AI Health Coach helper commands live in `scripts/fitness_commands.ps1` and are documented in `docs/project_memory/local_developer_command_menu.md`.

The user PowerShell profile should only dot-source the repo script. Do not move project command logic back into hidden profile-only state. Preserve `fitness`, `app`, `lstop`, `lrestart`, and `lupdate` behavior when updating commands.

Command updates are docs/tooling/local workflow changes only unless a milestone explicitly authorizes runtime behavior changes.

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

- Daily Coach same-session bridge retry memory: `docs/project_memory/milestones/daily_coach_same_session_approved_preview_bridge_v1_retry.md` and `docs/project_memory/reviews/daily_coach_same_session_approved_preview_bridge_v1_retry.md`.
- Daily Coach narrative product voice polish memory: `docs/project_memory/milestones/daily_coach_narrative_product_voice_polish_v1.md` and `docs/project_memory/reviews/daily_coach_narrative_product_voice_polish_v1.md`.

## Complex backend quality gates

For complex features involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior, follow the repo's Complex Backend Quality Gate:

```text
diagnostic
→ failing/coverage test
→ narrow implementation
→ targeted validation
→ prior-regression validation
→ original smoke reproduction
→ project memory update
→ Architecture acceptance
```

Do not treat generic green tests as sufficient when the product-critical path is not covered.

Bigger milestone is okay. Bigger single patch is not okay.

Repeated patches must be tied to newly understood failures, diagnostics, failing tests, lint/pre-commit failures, or smoke regressions. If a stop condition triggers, stop and request Architecture direction instead of blindly patching.
