# Nutrition Provider Diagnostic Propagation Fix v1

Date: 2026-06-18

Status: IMPLEMENTED / READY_FOR_DIAGNOSTIC_MATRIX_QA_RETRY

## Context

Nutrition Provider Diagnostic Matrix QA v1 failed with failure type `DIAGNOSTIC_CAPTURE_MISSING`.

Runtime safety passed, but rejected Nutrition provider candidates did not expose safe diagnostic categories/fields in the debug/QA runtime surface used by matrix QA.

Observed rejected runtime metadata was limited to:

- `nutrition_parse_status=success`
- `nutrition_candidate_valid=false`
- `nutrition_validation_status=rejected`
- `nutrition_validation_errors_count=1`

But debug/QA diagnostic fields were empty/null:

- `validation_error_categories=[]`
- `validation_error_fields=[]`
- `first_validation_error_category=null`
- `first_validation_error_field=null`

## Goal

Ensure rejected Nutrition provider candidates expose safe validation diagnostics in explicit debug/QA runtime output while keeping public report text, provider safe metadata, and persisted report history sanitized.

## What changed

- Extended `NutritionReportSectionProviderResult` to preserve debug/QA-only diagnostic fields from the direct provider result:
  - `validation_error_categories`
  - `validation_error_fields`
  - `first_validation_error_category`
  - `first_validation_error_field`
- Updated the configured Nutrition provider service to copy diagnostics from `DirectOllamaNutritionReportSectionProviderResult` into the configured result wrapper.
- Added `nutrition_section_provider_debug_metadata(...)` in `services/coordinator_service.py`.
- Added safe fallback diagnostic category behavior: if `nutrition_validation_errors_count > 0` but no category is mapped, debug metadata emits `validation_failure` instead of an empty category list.
- Updated async report job status storage to retain:
  - safe Nutrition provider job metadata
  - debug/QA-only Nutrition provider diagnostics
- Added `/reports/status/{job_id}/debug` for explicit debug/QA status inspection.
- Kept normal `/reports/status/{job_id}` free of debug diagnostic fields.
- Kept persisted metadata sanitization unchanged.

## Public/persisted safety boundary

Public/persisted metadata remains limited to safe summary fields such as:

- `nutrition_validation_errors_count`
- `nutrition_validation_status`
- `nutrition_fallback_reason`
- `nutrition_section_source`
- `nutrition_provider_latency_ms`

The following remain absent from provider safe metadata and persisted report history:

- `validation_error_categories`
- `validation_error_fields`
- `first_validation_error_category`
- `first_validation_error_field`
- raw validation error strings
- raw provider output
- rejected candidate text
- prompt/schema
- model-facing context
- parser internals
- traceback/exception text

## Tests added/proved

- Configured Nutrition provider service preserves diagnostics on validation rejection.
- Full-report Nutrition debug metadata exposes diagnostics while safe metadata does not.
- Debug metadata emits `validation_failure` when validation errors exist but category mapping is empty.
- `/reports/status/{job_id}/debug` exposes Nutrition diagnostic fields.
- Normal `/reports/status/{job_id}` does not expose `nutrition_section_provider_debug`.
- Persisted report history does not include diagnostic fields even if debug metadata is passed before save.

## Boundaries preserved

- No validator loosening.
- No unsupported claim approval.
- No provider prompt tuning.
- No qwen3 runtime.
- No users 101-105 retry matrix rerun in this milestone.
- No Nutrition Level 5 promotion.
- No Training provider behavior changes.
- No Streamlit/UI changes.
- No nutrition target formula changes.
- No meal planning, new foods, RAG, embeddings, or agent orchestration.

## Validation

Focused validation completed in sandbox:

- `pytest tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_report_section_direct_ollama_provider.py tests/test_nutrition_report_section_provider_service.py tests/test_nutrition_full_report_opt_in_integration.py tests/test_report_status.py tests/test_report_persistence_boundary.py -q`
- Result: `50 passed`

Broader focused safety validation completed in sandbox:

- `pytest tests/test_nutrition_report_section_boundary.py tests/test_full_report_section_registry.py tests/test_full_report_composition_boundary.py tests/test_nutrition_report_section_provider_service.py tests/test_nutrition_report_section_direct_ollama_provider.py tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_provider_contract_parser.py tests/test_nutrition_provider_contract_fallback.py tests/test_nutrition_full_report_opt_in_integration.py tests/test_report_persistence_boundary.py tests/test_report_status.py tests/test_api_smoke.py -q`
- Result: `73 passed`

Compile check passed for touched Python files.

## Expected next milestone

`Nutrition Provider Diagnostic Matrix QA Retry v1`

Recommended QA scope:

- Rerun users 101-105 full-report opt-in Nutrition matrix with qwen2.5:3b.
- Capture diagnostics from `/reports/status/{job_id}/debug` or equivalent explicit debug/QA runtime surface.
- Verify rejected candidates expose non-empty `validation_error_categories` when `nutrition_validation_errors_count > 0`.
- Verify public report text and persisted history remain clean.
- Verify Nutrition remains Level 4.
- Do not run qwen3.
- Do not approve Level 5.
