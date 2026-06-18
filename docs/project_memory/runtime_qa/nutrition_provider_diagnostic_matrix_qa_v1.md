# Nutrition Provider Diagnostic Matrix QA v1

Date: 2026-06-18

Result: FAIL

Failure type: DIAGNOSTIC_CAPTURE_MISSING

Runtime safety: PASS

Nutrition maturity: Level 4

Level 5 promotion: NOT APPROVED

## Summary

Nutrition Provider Diagnostic Matrix QA v1 failed because rejected Nutrition provider candidates did not expose safe diagnostic categories/fields in the debug/QA runtime output.

This was not a provider safety failure and not a persistence leakage failure.

## Accepted safety result

Confirmed by Architecture:

- all five report jobs completed
- direct_ollama/qwen2.5:3b was used
- qwen3 was not used
- provider attempted for all users
- provider output parsed successfully for all users
- validation rejected all candidates
- deterministic fallback was used safely
- no raw provider output leaked
- no raw output preview leaked
- no rejected candidate text leaked
- no prompt/schema leaked
- no raw validation error list leaked
- no diagnostic fields leaked into public report or current-job persisted history
- no traceback/exception text leaked
- no provider payload leaked
- no model-facing context leaked
- no parser/debug internals leaked
- no raw CrewAI error text leaked
- no unsupported derived numeric claims appeared
- no invented/action-oriented food suggestions without approved evidence appeared
- no unsafe serving/gram food claims appeared
- provider_integrated_report_sections remained training
- Nutrition remained Level 4
- Nutrition was not marked Level 5

## Failed requirement

Expected rejected provider candidates to expose:

- `validation_error_categories`
- `validation_error_fields`
- `first_validation_error_category`
- `first_validation_error_field`

Observed for users 101-105:

- `validation_error_categories=[]`
- `validation_error_fields=[]`
- `first_validation_error_category=null`
- `first_validation_error_field=null`

## Required follow-up

Fix propagation before additional provider tuning.

Next implementation milestone:

`Nutrition Provider Diagnostic Propagation Fix v1`
