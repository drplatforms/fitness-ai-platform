# Nutrition Explanation Value-Aware Copy Contract v1

## Summary

This milestone extends the approved nutrition explanation context with backend-owned, display-safe value-aware fields so AI-generated nutrition copy can be more specific while preserving deterministic source-of-truth boundaries.

The backend remains responsible for:
- nutrition targets
- logged actuals
- calculated gaps
- statuses
- display permissions
- approved food suggestions
- confidence
- validation
- fallback behavior

The provider may use approved values only when they are present in the value-aware context.

## Provider Rules

The provider may:
- quote backend-approved targets or ranges
- quote backend-approved logged actuals
- quote backend-calculated gaps or statuses
- reference approved food suggestion candidates
- create clearer explanation language
- provide brief meal/snack framing based only on approved suggestions

The provider must not:
- invent targets
- invent actuals
- calculate macro gaps
- mutate targets
- mention foods outside approved suggestions
- expose provider internals
- make medical claims
- output markdown
- output wrapper objects
- output extra keys

## Safety Boundary

Output must still parse into the exact CandidateNutritionExplanation contract and pass validation.

Invalid provider output falls back deterministically.

Normal preview output remains public-safe.

Runtime metadata remains debug-only.

## Non-Goals

- no parser relaxation
- no messy JSON extraction
- no target mutation
- no AI-calculated macro gaps
- no meal planning engine
- no report changes
- no workout changes
- no Streamlit provider controls
- no normal endpoint metadata exposure
