# Nutrition Provider Level 5 Promotion v1

Status: IMPLEMENTED / PENDING RUNTIME QA

## Context

Nutrition Provider Level 5 Promotion Readiness Review v1 was accepted with readiness status:

`READY_FOR_NUTRITION_LEVEL_5_PROMOTION_PATCH`

The strongest readiness basis was Nutrition Provider Approved Suggestion Runtime QA v1:

- users 101-105 provider-approved
- provider: direct_ollama
- model: qwen2.5:3b
- safe_fallback_count: 0
- fail_count: 0
- practical_food_focus_failure_count: 0
- parser success for all users
- validation approved for all users
- fallback_used false for all users
- public/persisted leakage checks clean

## Promotion meaning

Nutrition Report Section is now marked as a Level 5 provider-integrated full-report section.

This means:

- a full-report integrated Nutrition provider path exists
- provider output is parsed before rendering
- provider output is validated before rendering
- invalid provider output falls back deterministically
- deterministic fallback remains available
- provider execution remains explicitly gated
- persisted history remains public-safe
- debug/QA diagnostics remain separated from public/status/persisted surfaces
- metadata records provider/source/validation/fallback facts
- raw provider output, prompt/schema, rejected candidate text, raw validation errors, model-facing context, parser internals, and debug objects remain excluded from public/persisted history

## Implemented scope

- Promoted `nutrition_report_section` registry maturity to Level 5.
- Marked `nutrition_report_section` as `opt_in_full_report_integrated`.
- Preserved `nutrition_target_display` as a separate Level 2 display contract.
- Preserved Training as a separate Level 5 provider-integrated section.
- Added report-specific provider-integrated metadata semantics for Nutrition.
- Updated tests for approved, fallback, and disabled-gate Nutrition metadata behavior.
- Updated project memory docs.

## Report-specific metadata semantics

When Nutrition provider output is approved:

- `nutrition_section_source=direct_ollama_approved`
- `nutrition_candidate_valid=true`
- `nutrition_validation_status=approved`
- `nutrition_fallback_used=false`
- `provider_integrated_report_sections` includes `nutrition_report_section`

When Nutrition provider falls back deterministically:

- fallback/source metadata remains explicit
- `provider_integrated_report_sections` does not include `nutrition_report_section`

When Nutrition provider is not attempted because gates are disabled:

- deterministic/source metadata remains explicit
- `provider_integrated_report_sections` does not include `nutrition_report_section`

## Boundaries preserved

- direct_ollama is not default
- deterministic fallback remains
- provider gates remain
- validators were not loosened
- qwen3 was not run or promoted
- raw provider/debug output is not exposed publicly
- raw validation errors are not persisted
- rejected candidate text is not persisted
- prompt/schema/model-facing context are not persisted
- Nutrition Target Display and Nutrition Report Section remain separate
- no meal planning, new foods, serving-size expansion, RAG, embeddings, or agent orchestration were added
- Training behavior was not changed
- Streamlit/UI was not changed

## Expected result

`NUTRITION_LEVEL_5_PROMOTION_IMPLEMENTED_PENDING_QA`

## Recommended next QA

Nutrition Level 5 Promotion Runtime QA v1.
