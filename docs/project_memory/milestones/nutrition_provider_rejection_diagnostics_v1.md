# Nutrition Provider Rejection Diagnostics v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local validation complete / pending Architecture review

Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition Provider Matrix Retry Runtime QA v1 proved runtime safety but every seeded user fell back after validation rejection. Runtime metadata provided only `validation_errors_count=1`, which is too coarse for safe provider tuning.

## What changed

- Added structured validation diagnostic categories and fields.
- Added debug/QA-only diagnostic fields to Nutrition provider result objects.
- Kept public/persisted safe metadata sanitized.
- Added tests for diagnostic category generation.
- Added tests proving diagnostic categories are not persisted in public report history.
- Added project-memory review and runtime QA summary docs.

## Files/modules touched

- `models/nutrition_provider_contract_models.py`
- `services/nutrition_provider_validation_service.py`
- `services/nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_full_report_opt_in_integration.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/reviews/nutrition_provider_rejection_diagnostics_v1.md`
- `docs/project_memory/runtime_qa/nutrition_provider_matrix_retry_runtime_qa.md`

## Architecture decision

Pending review.

## Validation/tests

Focused tests passed in sandbox:

- validation/direct provider diagnostics: 19 passed.
- validation/provider/full-report/persistence focused suite: 36 passed.
- recommended provider/rejection focused suite: 47 passed.
- broader focused safety suite: 69 passed.

## Runtime QA

Required next. This milestone adds diagnostics; it does not prove new provider approval behavior.

## Known limitations

- Diagnostics are safe categories and fields, not raw validation messages.
- Runtime QA must confirm diagnostics are useful across actual qwen2.5 outputs.
- Provider approval quality is not claimed to have improved in this milestone.

## Next recommended step

`Nutrition Provider Diagnostic Matrix QA v1`
