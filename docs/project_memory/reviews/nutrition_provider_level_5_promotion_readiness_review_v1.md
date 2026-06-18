# Nutrition Provider Level 5 Promotion Readiness Review v1

Status: READY_FOR_NUTRITION_LEVEL_5_PROMOTION_PATCH

Date: 2026-06-18

## Decision

Nutrition Provider Level 5 Promotion Readiness Review v1 is accepted as a readiness review.

Nutrition is ready for a separate, explicit Nutrition Provider Level 5 Promotion v1 patch.

This review does not itself promote Nutrition to Level 5, does not make `direct_ollama` the default provider, does not remove deterministic fallback, and does not remove any provider gates.

## Current recommendation

Proceed to:

`Nutrition Provider Level 5 Promotion v1`

The promotion patch should be narrow and should update status/registry semantics only after preserving the existing safety gates and fallback behavior.

## Runtime evidence reviewed

### Nutrition Provider Retry Runtime QA v1

Accepted as a safety pass. Provider execution was protected by deterministic fallback when validation rejected candidates.

### Nutrition Full Report Runtime QA Matrix v1

Accepted as `PASS_MATRIX_WITH_SAFE_FALLBACKS`.

- provider-approved users: 1
- safe-fallback users: 4
- failures: 0
- qwen3 used: false
- Nutrition remained Level 4

### Nutrition Provider Matrix Retry Runtime QA v1

Accepted as a safety pass but not as a quality improvement.

- provider-approved users: 0
- safe-fallback users: 5
- failures: 0
- diagnostics were still too coarse before the diagnostic propagation fix

### Nutrition Provider Diagnostic Matrix QA Retry v1

Accepted as `PASS_DIAGNOSTICS_WITH_SAFE_FALLBACKS`.

- diagnostic capture success count: 5
- diagnostic capture missing count: 0
- public/persisted leakage: none
- repeated failure field identified: `practical_food_focus`

### Nutrition Provider Practical Food Focus Runtime QA v1

Accepted as `PASS_WITH_IMPROVED_DIAGNOSTICS`.

- provider-approved users: 1
- safe-fallback users: 4
- practical_food_focus failures reduced from 5 to 4
- user 105 no-approved-food-suggestion path was provider-approved

### Nutrition Provider Approved Suggestion Runtime QA v1

Accepted as `PASS_PROVIDER_APPROVED_MATRIX`.

- provider-approved users: 5
- safe-fallback users: 0
- failures: 0
- practical_food_focus failures: 0
- qwen3 used: false
- provider_integrated_report_sections remained `training`
- Nutrition remained Level 4 pending promotion review

## Final QA evidence summary

The final accepted seeded matrix result is the strongest Nutrition provider result so far:

- users 101-105 all provider-approved
- parser success for all users
- validation approved for all users
- fallback used for zero users
- section source: `direct_ollama_approved`
- practical_food_focus failure count: 0
- no raw/debug/provider leakage
- no unsupported numeric claims
- no invented/action-oriented food suggestions without approved evidence
- no unsafe serving/gram claims
- qwen3 was not used

## Safety evidence reviewed

Accepted safety evidence includes:

- public report text did not expose raw provider output
- persisted history did not expose raw provider output
- persisted history did not expose diagnostic category/field lists
- persisted history did not expose approved option context
- normal `/reports/status/{job_id}` did not expose debug diagnostics
- provider `safe_metadata` did not expose diagnostic category/field lists
- provider `safe_metadata` did not expose approved option context
- rejected candidate text did not leak
- raw validation errors did not leak
- prompt/schema did not leak
- traceback/exception text did not leak
- provider payload did not leak
- model-facing context did not leak
- parser/debug internals did not leak
- raw CrewAI error text did not leak

## Provider approval quality reviewed

Provider quality improved across the Nutrition tuning sequence:

| QA pass | Provider approved | Safe fallback | Repeated failure pattern |
|---|---:|---:|---|
| Initial full-report matrix | 1 | 4 | practical_food_focus and other rejection ambiguity |
| Matrix retry | 0 | 5 | diagnostics too coarse |
| Diagnostic matrix retry | 0 | 5 | practical_food_focus identified clearly |
| Practical food focus runtime QA | 1 | 4 | no-suggestion path fixed; approved-suggestion path still failing |
| Approved suggestion runtime QA | 5 | 0 | practical_food_focus failure resolved |

