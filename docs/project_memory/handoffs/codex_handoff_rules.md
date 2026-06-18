# Current Handoff: Codex / coding assistant

Recipient: Codex / coding assistant


Project: AI Health Coach / fitness-ai

Branch: `feature/training-evidence-claim-service`

Current status: Latest accepted milestone is `Nutrition Report Section Boundary v1`. Lightweight Project Memory Layer v1 is the current approved implementation milestone.

Source of truth: `docs/project_memory/current_state.md` plus the relevant milestone and runtime QA files.

Do not assume: qwen3 is promoted, direct_ollama is default, Nutrition has provider voice, or non-training sections are provider-integrated.

Recently completed: Full Report Section Registry v1 and Nutrition Report Section Boundary v1.

Important files:
- `docs/project_memory/current_state.md`
- `docs/project_memory/backend_truth_contract.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`

Important tests:
- `tests/test_full_report_section_registry.py`
- `tests/test_nutrition_report_section_boundary.py`
- `tests/test_full_report_composition_boundary.py`
- `tests/test_report_persistence_boundary.py`

Known risks:
- Context loss across sessions.
- Provider boundaries being broadened accidentally.
- qwen3 being treated as promoted prematurely.
- Nutrition voice being implemented before readiness review.

Next recommended milestone: `Nutrition Provider Readiness Review v1`

Non-goals:
- Do not build RAG, embeddings, vector DB, or agent memory.
- Do not change provider behavior.
- Do not loosen validators.
- Do not add nutrition provider voice yet.


Instructions for assistant:

Use repo files and project memory as source of truth. Do not invent files, tests, endpoints, or behavior.

Before changing code, inspect current files. Prefer small diffs, explicit validation, and copy/paste-friendly commands. If the milestone is docs-only, do not touch runtime code.
