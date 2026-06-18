# Nutrition Provider Rejection Analysis v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local validation complete / pending Architecture review

Date/commit: Unknown / verify with `git log --oneline -5`

## Problem

Nutrition Full Report Opt-In Runtime QA v1 passed safely but the qwen2.5:3b Nutrition provider candidate was rejected after successful parsing.

Runtime metadata showed:

- parse status: success
- validation status: rejected
- validation errors count: 1
- fallback reason: nutrition_provider_validation_failed
- final Nutrition section source: deterministic fallback

The system behaved safely, but provider approval quality needs analysis before retrying runtime QA or considering promotion.

## What changed

- Added `approved_numeric_values` to `NutritionProviderSafeContext`.
- Built `approved_numeric_values` from exact backend-approved actuals, comparison values, and approved food-suggestion numbers.
- Explicitly excluded derived gaps/deltas/percentages from approved numeric values.
- Updated direct-Ollama Nutrition prompt to forbid calculated/inferred numeric gaps, deltas, percentages, serving sizes, and targets.
- Added tests reproducing the likely qwen2.5 rejection class with a fake candidate using an inferred `40 g` protein gap.
- Added this milestone summary.
- Added `docs/project_memory/reviews/nutrition_provider_rejection_analysis_v1.md`.
- Updated project memory current state and open questions.
- Added runtime QA summary for Nutrition Full Report Opt-In Runtime QA v1.

## Files/modules touched

- `models/nutrition_provider_contract_models.py`
- `services/nutrition_provider_validation_service.py`
- `services/nutrition_report_section_direct_ollama_provider.py`
- `tests/test_nutrition_provider_contract_validation.py`
- `tests/test_nutrition_report_section_direct_ollama_provider.py`
- `docs/project_memory/reviews/nutrition_provider_rejection_analysis_v1.md`
- `docs/project_memory/runtime_qa/nutrition_full_report_opt_in_runtime_qa.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Architecture decision

Architecture accepted Nutrition Full Report Opt-In Runtime QA v1 as `PASS_WITH_SAFE_FALLBACK` and approved Nutrition Provider Rejection Analysis v1.

## Validation/tests

Required local validation:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code`
- `pytest tests/test_nutrition_report_section_provider_service.py -q`
- `pytest tests/test_nutrition_report_section_direct_ollama_provider.py -q`
- `pytest tests/test_nutrition_provider_contract_validation.py -q`
- `pytest tests/test_nutrition_provider_contract_parser.py -q`
- `pytest tests/test_nutrition_full_report_opt_in_integration.py -q`
- `pytest tests/test_report_persistence_boundary.py -q`

## Runtime QA

Runtime QA is required next because this milestone changes provider prompt/context behavior.

Recommended next runtime QA:

- rerun full opt-in Nutrition full-report integration for user 102/date 2026-06-14 with qwen2.5:3b,
- verify parse/validation/fallback metadata,
- verify no raw/debug/provider leakage,
- verify Nutrition remains Level 4,
- do not run qwen3,
- do not run users 101-105 sweep unless Architecture approves after minimum retry QA.

## Known limitations

The raw rejected runtime candidate and raw validation error list were not available in the uploaded QA handoff. The implemented test reproduces the most plausible strict-validator rejection category from the current code: model-inferred numeric gap values.

## Next recommended step

Nutrition Provider Retry Runtime QA v1.

Expected status after this milestone:

`READY_FOR_RETRY_RUNTIME_QA`
