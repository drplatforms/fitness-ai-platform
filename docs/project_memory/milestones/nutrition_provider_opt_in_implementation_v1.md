# Nutrition Provider Opt-In Implementation v1

Branch: feature/training-evidence-claim-service
Status: Implemented locally / pending Architecture review
Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition had a backend-owned report-section boundary, provider-safe contract models, parser scaffolding, validator scaffolding, and deterministic fallback, but no isolated provider execution path. Architecture approved the first provider execution milestone with strict boundaries: opt-in only, deterministic fallback protected, fake-provider tested, no live Ollama dependency in pytest, and no full-report provider integration or Level 5 promotion.

## What changed

- Added isolated direct-Ollama Nutrition report section provider module.
- Added configured Nutrition report section provider service.
- Added provider-safe prompt/context construction using `NutritionReportEvidenceContext` and approved nutrition evidence only.
- Wired fake/provider candidate output through the accepted parser and validator contract.
- Converted approved candidates to `ApprovedNutritionReportSection`.
- Added deterministic fallback on parse, validation, timeout, exception, non-string output, invalid provider, or disabled provider path.
- Added safe allowlisted metadata for provider status, parse status, validation status, fallback status, confidence ceiling, approved claim types, food suggestion count, section source, and latency.
- Updated section registry to reflect Nutrition as Level 4 but not full-report provider-integrated.
- Added fake-provider tests for direct provider and configured provider service.

## Files/modules touched

- `models/nutrition_provider_contract_models.py`
- `services/nutrition_provider_validation_service.py`
- `services/nutrition_report_section_direct_ollama_provider.py`
- `services/nutrition_report_section_provider_service.py`
- `services/full_report_section_registry_service.py`
- `tests/nutrition_provider_fixtures.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_report_section_provider_service.py`
- `tests/test_nutrition_report_section_boundary.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/full_report_section_registry_v1.md`

## Architecture decision

Nutrition provider execution is now allowed only as an isolated opt-in section path. It is not full-report provider integration. Training remains the only full-report provider-integrated section.

## Validation/tests

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
```

Focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_report_section_direct_ollama_provider.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_report_section_provider_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_parser.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_validation.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_fallback.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_report_section_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
```

## Runtime QA

Not required unless Architecture requests section-only provider runtime QA. This milestone does not wire Nutrition into full-report async generation, persistence, or public report composition.

Recommended next runtime QA milestone: `Nutrition Provider Opt-In Runtime QA v1`.

## Known limitations

- Nutrition provider execution is not integrated into full-report generation.
- Nutrition is not Level 5.
- No qwen3 testing is included.
- Runtime qwen2.5 schema adherence is unknown until opt-in runtime QA.
- Safe metadata is internal only and not currently persisted through full-report history.

## Next recommended step

Ask Architecture to review for `READY_FOR_OPT_IN_RUNTIME_QA` and approve a section-only Nutrition provider runtime QA milestone.
