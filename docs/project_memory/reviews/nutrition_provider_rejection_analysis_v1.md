# Nutrition Provider Rejection Analysis v1

Status: Implemented / local validation complete / pending Architecture review

Branch: `feature/training-evidence-claim-service`

Latest input snapshot: `6a0b0e2 Add nutrition full report opt-in integration`

## Purpose

Analyze the Nutrition provider rejection observed during Nutrition Full Report Opt-In Runtime QA v1 and identify the smallest safe improvement that can improve future provider approval quality without weakening validators or expanding unsupported claims.

## Runtime QA input reviewed

Architecture accepted Nutrition Full Report Opt-In Runtime QA v1 as `PASS_WITH_SAFE_FALLBACK`.

The accepted opt-in full-report case showed:

- provider selected: `direct_ollama`
- selected model: `qwen2.5:3b`
- parse status: `success`
- candidate valid: `false`
- validation status: `rejected`
- validation errors count: `1`
- fallback used: `true`
- fallback reason: `nutrition_provider_validation_failed`
- fallback source: `nutrition_provider_contract_fallback`
- final Nutrition section source: `deterministic_nutrition_report_section_fallback`
- public/persisted leakage checks: clean

## Debug evidence limitation

The uploaded QA handoff did not include the rejected raw candidate text or raw validation error list. That is correct for public/persisted safety, but it means this review cannot honestly claim the exact runtime rejection string.

The analysis therefore uses:

1. the accepted safe runtime metadata,
2. current parser/validator implementation,
3. current provider-safe context shape,
4. current prompt contract, and
5. fake-candidate reproduction of the most likely rejection class.

No raw provider output is persisted or exposed by this milestone.

## Current validator facts

The Nutrition provider validator currently rejects:

- unsupported nutrition language,
- confidence above backend confidence ceiling,
- field-level claims that lack approved claim types,
- numeric values not explicitly approved by backend evidence,
- unapproved food names,
- unapproved serving-size values.

The runtime failure parsed successfully and produced exactly one validation error. Because parse passed, the issue was not malformed JSON, missing keys, extra keys, wrapper object, or invalid confidence enum.

## Most plausible rejection category

The most likely category is:

`numeric_value_not_approved_by_evidence`

Specifically, qwen2.5 may infer a numeric gap such as “40 g short” from approved values like:

- actual protein: `80 g`
- target minimum: `120 g`

The inferred value `40 g` is mathematically derivable, but it is not explicitly approved in the provider-safe numeric allowlist. The validator is correct to reject it until the backend explicitly approves that derived gap value.

This is a provider approval quality issue, not a validator bug.

## Why the validator should remain strict

The strict validator protects against a model doing its own arithmetic or inventing numbers. This is especially important for nutrition, where seemingly small numeric claims can become unapproved target, gap, deficit, or serving-size advice.

The fix should not allow inferred values. The safer fix is to make the provider context/prompt clearer:

- show the exact numeric values the model may repeat,
- explicitly forbid inferred/calculated gaps and deltas,
- instruct the model to describe relationships qualitatively when a useful numeric value is not explicitly allowed.

## Code-level improvement made

This milestone adds an explicit provider-safe numeric allowlist:

`approved_numeric_values`

The provider-safe context now lists exact backend-approved numbers that a candidate may repeat. It intentionally excludes derived gap/delta/percentage values unless the backend explicitly adds them later.

The direct-Ollama Nutrition prompt now instructs the model to:

- use only numbers listed in `approved_numeric_values`,
- not calculate or infer gaps, deltas, percentages, serving sizes, or targets,
- describe relationships qualitatively when a useful number is not listed.

## Tests added

New fake-candidate tests prove:

- provider-safe context includes exact approved numbers,
- inferred numeric gap values such as `40 g` are not allowlisted,
- validator rejects candidate text that includes an inferred `40 g` protein gap,
- direct-Ollama prompt includes the approved numeric-value instruction.

## Boundaries preserved

- No validator loosening.
- No unsupported claim approval.
- No raw provider output persistence.
- No public rejected candidate exposure.
- No Nutrition Level 5 promotion.
- No qwen3 testing.
- No users 101-105 runtime sweep.
- No nutrition target formula changes.
- No new foods.
- No meal planning.
- No serving-size expansion.
- No RAG, embeddings, or agent orchestration.
- No Training provider behavior changes.
- No Streamlit/UI changes.

## Final readiness status

`READY_FOR_RETRY_RUNTIME_QA`

The next QA should rerun the same minimum full-report opt-in Nutrition runtime case for user 102/date 2026-06-14 with qwen2.5:3b. The expected improvement is that qwen2.5 avoids inferred numeric gap language and either passes validation or continues to fall back safely.

Passing runtime retry QA should still not imply Level 5 promotion. Level 5 requires a separate Architecture decision after broader runtime QA, persisted-history inspection, exact-key leakage checks, and composition fallback confirmation.
