# Nutrition Forced-Fallback Runtime QA Plan v1

Status: SUPERSEDED BY ACCEPTED RUNTIME QA

## Purpose

Validate Nutrition Level 5 fallback runtime semantics using the QA-only forced-invalid provider mode.

## Setup

Enable the normal opt-in Nutrition provider gates plus the QA-only forced-invalid flag:

```text
AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED=true
AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=true
NUTRITION_REPORT_SECTION_PROVIDER=direct_ollama
NUTRITION_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
AI_HEALTH_REPORT_NUTRITION_FORCE_INVALID_PROVIDER_OUTPUT=true
```

The forced-invalid flag should prevent a live model call and produce a deterministic invalid candidate.

## Runtime expectations

Expected forced-fallback result:

- provider attempted
- selected provider remains `direct_ollama`
- parse status is `success`
- candidate valid is `false`
- validation status is `rejected`
- validation error count is greater than 0
- fallback is used
- fallback reason is `qa_forced_invalid_provider_output`
- Nutrition section source is `deterministic_nutrition_report_section_fallback`
- `provider_integrated_report_sections` remains `training`
- `nutrition_report_section` is not included in provider-integrated sections for fallback output

## Safety checks

Confirm normal status, persisted history, public report text, and provider safe metadata do not expose:

- raw provider output
- rejected candidate text
- raw validation errors
- prompt/schema
- model-facing context
- parser/debug internals
- validation_error_categories
- validation_error_fields
- approved practical food focus option context

The debug endpoint may expose safe diagnostic category/field names only.

## Non-goals

- Do not run qwen3.
- Do not make `direct_ollama` default.
- Do not remove fallback or provider gates.
- Do not change public positioning until QA result is accepted.

## Result

Superseded by `docs/project_memory/runtime_qa/nutrition_level_5_forced_fallback_runtime_qa_v1.md`.

Nutrition Level 5 Forced-Fallback Runtime QA v1 passed with `PASS_FORCED_FALLBACK_RUNTIME_QA` and final status `NUTRITION_LEVEL_5_RUNTIME_SEMANTICS_COMPLETE`.
