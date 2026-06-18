# Nutrition Provider Matrix Rejection Analysis v1

Status: Implemented / local validation complete / pending Architecture review

Branch: `feature/training-evidence-claim-service`

## Context

Nutrition Full Report Runtime QA Matrix v1 was accepted as `PASS_MATRIX_WITH_SAFE_FALLBACKS`.

The matrix proved that Nutrition's Level 4 full-report opt-in provider path is runtime-safe across seeded users 101-105:

- user 102: provider approved
- users 101, 103, 104, 105: provider parsed but validator rejected, deterministic fallback used safely
- failures: none
- qwen3 used: false
- Nutrition maturity: Level 4
- Level 5 promotion: not approved

## Evidence limitation

The Architecture handoff provides accepted per-user outcomes and safety metadata, but it does not include raw provider candidates or raw validation error lists for users 101, 103, 104, and 105.

This review does not claim the exact raw runtime rejection strings.

The implemented change targets the smallest safe validator/prompt ambiguity found by inspecting the current contract and reproducing a likely safe-fallback pattern with fake candidate output.

## Rejection analysis

A likely repeated rejection pattern is safe negative food-suggestion language.

Before this milestone, the validator treated any `practical_food_focus` text containing words such as `suggestion`, `serving`, `grams`, or `g` as food-suggestion language requiring an approved `food_suggestion_available` claim.

That behavior correctly rejected invented foods and serving-size claims.

However, it could also reject safe limitation language such as:

`No approved food suggestion is available from the current evidence.`

For matrix users with incomplete evidence or no approved food suggestion, qwen2.5 may naturally say that no approved suggestion is available. That statement is safe and should not require a positive `food_suggestion_available` claim as long as it does not recommend a food, serving, grams, substitution, or action.

## Smallest safe fix

The validator now explicitly allows negative/unavailable food suggestion language when it only states that no approved suggestion is available.

It still rejects invented or action-oriented food suggestion language when no approved food suggestion claim exists.

Prompt guidance now tells the model:

- if `approved_food_suggestions` is empty, say that no approved food suggestion is available
- do not suggest foods, servings, grams, or substitutions

## What changed

- Added a validator helper for safe unavailable food-suggestion language.
- Removed duplicated food-suggestion phrase gating from generic field-level claim checks.
- Kept positive/action-oriented food suggestion validation in the dedicated food-suggestion validator.
- Updated Nutrition direct-Ollama prompt with explicit no-suggestion guidance.
- Added fake-candidate tests for the safe no-suggestion pattern.
- Added fake-candidate tests proving invented food suggestions still reject.

## Rejection categories addressed

Likely addressed:

- provider verbosity around unavailable food suggestions
- field-level claim mismatch around negative food suggestion language
- prompt ambiguity when approved food suggestions are empty

Not addressed:

- unsupported numeric inference
- target unavailable claims
- confidence ceiling issues
- unsupported serving-size recommendations
- medical/supplement/guarantee/shame language
- unsupported food names
- qwen3 behavior

## Safety boundary

This milestone does not loosen validator truth boundaries.

Allowed now:

- `No approved food suggestion is available from the current evidence.`

Still rejected:

- `A Greek yogurt suggestion can help close the protein gap.` when no approved suggestion exists
- invented food names
- invented serving sizes
- unapproved grams/calories/protein values
- meal planning
- supplement, medical, shame, or guaranteed-outcome language

## Validation

Focused tests passed locally/sandbox:

- `pytest tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_report_section_direct_ollama_provider.py -q`
- `pytest tests/test_nutrition_report_section_provider_service.py tests/test_nutrition_report_section_direct_ollama_provider.py tests/test_nutrition_provider_contract_validation.py tests/test_nutrition_provider_contract_parser.py tests/test_nutrition_full_report_opt_in_integration.py tests/test_report_persistence_boundary.py -q`
- broader focused safety suite passed

## Runtime QA recommendation

Next recommended milestone:

`Nutrition Provider Matrix Retry Runtime QA v1`

Recommended scope:

- rerun users 101-105 full-report opt-in Nutrition matrix with qwen2.5:3b
- verify whether safe-fallback users improve approval rate
- verify all safe fallback behavior still works
- verify raw/debug/provider leakage remains clean
- verify Nutrition remains Level 4
- do not run qwen3
- do not approve Level 5

## Final status

`READY_FOR_MATRIX_RETRY_QA`
