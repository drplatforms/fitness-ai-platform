# Next Milestone

Current milestone in progress: Nutrition Serving Unit Logging Contract Design v1.

Recommended branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Source branch: `main`.

Required source main commit: `9cb1d41`.

Milestone type: backend design / contract / project memory only.

Commit-check mode: docs-only.

## Objective

Design how backend-owned serving-unit metadata should enter future nutrition logging while preserving the existing grams-based actuals bridge.

The design should define the contract before implementation touches:

- `/nutrition/log`;
- `/nutrition/{user_id}/log-canonical`;
- Streamlit nutrition logging;
- Target-vs-Actual;
- provider/Ollama/CrewAI paths.

## Approved deliverable

- `docs/nutrition_serving_unit_logging_contract_design.md`

## Approved project-memory updates

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/milestones/nutrition_serving_unit_logging_contract_design_v1.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

## Design baseline approved by Architecture

Architecture approved these preliminary directions for the design contract:

1. Keep `food_entries` as the grams-based actuals bridge.
2. Prefer a companion serving-unit provenance table for future implementation.
3. Prefer a dedicated future endpoint: `POST /nutrition/{user_id}/log-serving`.
4. Persist resolved grams used at log time.
5. Preserve serving-unit provenance:
   - `canonical_food_id`
   - `serving_unit_id`
   - serving quantity
   - resolved grams
   - `grams_min`
   - `grams_max`
   - confidence
   - amount source
   - original serving display
6. Do not change Target-vs-Actual immediately.
7. Do not expose serving-unit internals to AI/provider yet.
8. Do not allow Streamlit to invent mappings.
9. Do not allow AI/provider to invent serving units, grams, conversions, macros, or actuals.
10. Treat serving-unit logging as a backend-owned convenience layer that resolves to grams.

## Questions the contract must answer

- Should serving-unit logs extend `food_entries`?
- Should serving-unit logs use a companion provenance table?
- Should a new canonical nutrition log table be created?
- Should resolved grams be persisted?
- Should min/max grams and confidence be copied onto the log?
- Should logs store canonical food id, legacy food id, or both?
- How should `amount_source` be represented?
- Which confidence vocabulary should be canonical?
- Should Target-vs-Actual change immediately?
- Should serving-unit logging affect actuals confidence?
- Should user overrides be supported in v1?
- Should future implementation use an existing endpoint or a new endpoint?
- Should the serving-unit endpoint allow grams override?
- What validation is required?
- How should missing nutrients behave?
- How should serving-unit logs display in history?
- Should serving-unit logs enter AI/provider context immediately?

## Strict non-goals

Do not implement serving-unit logging.

Do not modify `/nutrition/log`.

Do not modify `/nutrition/{user_id}/log-canonical`.

Do not add a new API endpoint.

Do not modify schema/code migrations.

Do not modify food_entries schema in code.

Do not modify Target-vs-Actual behavior.

Do not modify Streamlit.

Do not modify nutrition actuals math.

Do not modify AI/provider behavior.

Do not modify CrewAI/Ollama behavior.

Do not add meal planning.

Do not add food suggestion changes.

Do not add nutrition explanation changes.

Do not change canonical food search.

Do not expand serving-unit seed coverage.

Do not import USDA/source data.

Do not add barcode scanning.

Do not change workout generation.

Do not change recovery logic.

Do not add dependencies.

Do not commit snapshots, qa_artifacts, runtime JSON, patch scripts, or temp files.

Do not use `git add .`.

Do not run broad formatters for docs-only work.

## Validation

```powershell
git diff --check

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q

scripts/dev_commit_check.ps1 -Mode docs-only

. .\scripts\fitness_commands.ps1
fsweep

git status --short
```

Expected changed files are docs/project-memory files only.

If Python/runtime/API/Streamlit/test files appear in `git status`, stop and correct scope before commit.

## Recommended next milestone after acceptance

Recommended: Nutrition Serving Unit Logging Backend v1.

Purpose:

- add backend-owned serving-unit logging endpoint/service;
- resolve serving-unit quantity to grams;
- write resolved grams through existing actuals bridge;
- persist serving-unit provenance;
- preserve Target-vs-Actual behavior;
- preserve existing grams and canonical logging behavior.

Suggested next implementation sequence after this design is accepted:

1. Nutrition Serving Unit Logging Backend v1.
2. Nutrition Actuals Confidence Model v1.
3. Streamlit Serving Unit Logging UI v1.
4. Target-vs-Actual Confidence Display v1.
5. Nutrition Food Suggestions Serving-Aware v1.

## Historical authorization anchors

The following historical phrases remain required project-memory continuity anchors, not active scope for this milestone:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- `feature/daily-coach-async-persistence-contracts-schema-v1`
- schema/contracts
- NOT_AUTHORIZED_YET
