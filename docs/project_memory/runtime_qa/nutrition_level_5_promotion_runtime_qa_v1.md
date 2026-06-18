# Nutrition Level 5 Promotion Runtime QA v1

Status: ACCEPTED

Final milestone status: `NUTRITION_REPORT_SECTION_LEVEL_5_RUNTIME_VALIDATED`

## Summary

Nutrition Level 5 Promotion Runtime QA v1 passed. Architecture accepts Nutrition Report Section as a Level 5 provider-integrated full-report section under explicit opt-in provider gates.

This validation covers direct_ollama/qwen2.5:3b across seeded users 101-105. It does not approve direct_ollama as default, qwen3, removing deterministic fallback, removing provider gates, or merging Nutrition Target Display with Nutrition Report Section.

## Accepted runtime result

Provider-approved users:

- User 101: PASS_PROVIDER_APPROVED_LEVEL_5
- User 102: PASS_PROVIDER_APPROVED_LEVEL_5
- User 103: PASS_PROVIDER_APPROVED_LEVEL_5
- User 104: PASS_PROVIDER_APPROVED_LEVEL_5
- User 105: PASS_PROVIDER_APPROVED_LEVEL_5

Provider-approved matrix summary:

- provider_approved_count: 5
- safe_fallback_count: 0
- fail_count: 0
- provider_integrated_sections_correct_count: 6
- provider_integrated_sections_incorrect_count: 0

Approved provider output correctly included:

- provider_integrated_report_sections: training,nutrition_report_section
- nutrition_section_source: direct_ollama_approved
- nutrition_report_section_level: Level 5

## Disabled-gate result

Disabled-gate user:

- User 101: PASS_DISABLED_GATE_SEMANTICS
- nutrition_provider_attempted: false
- nutrition_selected_provider: deterministic
- nutrition_selected_model: deterministic
- nutrition_section_source: deterministic
- provider_integrated_report_sections: training
- nutrition_report_section_level: Level 5
- nutrition_report_section_provider_status: opt_in_full_report_integrated
- nutrition_target_display_level: Level 2
- nutrition_target_display_provider_status: none

Architecture accepts this result. Disabled-gate Nutrition output did not falsely include nutrition_report_section in provider_integrated_report_sections.

## Fallback semantics note

Fallback runtime semantics were not tested.

Reason: no safe QA-only forced-invalid provider mode was used.

Architecture accepts this as an honest coverage note. This should not be represented as completed runtime fallback coverage.

Future optional milestone:

`Nutrition Provider Forced-Fallback Runtime QA Harness v1`

Purpose: provide a safe QA-only forced-invalid provider mode to validate fallback metadata semantics at runtime without relying on live model failure. This is optional and not a blocker for accepting the current Level 5 promotion runtime QA.

## Safety and leakage result

Safety checks passed:

- normal /reports/status/{job_id} did not expose debug diagnostics or approved option context
- persisted history did not expose diagnostic category/field lists or approved option context
- provider safe_metadata did not expose diagnostic category/field lists or approved option context
- no raw provider output leaked
- no rejected candidate text leaked
- no raw validation errors leaked
- no prompt/schema leaked
- no traceback/exception text leaked
- no provider payload leaked
- no model-facing context leaked
- no parser/debug internals leaked
- no unsupported derived numeric claims appeared
- no invented/action-oriented food suggestions without approved evidence appeared
- no unsafe serving/gram food claims appeared
- qwen3 was not used

## Final section maturity state

Training:

- Level 5 provider-integrated section

Nutrition Report Section:

- Level 5 provider-integrated full-report section
- provider_status: opt_in_full_report_integrated
- provider-integrated only when provider output is approved

Nutrition Target Display:

- Level 2 display contract
- provider_status: none
- remains separate from Nutrition Report Section

## Final boundaries

Still not approved:

- direct_ollama as default
- qwen3
- removing deterministic fallback
- removing provider gates
- loosening validators
- exposing raw provider output publicly
- exposing debug diagnostics publicly
- persisting raw validation errors
- persisting rejected candidate text
- persisting prompt/schema/model-facing context
- merging Nutrition Target Display and Nutrition Report Section
- meal planning
- new foods
- serving-size expansion
- RAG
- embeddings
- agent orchestration
- Training behavior changes
- Streamlit/UI changes

## Final Architecture position

Nutrition Level 5 Promotion Runtime QA v1 is accepted. Nutrition Report Section is now Level 5 runtime validated under explicit opt-in provider gates.

This is a major backend/provider milestone.
