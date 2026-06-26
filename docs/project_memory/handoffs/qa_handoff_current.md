# QA Handoff Current

Milestone: Nutrition Catalog Diagnostic v1

QA status: diagnostic/tool validation only. No browser smoke required unless runtime/UI behavior changes.

Branch: `feature/nutrition-catalog-diagnostic-v1`.

## QA focus

This milestone should validate that the diagnostic is read-only, deterministic enough for the current data state, and reports the expected nutrition catalog foundation sections.

Primary checks:

- diagnostic tool runs on Windows;
- diagnostic tool runs on Linux;
- diagnostic output is readable;
- diagnostic JSON output is created when requested;
- focused tests pass;
- project memory validation passes;
- no data is modified;
- no provider/Ollama/OpenAI is required;
- no Streamlit behavior changed;
- no food catalog expansion was added;
- no serving units were implemented;
- no food logging behavior changed;
- no nutrition calculation behavior changed;
- no snapshots, qa_artifacts, local runtime outputs, or patch/apply scripts are committed.

## Expected validation

```powershell
git diff --check
pytest tests/test_nutrition_catalog_diagnostic_v1.py -q
python tools/nutrition_catalog_diagnostic.py --output ..\nutrition_catalog_diagnostic_v1.json
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q
scripts/dev_commit_check.ps1 -Mode code
python -m py_compile services/nutrition_catalog_diagnostic_service.py
python -m py_compile tools/nutrition_catalog_diagnostic.py
```

Linux validation is recommended because the tool inspects runtime data paths.

No browser smoke required.

## Expected diagnostic sections

- Catalog Summary
- Nutrient Completeness
- Serving Unit Readiness
- Alias/Search Readiness
- High-Value Staple Coverage
- Duplicate/Near-Duplicate Risks
- Logging Assumptions
- Actuals/Targets Dependencies
- Food Suggestion Readiness
- AI/Provider Grounding Readiness
- Recommended Next Steps
