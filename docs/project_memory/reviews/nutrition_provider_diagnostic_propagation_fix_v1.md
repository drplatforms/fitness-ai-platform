# Nutrition Provider Diagnostic Propagation Fix v1 Review

Date: 2026-06-18

Review status: IMPLEMENTED / READY_FOR_DIAGNOSTIC_MATRIX_QA_RETRY

## Problem reviewed

Nutrition Provider Diagnostic Matrix QA v1 failed because diagnostics were not visible in the debug/QA runtime surface for rejected full-report Nutrition provider candidates.

The safety boundary was intact. The failure was propagation-only.

## Root cause

The most likely propagation break was confirmed in the configured Nutrition provider boundary.

`DirectOllamaNutritionReportSectionProviderResult` could carry sanitized diagnostic fields, but `NutritionReportSectionProviderResult` only returned:

- `approved_section`
- `safe_metadata`

Because `safe_metadata` intentionally excludes diagnostic categories/fields, the configured provider service dropped the debug/QA diagnostics before the full-report layer could expose them.

The full-report job/status layer also had no explicit debug endpoint that surfaced Nutrition diagnostics from the full-report Nutrition section result.

## Fix strategy

Preserve diagnostics in an internal/debug wrapper, not in safe metadata.

This keeps the project boundaries aligned:

- provider validation result owns diagnostic derivation
- direct provider result carries sanitized diagnostics
- configured provider result preserves sanitized diagnostics
- full-report debug/QA status exposes sanitized diagnostics
- public/persisted metadata remains sanitized

## Implementation review

The implementation adds diagnostic propagation without altering the validator decision rules.

Key behavior:

- validation failures keep deterministic fallback behavior
- diagnostics remain safe category/field names only
- safe metadata remains allowlisted and diagnostic-free
- persisted history remains diagnostic-free
- normal status endpoint remains diagnostic-free
- debug endpoint exposes diagnostics for QA
- unmapped validation failures produce `validation_failure` instead of empty categories

## Accepted debug-only surface

`/reports/status/{job_id}/debug` may expose:

- `nutrition_section_provider_debug.validation_error_categories`
- `nutrition_section_provider_debug.validation_error_fields`
- `nutrition_section_provider_debug.validation_error_count`
- `nutrition_section_provider_debug.first_validation_error_category`
- `nutrition_section_provider_debug.first_validation_error_field`

These are not persisted and are not included in normal `/reports/status/{job_id}`.

## Non-goals preserved

- No validator loosening.
- No provider approval-quality tuning.
- No prompt changes.
- No qwen3.
- No Level 5 promotion.
- No Training provider changes.
- No UI changes.

## Recommendation

Accept this milestone if local Windows validation passes.

Then proceed to:

`Nutrition Provider Diagnostic Matrix QA Retry v1`

The retry should capture diagnostics from the explicit debug/QA endpoint and verify categories are populated for rejected candidates.
