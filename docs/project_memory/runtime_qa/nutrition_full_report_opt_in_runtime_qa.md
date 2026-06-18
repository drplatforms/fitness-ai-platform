# Nutrition Full Report Opt-In Runtime QA v1

Status: Accepted by Architecture

QA result: `PASS_WITH_SAFE_FALLBACK`

Date/commit: Unknown / verify with `git log --oneline -5`

## Scope

Runtime QA exercised Nutrition’s Level 4 opt-in provider path inside full-report generation for user 102/date 2026-06-14.

This QA did not approve Level 5 promotion.

## Accepted cases

### Case 1: Default deterministic full report

Decision: `PASS`

- Nutrition full-report integration disabled.
- Nutrition provider execution disabled/default false.
- Nutrition provider not attempted.
- Nutrition section source deterministic.
- Nutrition Report Section rendered.
- Nutrition Target Display rendered.
- Provider-integrated report sections remained `training`.
- Persisted row found.
- Raw/debug leakage checks were clean.

### Case 2: Section provider enabled, full-report integration disabled

Decision: `PASS`

- Section provider environment was present.
- Full-report integration gate remained disabled.
- Full report did not attempt Nutrition provider.
- Nutrition section source deterministic.
- Provider-integrated report sections remained `training`.
- Persisted row found.
- Raw/debug leakage checks were clean.

Architecture accepted this as proof that the section provider gate alone is not sufficient to make full reports call the Nutrition provider.

### Case 3: Full opt-in Nutrition full-report integration

Decision: `PASS_WITH_SAFE_FALLBACK`

- Nutrition full-report integration enabled.
- Nutrition provider execution enabled.
- Provider attempted.
- Selected provider: `direct_ollama`.
- Selected model: `qwen2.5:3b`.
- Parse status: `success`.
- Candidate valid: `false`.
- Validation status: `rejected`.
- Validation errors count: `1`.
- Fallback used: `true`.
- Fallback reason: `nutrition_provider_validation_failed`.
- Fallback source: `nutrition_provider_contract_fallback`.
- Final Nutrition section source: `deterministic_nutrition_report_section_fallback`.
- Full report completed and persisted safely.
- Raw/debug/provider leakage checks were clean.

## Safety conclusion

The provider rejection was fallback-protected in full-report runtime. Public report text and persisted history did not expose raw provider output, rejected candidate text, prompt/schema, traceback, raw validation error list, model-facing context, parser internals, debug objects, or raw CrewAI error text.

## Maturity conclusion

Nutrition remains Level 4. Training remains the only full-report provider-integrated Level 5 section.

## Next step

Nutrition Provider Rejection Analysis v1.
