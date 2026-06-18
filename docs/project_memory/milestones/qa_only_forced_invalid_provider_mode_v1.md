# QA-Only Forced Invalid Provider Mode v1

Status: IMPLEMENTED / PENDING RUNTIME QA

## Goal

Add a safe QA-only forced-invalid Nutrition provider mode so Nutrition Level 5 fallback semantics can be runtime-tested without depending on live model failure.

## Implementation

A disabled-by-default environment flag was added:

- `AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT=true`

When the normal Nutrition provider gates are enabled and the configured provider is `direct_ollama`, this flag makes the direct-Ollama Nutrition provider path build a deterministic parseable-but-invalid candidate locally. The live model is not called.

The invalid candidate parses successfully, fails backend validation, and triggers deterministic Nutrition fallback through the same fallback boundary used by real provider validation failures.

## Expected forced-invalid behavior

- `nutrition_provider_attempted=true`
- `nutrition_selected_provider=direct_ollama`
- `nutrition_parse_status=success`
- `nutrition_candidate_valid=false`
- `nutrition_validation_status=rejected`
- `nutrition_validation_errors_count>0`
- `nutrition_fallback_used=true`
- `nutrition_fallback_reason=qa_forced_invalid_provider_output`
- `nutrition_section_source=deterministic_nutrition_report_section_fallback`
- `provider_integrated_report_sections=training`

`provider_integrated_report_sections` must not include `nutrition_report_section` when the forced-invalid provider path falls back.

## Safety boundaries

- Disabled by default.
- Requires explicit QA/test env flag.
- Does not make `direct_ollama` default.
- Does not remove provider gates.
- Does not remove deterministic fallback.
- Does not loosen validators.
- Does not call qwen3.
- Does not change Training behavior.
- Does not change Streamlit/UI.
- Does not expose raw provider output, rejected candidate text, raw validation errors, prompt/schema, model-facing context, or debug internals publicly or in persisted history.

## Next status

Recommended next milestone:

`Nutrition Level 5 Forced-Fallback Runtime QA v1`
