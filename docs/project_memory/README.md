# AI Health Coach Project Memory

Last updated: 2026-06-18

## Purpose

This directory is the repo-native memory layer for AI Health Coach / fitness-ai.

It exists to reduce context loss across Architecture, Backend Development, QA, product planning, future ChatGPT sessions, and future Codex/backend implementation work.

This is a documentation-first source of project truth. It records accepted architecture decisions, current implementation boundaries, runtime QA outcomes, model/provider status, section ownership, current development state, and safe next steps.

## Non-goals

This is not RAG. It is not embeddings. It is not a vector database. It is not an agent system. It is not database-backed memory. It does not change runtime behavior.

## Read-first order

A new assistant or developer should read these files first:

1. `docs/project_memory/current_state.md`
2. `docs/project_memory/product_vision.md`
3. `docs/project_memory/architecture_principles.md`
4. `docs/project_memory/backend_truth_contract.md`
5. `docs/project_memory/ai_boundaries.md`
6. `docs/project_memory/section_registry_summary.md`
7. Latest relevant milestone file in `docs/project_memory/milestones/`
8. Latest relevant runtime QA file in `docs/project_memory/runtime_qa/`
9. Role-specific handoff in `docs/project_memory/handoffs/`

## How Architecture should use this

Use this directory as the baseline before approving or rejecting a new milestone. Architecture should update `current_state.md`, relevant ADRs, milestone summaries, and runtime QA summaries after each accepted milestone.

## How Backend should use this

Backend should read `current_state.md`, `backend_truth_contract.md`, `ai_boundaries.md`, and the role-specific backend handoff before implementing. Backend should not rely on chat memory alone for accepted constraints.

## How QA should use this

QA should read `qa_workflow.md`, the latest runtime QA summaries, and the relevant milestone summary before designing tests or runtime sweeps.

## How future ChatGPT/Codex sessions should use this

Future AI sessions should treat this directory as the project memory source of truth. They should not infer provider status, section maturity, accepted behavior, or next milestones from stale chat context when this directory is available.

## Update expectations

After each milestone:

- Update `current_state.md`.
- Update or add a milestone summary.
- Update runtime QA summary if runtime QA was performed.
- Update role handoffs if responsibilities changed.
- Add an ADR when the decision changes architecture or product boundaries.
- Do not invent unknown commit hashes. Use `Unknown / verify with git log` when commit/date is not known.
