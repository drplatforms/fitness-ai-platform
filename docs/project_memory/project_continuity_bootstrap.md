# Project Continuity Bootstrap — Future Feature & Technology Inventory v1

Current source of truth: `main`.

Current accepted main commit: `9d66514`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_9d66514_nutrition-actuals-provenance-confidence-model-v1.zip`.

Current project-memory milestone: Future Feature & Technology Inventory v1.

Milestone type: CLASS 0 — DOCS / PROJECT MEMORY ONLY.

Branch: `feature/future-feature-technology-inventory-v1`.

Requested final status: `FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED`.

## First files to read

1. `docs/project_memory/current_state.md`
2. `docs/project_memory/future_feature_technology_inventory_v1.md`
3. `docs/project_memory/next_milestone.md`
4. `docs/project_memory/project_state.json`
5. `docs/project_memory/handoffs/architecture_handoff_current.md`
6. `docs/project_memory/handoffs/backend_handoff_current.md`
7. `docs/project_memory/handoffs/qa_handoff_current.md`
8. `docs/project_memory/ai_boundaries.md`
9. `docs/project_memory/backend_truth_contract.md`
10. `docs/project_memory/future_architecture_ledger.md`

## Current accepted nutrition baseline

Accepted chain:

```text
canonical food search
-> backend-approved serving-unit discovery
-> Streamlit serving-unit selection
-> quantity entry
-> backend log-serving
-> resolved grams
-> food_entries actuals bridge
-> serving-unit provenance metadata
-> actuals provenance/confidence interpretation
-> Target-vs-Actual compatibility
```

## Inventory purpose

The future inventory preserves product/technology/AI/platform ideas so future agents do not lose the north star.

It is not implementation authorization.

## Doctrine to preserve

Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries.

Streamlit renders approved fields and collects user input.

AI may explain, summarize, propose, or generate candidates only inside strict backend-approved contracts.

AI must not become the source of truth.

## Current workflow reminders

- Use phase-separated delivery.
- Never stage with `git add .`.
- Temporary patch files live outside the repo, usually under `C:\projects`.
- Use `git apply --check ..\<patch>.patch` before applying patches.
- Use `python ..\<script>.py` for outside-repo scripts when needed.
- Do not run repo-wide mutating formatters for feature work.
- For docs-only work, do not run broad formatters.
- Long handoffs must be in one copy/paste-ready code block.
- Linux pull validation follows Windows push.

## Historical continuity anchors

These phrases are reference-only continuity anchors:

- Project Continuity System v2
- feature/project-continuity-system-v2
- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- provider runtime implementation
- raw provider output persistence
- rejected provider output persistence
- qwen3
- not bridge-enabled
- qwen3:32b
- research / future premium async candidate only
- Deterministic fallback remains mandatory.
- normal Today provider call
- public async narrative display

## Accepted historical workflow anchors — reference-only

Current Accepted Milestone Stack is maintained by `current_state.md` and `project_state.json`.

Sound right and be right remains the provider/coach-copy doctrine.

Daily Coach Async Service Shell / No Worker v1 remains a historical accepted milestone.

Daily Coach Async Developer-Only Prototype v1 remains a historical accepted milestone.

Developer Mode-only manual lifecycle prototype remains reference-only.

The `app` command launches Linux runtime.

qwen3 is not bridge-enabled.

Historical Daily Coach async work was service shell only with no provider runtime yet.

What Future Chats Must Do First: read current_state, project_state, next_milestone, current handoffs, and this bootstrap before acting.
