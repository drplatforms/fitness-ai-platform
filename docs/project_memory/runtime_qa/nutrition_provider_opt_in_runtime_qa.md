# Nutrition Provider Opt-In Runtime QA v1

Status: Accepted / PASS_WITH_DEBUG_ENDPOINT_CLARIFICATION

Date/commit: 2026-06-18 / `c0b3ff9 Add nutrition provider opt-in implementation`

## Summary

Runtime QA proved that Nutrition's isolated opt-in provider path can run safely behind explicit config gates while preserving deterministic default behavior and without leaking raw/debug/provider content into user-facing or persisted public surfaces.

This QA does not approve full-report integration.

This QA does not approve Level 5 promotion.

Nutrition remains Level 4.

Training remains the only full-report provider-integrated section.

## Default deterministic section smoke

Accepted result for user 102 / report date 2026-06-14:

- `nutrition_provider_execution_enabled=false`
- `provider_enabled=false`
- `provider_attempted=false`
- `selected_provider=deterministic`
- `selected_model=deterministic`
- `parse_status=not_attempted / deterministic path`
- `candidate_valid=not_attempted / deterministic path`
- `validation_status=approved / deterministic section returned safely`
- `validation_errors_count=0`
- `fallback_used=false / deterministic_default`
- `fallback_reason=null`
- `nutrition_section_source=deterministic`
- `provider_latency_ms=null`
- `raw_debug_terms=[]`
- `angle_brackets=false`
- `forbidden_seed_terms=[]`
- `nutrition_level=Level 4`
- `full_report_provider_integrated_sections=training only`
- decision: `PASS_WITH_DEBUG_ENDPOINT_CLARIFICATION`

## Opt-in direct_ollama section smoke

Accepted result for user 102 / report date 2026-06-14:

- `nutrition_provider_execution_enabled=true`
- `provider_enabled=true`
- `provider_attempted=true`
- `selected_provider=direct_ollama`
- `selected_model=qwen2.5:3b`
- `parse_status=success / parsed`
- `candidate_valid=true`
- `validation_status=approved`
- `validation_errors_count=0`
- `fallback_used=false`
- `fallback_reason=null`
- `fallback_source=null`
- `nutrition_section_source=direct_ollama_approved`
- `provider_latency_ms=present`
- `raw_debug_terms=[]`
- `angle_brackets=false`
- `forbidden_seed_terms=[]`
- `nutrition_level=Level 4`
- `full_report_provider_integrated_sections=training only`
- decision: `PASS_WITH_DEBUG_ENDPOINT_CLARIFICATION`

## Debug endpoint clarification

The following fields appeared only in explicit section-only debug endpoint metadata:

- `validation_errors=[]`
- `raw_output_preview_truncated=null`

These are accepted as content-safe debug endpoint fields.

They remain forbidden in:

- public report text
- user-facing section output
- persisted report history
- non-debug API responses
- UI-facing payloads

No backend code change is required unless these fields appear in public, user-facing, persisted, non-debug, or UI-facing output.

## Safety result

QA confirmed:

- no raw provider output appeared
- no rejected candidate text appeared
- no prompt/schema appeared
- no traceback/exception text appeared
- no raw validation error content appeared
- `validation_errors` was empty only
- `raw_output_preview_truncated` was null only
- no evidence showed these fields in public report text, persisted report history, non-debug API responses, or UI-facing payloads

## Full-report boundary result

Accepted:

- Nutrition remains Level 4.
- Nutrition is not Level 5.
- Nutrition is not full-report provider-integrated.
- Training remains the only full-report provider-integrated section.
- No qwen3 testing was performed.
- No full-report integration QA was performed.
- No users 101-105 sweep was performed.

## Next recommended milestone

`Nutrition Full Report Opt-In Integration Design Review v1`

This is a design-review milestone.

Do not implement full-report integration until Architecture approves an implementation milestone.
