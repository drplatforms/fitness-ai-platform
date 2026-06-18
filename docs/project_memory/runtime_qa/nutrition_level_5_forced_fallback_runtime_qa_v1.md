# Nutrition Level 5 Forced-Fallback Runtime QA v1

Status: ACCEPTED

QA result: PASS_FORCED_FALLBACK_RUNTIME_QA

Final status: NUTRITION_LEVEL_5_RUNTIME_SEMANTICS_COMPLETE

## Summary

Nutrition Level 5 Forced-Fallback Runtime QA v1 closed the last documented runtime coverage gap for Nutrition Level 5 semantics.

The accepted QA result proves that Nutrition Level 5 metadata now correctly distinguishes:

1. provider-approved Nutrition output
2. disabled-gate deterministic Nutrition output
3. forced-invalid deterministic fallback Nutrition output

Fallback and disabled-gate outputs do not falsely claim Nutrition provider integration.

## Forced-fallback result

Forced-invalid users:

- User 101: PASS_FORCED_FALLBACK
- User 102: PASS_FORCED_FALLBACK
- User 103: PASS_FORCED_FALLBACK
- User 104: PASS_FORCED_FALLBACK
- User 105: PASS_FORCED_FALLBACK

For every forced-invalid user:

- nutrition_fallback_used: true
- nutrition_fallback_reason: qa_forced_invalid_provider_output
- nutrition_section_source: deterministic_nutrition_report_section_fallback
- provider_integrated_report_sections: training
- provider_integrated_correct: true
- live_model_called: false
- leakage_found: false
- qwen3_used: false

## Control result

Control user:

- User 102: PASS_CONTROL_PROVIDER_APPROVED
- forced-invalid mode: disabled
- nutrition_fallback_used: false
- nutrition_fallback_reason: null
- nutrition_section_source: direct_ollama_approved
- provider_integrated_report_sections: training,nutrition_report_section
- provider_integrated_correct: true
- leakage_found: false
- qwen3_used: false

The QA-only mode did not contaminate normal provider behavior.

## Sanitization result

All sanitizer checks passed.

No leakage was found in:

- normal public report text
- normal /reports/status/{job_id}
- persisted report history
- provider safe_metadata

Confirmed absent from public, normal-status, persisted, and provider-safe metadata surfaces:

- raw provider output
- forced invalid candidate text
- rejected candidate text
- prompt/schema
- raw validation errors
- validation internals
- traceback/exception internals
- provider payload
- model-facing context
- parser internals
- debug objects
- diagnostic category/field lists
- approved option context

Debug-only diagnostics remain confined to explicit debug endpoint behavior.

## Final coverage state

Provider-approved path: PASS

Evidence:

- users 101-105 provider-approved in prior Level 5 runtime QA
- provider_integrated_report_sections included training,nutrition_report_section
- Nutrition Report Section treated as Level 5 provider-integrated

Disabled-gate path: PASS

Evidence:

- provider not attempted
- deterministic Nutrition behavior preserved
- provider_integrated_report_sections remained training

Forced-fallback path: PASS

Evidence:

- forced-invalid candidate generated only under explicit QA flag
- live model not called
- parse succeeded
- validation rejected candidate
- deterministic fallback rendered
- provider_integrated_report_sections remained training
- Nutrition was not falsely marked provider-integrated during fallback

## Boundaries preserved

- direct_ollama remains opt-in only
- direct_ollama is not default
- qwen3 remains not approved
- forced-invalid provider mode remains QA-only
- forced-invalid provider mode remains disabled by default
- provider gates remain mandatory
- deterministic fallback remains mandatory
- validators remain strict
- Training behavior unchanged
- Streamlit/UI unchanged
- public README/portfolio positioning unchanged unless later updated to remove the old limitation
- Nutrition Target Display remains separate Level 2 display contract
- Nutrition Report Section remains Level 5 provider-integrated only when provider-approved

## Public claims note

Allowed conservative wording:

- Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode.

Do not imply:

- forced-invalid mode is available to normal users
- forced-invalid mode is production behavior
- direct_ollama is default
- qwen3 is approved

## Recommended next milestone options

Choose separately after closeout and merge:

- Demo / Deployment Packaging Design v1
- Nutrition Explanation Value-Aware Copy v1
- UI polish / screenshot capture pass
- GitHub README / portfolio update pass
