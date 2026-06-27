# QA Handoff Current

Milestone: Project Memory Warning Review v1

QA status: docs-only project-memory validation required.

Branch: `feature/project-memory-warning-review-v1`.

Source baseline: `main` at `4abf453`.

Commit-check mode: docs-only.

## QA focus

This milestone has no runtime behavior.

QA should validate that only docs/project-memory files changed and that current canonical memory reflects the accepted/merged serving-unit contract.

Primary checks:

- no Python files changed;
- no API routes changed;
- no database/schema code changed;
- no tests changed unless explicitly required by project-memory tooling;
- no Streamlit files changed;
- no provider/Ollama/CrewAI files changed;
- no food suggestion, workout, recovery, or report behavior changed;
- project memory is internally aligned with main baseline `4abf453`;
- Nutrition Serving Unit Logging Contract Design v1 is shown as accepted/merged;
- next milestone remains Nutrition Serving Unit Logging Backend v1;
- remaining project-memory warnings are documented as historical/archive noise when non-actionable.

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

The warning count may not reach zero. That is acceptable if `FAIL=0`, current canonical memory is accurate, and non-actionable warnings are documented.

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