The final matrix proves qwen2.5:3b can produce provider-approved Nutrition sections across seeded users 101-105 when the backend supplies approved practical_food_focus options and the validator remains strict.

## Section maturity reviewed

### Nutrition Target Display

Remains distinct from the Nutrition Report Section.

Status: Level 2.

It is a backend-approved target display contract and should not be merged with provider-owned Nutrition voice.

### Nutrition Report Section

Current status before promotion patch: Level 4.

Evidence supporting promotion readiness:

- backend-owned evidence context exists
- provider-safe context exists
- strict parser exists
- strict validator exists
- deterministic fallback exists
- full-report integration gate exists
- provider execution gate exists
- debug/QA diagnostics exist and are separated from public surfaces
- persisted metadata is sanitized by exact-key allowlist
- seeded full-report runtime matrix is provider-approved for users 101-105

### Training

Training remains Level 5 and remains the only provider-integrated full-report section until a separate Nutrition promotion patch is accepted.

## Proposed Level 5 definition for Nutrition

Nutrition Level 5 should mean:

1. Nutrition has a full-report integrated provider path.
2. Provider output is always parsed and validated by backend before rendering.
3. Deterministic fallback remains available on parser, validation, provider, timeout, exception, missing evidence, or composition failure.
4. Provider execution remains explicitly gated unless Architecture separately approves a default behavior change.
5. Public report text contains only approved section output or deterministic fallback output.
6. Persisted report history contains only public-safe report text and exact-key safe metadata.
7. Debug/QA diagnostics remain separated from normal public/status/persisted surfaces.
8. Metadata accurately records selected provider, section source, validation status, fallback status, and section maturity.
9. Runtime QA has shown provider approval consistency across seeded users 101-105 with qwen2.5:3b.
10. No raw provider output, prompt/schema, rejected candidate text, raw validation errors, model-facing context, parser internals, or debug objects leak publicly or into persisted history.

## Recommended Nutrition Provider Level 5 Promotion v1 patch scope

The promotion patch should be narrow.

Recommended changes:

1. Update section registry/project memory to mark `nutrition_report_section` as Level 5 provider-ready after accepted runtime QA.
2. Update provider-integrated section semantics so Nutrition can be counted as provider-integrated only when provider output is approved and rendered from `direct_ollama_approved`.
3. Preserve the distinction between:
   - provider-capable / Level 5 section maturity
   - provider actually attempted in a specific report
   - provider-approved section in a specific report
4. Preserve deterministic fallback semantics.
5. Preserve opt-in gates unless Architecture explicitly approves a later default-provider change.
6. Preserve `nutrition_target_display` as a separate Level 2 display contract.
7. Add/adjust tests for registry/metadata semantics if code-level registry behavior changes.
8. Update project memory docs and runtime QA notes.

## Promotion patch non-goals

Do not:

- make `direct_ollama` default
- remove deterministic fallback
- remove provider gates
- loosen validators
- run or promote qwen3
- expose raw provider output
- expose debug diagnostics publicly
- persist raw validation errors
- merge Nutrition Target Display and Nutrition Report Section
- add meal planning
- add new foods
- add serving-size expansion
- add RAG
- add embeddings
- add agent orchestration
- change Training behavior
- change Streamlit/UI

## Known risks before promotion patch

1. Promotion semantics could accidentally imply Nutrition provider is default when it is still opt-in.
2. `provider_integrated_report_sections` semantics need care: Training is always the established provider-integrated section, while Nutrition should only be listed as provider-integrated when its approved provider section is actually used or when Architecture explicitly redefines the field.
3. qwen2.5:3b is the only approved Nutrition provider runtime model; qwen3 remains unapproved.
4. Seeded matrix success does not equal broad production nutrition coverage.
5. The old CrewAI coordinator remains separate and should not be confused with the Nutrition direct-Ollama provider path.

## Final decision

Final status:

`READY_FOR_NUTRITION_LEVEL_5_PROMOTION_PATCH`

Nutrition should remain Level 4 until the separate promotion patch is implemented, reviewed, validated, and accepted.
