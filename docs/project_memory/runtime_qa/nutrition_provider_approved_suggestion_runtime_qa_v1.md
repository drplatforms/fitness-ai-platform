# Nutrition Provider Approved Suggestion Runtime QA v1

Status: ACCEPTED

QA result: PASS_PROVIDER_APPROVED_MATRIX

## Summary

Nutrition Provider Approved Suggestion Runtime QA v1 is the strongest Nutrition provider runtime result so far.

Runtime matrix result:

- provider_approved_count: 5
- safe_fallback_count: 0
- fail_count: 0
- practical_food_focus_failure_count: 0
- prior_practical_food_focus_failure_count: 4
- qwen3_used: false
- provider_integrated_report_sections: training
- nutrition_level: Level 4

This is accepted as a provider approval-quality pass for the seeded Nutrition matrix.

It does not automatically approve Level 5 promotion.

## Accepted per-user result

All seeded users passed provider approval.

User 101:

- candidate_valid: true
- validation_status: approved
- fallback_used: false
- section_source: direct_ollama_approved

User 102:

- candidate_valid: true
- validation_status: approved
- fallback_used: false
- section_source: direct_ollama_approved

User 103:

- candidate_valid: true
- validation_status: approved
- fallback_used: false
- section_source: direct_ollama_approved

User 104:

- candidate_valid: true
- validation_status: approved
- fallback_used: false
- section_source: direct_ollama_approved

User 105:

- candidate_valid: true
- validation_status: approved
- fallback_used: false
- section_source: direct_ollama_approved

## Safety result

Safety checks passed:

- normal `/reports/status/{job_id}` did not expose debug diagnostics or approved option context
- persisted history did not expose diagnostic category/field lists or approved option context
- provider `safe_metadata` did not expose diagnostic category/field lists or approved option context
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

## Boundary result

Confirmed:

- Nutrition full-report opt-in provider path executed across seeded users 101-105
- direct_ollama/qwen2.5:3b was used
- qwen3 was not used
- provider_integrated_report_sections remained training
- Nutrition remained Level 4 pending promotion review
- Nutrition Target Display remained distinct from Nutrition Report Section
- Training remained deterministic because Training provider gates were unset

## Architecture interpretation

The backend-approved practical_food_focus option strategy resolved the repeated practical_food_focus failure pattern.

Previous failure pattern:

- users 101-104 failed unsupported_food_suggestion on practical_food_focus
- user 105 had already passed no-approved-food-suggestion behavior

Current result:

- users 101-105 all provider-approved
- practical_food_focus_failure_count: 0

This confirms the Level 4 provider pattern:

backend-approved practical_food_focus options
→ provider copies/selects exact approved sentence
→ strict validator approves
→ public/persisted output remains safe

## Decision

Proceed to Nutrition Provider Level 5 Promotion Readiness Review v1.
