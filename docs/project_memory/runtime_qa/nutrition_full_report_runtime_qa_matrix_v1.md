# Nutrition Full Report Runtime QA Matrix v1

Status: Accepted by Architecture

QA result: `PASS_MATRIX_WITH_SAFE_FALLBACKS`

Date/commit if known: Unknown / verify with git log and QA artifacts.

## Scope

Full-report opt-in Nutrition provider runtime matrix across seeded users 101-105.

- Provider: `direct_ollama`
- Model: `qwen2.5:3b`
- qwen3: not used
- Nutrition maturity: Level 4
- Level 5 promotion: not approved

## Summary

- provider_approved_count: 1
- safe_fallback_count: 4
- fail_count: 0
- overall_decision: `PASS_MATRIX_WITH_SAFE_FALLBACKS`

## Per-user result

| User | Result | Summary |
|---|---|---|
| 101 | PASS_WITH_SAFE_FALLBACK | provider attempted, parsed, validator rejected, deterministic fallback used safely |
| 102 | PASS_PROVIDER_APPROVED | provider attempted, parsed, validator approved, direct_ollama_approved rendered |
| 103 | PASS_WITH_SAFE_FALLBACK | provider attempted, parsed, validator rejected, deterministic fallback used safely |
| 104 | PASS_WITH_SAFE_FALLBACK | provider attempted, parsed, validator rejected, deterministic fallback used safely |
| 105 | PASS_WITH_SAFE_FALLBACK | provider attempted, parsed, validator rejected, deterministic fallback used safely |

## Scanner triage

Initial matrix failures were accepted as scanner false positives:

1. Persisted-history scan looked across all persisted history rows instead of only the current matrix job.
2. Unsupported numeric scanner was too broad and flagged generic phrases such as `serving size`.

Corrected triage:

- current-job forbidden exact keys: clean
- narrow unsupported derived numeric checks: clean for users 101-105
- qwen3_used: false
- provider_integrated_report_sections: training
- Nutrition remained Level 4

## Safety result

Accepted clean:

- raw provider output leakage
- rejected candidate text leakage
- prompt/schema leakage
- raw validation error list leakage
- traceback/exception leakage
- provider payload leakage
- model-facing context leakage
- parser/debug leakage
- raw CrewAI error text leakage
- qwen3 runtime artifacts
- angle bracket artifacts
- forbidden seed/test terms

Allowed safe summary metadata observed:

- `coordinator_fallback_reason=crewai_coordinator_error`
- `full_report_composer_source=deterministic_fallback_after_crewai_error`
- `nutrition_validation_errors_count`
- `nutrition_fallback_reason`
- `nutrition_fallback_source`

## Boundary result

- Nutrition full-report opt-in provider path executed for users 101-105.
- Deterministic fallback preserved report completion and persistence where validation rejected provider candidates.
- Nutrition Report Section rendered separately from Nutrition Target Display.
- `provider_integrated_report_sections` remained `training`.
- Training behavior remained deterministic because Training provider gates were unset.
- Nutrition remained Level 4.
- Nutrition was not marked Level 5.

## Follow-up

Architecture approved `Nutrition Provider Matrix Rejection Analysis v1` to inspect rejected users and improve approval quality without weakening validators.
