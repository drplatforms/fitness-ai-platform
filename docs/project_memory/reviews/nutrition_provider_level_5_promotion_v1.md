# Nutrition Provider Level 5 Promotion v1 Review

## Decision

Implemented as a controlled Level 5 promotion patch for `nutrition_report_section`.

## Status

`NUTRITION_LEVEL_5_PROMOTION_IMPLEMENTED_PENDING_QA`

## Summary

Nutrition Report Section is promoted to Level 5 provider-integrated status after accepted readiness review and provider-approved seeded runtime QA.

This promotion is intentionally narrow. It updates registry/maturity and report metadata semantics. It does not change provider defaults, gates, validation strictness, fallback behavior, model choice, UI, or Training behavior.

## Code-level changes

- `services/full_report_section_registry_service.py`
  - `nutrition_report_section` maturity set to Level 5.
  - `nutrition_report_section` provider status set to `opt_in_full_report_integrated`.
  - Added report-specific provider-integrated section metadata helper.

- `services/coordinator_service.py`
  - persisted report metadata now includes `nutrition_report_section` in `provider_integrated_report_sections` only when Nutrition provider output actually rendered and was approved.
  - fallback and disabled-gate Nutrition paths do not imply provider-approved Nutrition content.

## Test coverage

Updated/added tests prove:

- registry lists both Training and Nutrition Report Section as provider-integrated Level 5 sections
- Nutrition Target Display remains separate and Level 2
- approved Nutrition provider output can be reflected as provider-integrated for that report
- fallback Nutrition output is not falsely represented as provider-integrated
- disabled-gate Nutrition output is not falsely represented as provider-integrated
- public/persisted metadata remains sanitized
- existing Nutrition provider, parser, validator, fallback, status, persistence, and API smoke tests continue passing

## Safety review

The patch preserves:

- deterministic fallback
- explicit provider gates
- qwen2.5-only accepted Nutrition provider path
- strict parser/validator boundary
- debug route separation
- public/persisted sanitizer boundary
- Nutrition Target Display separation
- Training behavior

The patch does not:

- make direct_ollama default
- remove fallback
- remove gates
- loosen validators
- run or promote qwen3
- expose raw provider output
- persist rejected candidate/debug/prompt/schema/model-facing data
- add meal planning or new food behavior

## Runtime QA requirement

Runtime QA is required because this patch changes registry/metadata semantics that QA should verify against real full-report opt-in jobs.

Recommended next milestone:

`Nutrition Level 5 Promotion Runtime QA v1`
