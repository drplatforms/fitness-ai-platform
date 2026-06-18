# Nutrition Provider Matrix Rejection Analysis v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local validation complete / pending Architecture review

Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition Full Report Runtime QA Matrix v1 proved runtime safety across seeded users 101-105, but provider quality was inconsistent:

- user 102 approved
- users 101, 103, 104, and 105 fell back safely after validation rejection

The next task was to identify a small safe improvement that could raise approval quality without weakening validators.

## What changed

- Added safe negative food-suggestion language handling to the Nutrition provider validator.
- Updated Nutrition direct-Ollama prompt for empty `approved_food_suggestions`.
- Added fake-candidate tests reproducing safe no-suggestion text.
- Added fake-candidate tests proving invented food suggestions still reject.
- Added review documentation.
- Added runtime QA matrix memory summary.
- Updated current project memory.

## Files/modules touched

- `services/nutrition_provider_validation_service.py`
- `services/nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/milestones/nutrition_provider_matrix_rejection_analysis_v1.md`
- `docs/project_memory/reviews/nutrition_provider_matrix_rejection_analysis_v1.md`
- `docs/project_memory/runtime_qa/nutrition_full_report_runtime_qa_matrix_v1.md`

## Architecture decision

Nutrition remains Level 4.

Training remains the only Level 5 full-report provider-integrated section.

This milestone does not approve Level 5 promotion, qwen3, meal planning, new foods, RAG, or validator loosening.

## Validation/tests

Run:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code`
- `pytest tests/test_nutrition_report_section_provider_service.py -q`
- `pytest tests/test_nutrition_report_section_direct_ollama_provider.py -q`
- `pytest tests/test_nutrition_provider_contract_validation.py -q`
- `pytest tests/test_nutrition_provider_contract_parser.py -q`
- `pytest tests/test_nutrition_full_report_opt_in_integration.py -q`
- `pytest tests/test_report_persistence_boundary.py -q`

## Runtime QA

Required next.

Recommended next runtime milestone:

`Nutrition Provider Matrix Retry Runtime QA v1`

## Known limitations

The raw rejected candidates and raw validation errors from matrix users 101, 103, 104, and 105 were not provided in the Architecture handoff.

This milestone targets a concrete validator/prompt ambiguity that is likely to affect users without approved food suggestions, but it does not claim this was the exact runtime rejection string for all four rejected users.

## Next recommended step

Run Nutrition Provider Matrix Retry Runtime QA v1 across seeded users 101-105 with qwen2.5:3b.
