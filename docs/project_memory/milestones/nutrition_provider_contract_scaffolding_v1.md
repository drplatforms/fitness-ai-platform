# Nutrition Provider Contract Scaffolding v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local focused tests passed / pending Architecture review

Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition Provider Contract Design v1 defined the provider-safe contract required before a future opt-in nutrition provider can be attempted. The repo needed code scaffolding for the context, parser, validator, metadata, fallback result, and tests without implementing provider execution.

## What changed

- Added provider-safe nutrition context model.
- Added candidate parser contract for `CandidateNutritionReportSection`.
- Added validator scaffolding for field-level claim gating, numeric validation, confidence ceiling checks, canonical food/serving checks, and unsupported language rejection.
- Added safe metadata allowlist for future provider attempts.
- Added deterministic fallback result wrapper.
- Added parser, validator, and fallback tests.

## Files/modules touched

- `models/nutrition_provider_contract_models.py`
- `services/nutrition_provider_candidate_parser.py`
- `services/nutrition_provider_validation_service.py`
- `tests/test_nutrition_provider_contract_parser.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_provider_contract_fallback.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/milestones/nutrition_provider_contract_scaffolding_v1.md`

## Architecture decision

This milestone is scaffolding only.

Nutrition remains not provider-integrated.

Training remains the only provider-integrated full-report section.

No provider execution is added.

No Ollama call is added.

No qwen3 testing or promotion is added.

## Validation/tests

Expected focused validation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_report_section_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_parser.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_validation.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_nutrition_provider_contract_fallback.py -q
```

Sandbox focused validation passed:

- `tests/test_nutrition_provider_contract_parser.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_provider_contract_fallback.py`
- `tests/test_nutrition_report_section_boundary.py`
- `tests/test_full_report_section_registry.py`
- selected report/persistence/provider/API safety tests

## Runtime QA

Not required for this milestone unless Architecture requests it, because no provider execution, persistence behavior, or report generation behavior changed.

## Known limitations

- This is not provider implementation.
- This does not call `direct_ollama`.
- The validator is strict enough for first scaffolding tests but may need more negative cases before provider execution.
- Safe metadata exists as a contract helper but is not persisted by runtime report generation yet.
- Nutrition is not promoted to Level 4 or Level 5.

## Next recommended step

Recommended status after review:

`READY_FOR_PROVIDER_IMPLEMENTATION_DESIGN_REVIEW` if Architecture accepts the parser/validator/fallback scaffolding.

Recommended next milestone should still avoid qwen3 and should not promote Nutrition until a provider implementation plan, runtime QA plan, and strict negative test matrix are approved.
