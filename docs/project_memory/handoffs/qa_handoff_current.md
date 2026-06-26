# QA Handoff Current

Milestone: Nutrition Serving Unit Logging Contract Design v1

QA status: docs-only contract validation required.

Branch: `feature/nutrition-serving-unit-logging-contract-design-v1`.

Commit-check mode: docs-only.

## QA focus

This milestone has no runtime behavior.

QA should validate that only approved docs/project-memory files changed and that the design contract preserves all non-goals.

Primary checks:

- no Python files changed;
- no API routes changed;
- no database/schema code changed;
- no tests changed;
- no Streamlit files changed;
- no provider/Ollama/CrewAI files changed;
- no food suggestion, workout, recovery, or report behavior changed;
- project memory is internally aligned with main baseline `9cb1d41` and current contract milestone;
- design doc answers the Architecture questions;
- future implementation scope remains clearly separated from this docs-only milestone.

## Expected validation

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

Expected changed files:

- `docs/nutrition_serving_unit_logging_contract_design.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/milestones/nutrition_serving_unit_logging_contract_design_v1.md`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`

If any other files appear, stop and correct scope.

## Runtime smoke

Not required.

No browser smoke is required because there are no Streamlit or backend runtime changes.

## Future QA expectations

For the later Nutrition Serving Unit Logging Backend v1, QA should expect tests for:

- active canonical food can be logged by serving unit;
- inactive canonical food is rejected;
- inactive serving unit is rejected;
- serving unit must belong to canonical food;
- serving quantity must be positive;
- resolved grams are persisted;
- provenance metadata is persisted;
- existing grams logging remains stable;
- existing canonical grams logging remains stable;
- Target-vs-Actual sees serving-unit logs through resolved grams;
- missing nutrients remain unknown, not zero;
- no raw source payloads are exposed;
- no provider/Ollama/CrewAI call occurs.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains available for local port inspection.
