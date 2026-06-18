# Nutrition Provider Rejection Diagnostics v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local validation complete / pending Architecture review

Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition Provider Matrix Retry Runtime QA v1 passed safely but did not improve approval quality.

Every seeded user produced the same coarse runtime metadata:

- nutrition_parse_status: success
- nutrition_candidate_valid: false
- nutrition_validation_status: rejected
- nutrition_validation_errors_count: 1

This proves the parser and fallback boundary are safe, but it does not provide enough information to tune provider behavior safely. Continuing to adjust prompts or validators based only on `validation_errors_count=1` would be guessing.

## Goal

Add safe, structured, non-public rejection diagnostics for Nutrition provider validation failures.

The diagnostic layer should identify repeated failure categories without exposing:

- raw provider output
- rejected candidate text
- prompt/schema
- raw validation error strings
- traceback or exception text
- provider payloads
- model-facing context
- parser internals
- debug objects

## What changed

- Added safe validation category constants to `models/nutrition_provider_contract_models.py`.
- Extended `NutritionProviderCandidateValidationResult` with:
  - `validation_error_categories`
  - `validation_error_fields`
  - `validation_error_count`
  - `first_validation_error_category`
  - `first_validation_error_field`
- Added diagnostic category/field derivation in `services/nutrition_provider_validation_service.py`.
- Added debug/QA-only diagnostics to `DirectOllamaNutritionReportSectionProviderResult`.
- Kept provider `safe_metadata` unchanged and public/persisted-safe.
- Added tests proving diagnostics are generated for fake invalid candidates.
- Added tests proving diagnostics are not included in safe metadata or persisted report history.

## Safe diagnostic categories

Current diagnostic categories include:

- unsupported_numeric_value
- unsupported_food_suggestion
- unsupported_serving_size
- unsupported_meal_plan
- unsupported_medical_claim
- unsupported_supplement_claim
- unsupported_guarantee_claim
- unsupported_compliance_or_shame_language
- field_claim_not_approved
- confidence_ceiling_violation
- missing_required_field
- extra_key_detected
- invalid_enum_value
- empty_or_placeholder_text
- wrapper_object_detected
- invalid_json
- type_mismatch
- validation_failure

## Debug/QA-only fields

Allowed only for explicit debug/QA inspection:

- validation_error_categories
- validation_error_fields
- first_validation_error_category
- first_validation_error_field

When Nutrition metadata is prefixed for full-report QA, these correspond to:

- nutrition_validation_error_categories
- nutrition_validation_error_fields
- nutrition_first_validation_error_category
- nutrition_first_validation_error_field

These fields must not be persisted in report history or exposed in public/user-facing report output.

## Public/persisted metadata rule

Public/persisted metadata remains limited to summary fields such as:

- nutrition_validation_errors_count
- nutrition_validation_status
- nutrition_fallback_reason
- nutrition_section_source
- nutrition_provider_latency_ms

Raw validation error strings remain forbidden in public/persisted metadata.

## Validation/tests

Local validation completed in sandbox:

- `pytest tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_report_section_direct_ollama_provider.py -q` passed: 19 passed.
- `pytest tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_report_section_provider_service.py tests/test_nutrition_full_report_opt_in_integration.py tests/test_report_persistence_boundary.py -q` passed: 36 passed.
- `pytest tests/test_nutrition_report_section_provider_service.py tests/test_nutrition_report_section_direct_ollama_provider.py tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_provider_contract_parser.py tests/test_nutrition_full_report_opt_in_integration.py tests/test_report_persistence_boundary.py -q` passed: 47 passed.
- Broader focused safety suite passed: 69 passed.
- Py compile passed for touched/related files.

## Runtime QA

Runtime QA is required next because this milestone changes diagnostic behavior used for provider rejection triage.

## Recommended next milestone

`Nutrition Provider Diagnostic Matrix QA v1`

Goal: rerun the full-report opt-in Nutrition matrix for users 101-105 and capture safe diagnostic categories/fields for rejected candidates while verifying no diagnostic detail leaks into public report text or persisted report history.

## Expected status after review

`READY_FOR_DIAGNOSTIC_MATRIX_QA`

Do not claim provider approval improvement yet.
Do not claim Level 5 readiness.
