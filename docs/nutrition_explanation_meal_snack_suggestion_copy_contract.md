# Nutrition Explanation Meal/Snack Suggestion Copy Contract v1

## Summary

This milestone allows optional nutrition explanation providers to generate brief meal/snack guidance from backend-approved food suggestion candidates while preserving deterministic source-of-truth boundaries.

The existing `food_suggestion_context` field remains the user-facing contract. No new candidate or approved explanation field is required for v1.

## Source of Truth

The backend remains responsible for:

- nutrition targets
- logged actuals
- macro gaps and statuses
- display permissions
- approved food suggestion candidates
- serving amounts
- macro/calorie contribution estimates
- confidence
- logging completeness
- validation
- fallback behavior

The provider may explain only approved context. Provider output remains untrusted until it parses into `CandidateNutritionExplanation` and passes validation.

## Provider Context

The compressed provider context includes `value_aware_context.approved_food_suggestion_candidates` when backend-approved food suggestions are available.

Provider-facing candidate fields may include:

- `display_name`
- `suggested_grams`
- `estimated_calories`
- `estimated_protein_g`
- `estimated_carbohydrate_g`
- `estimated_fat_g`
- `macro_gap_addressed`
- `macro_support_category`
- `suggestion_summary`
- `confidence`

The provider may quote these values only when they are present in `value_aware_context`.

## Required Meal/Snack Copy Behavior

When `approved_food_suggestion_candidates` are present:

- `food_suggestion_context` must mention at least one approved candidate `display_name` exactly.
- `food_suggestion_context` may use `suggested_grams` only when that field is present for the approved candidate.
- Macro/calorie contribution values may be quoted only when present in the approved candidate payload.
- Copy must stay brief and practical.
- Copy must frame suggestions as options, not rigid prescriptions.

When no approved food suggestion candidates are present:

- the provider may say food suggestions are limited or unavailable.
- the provider must not invent an alternative food.

## Rejected Vague Contract Copy

When candidates exist, the validator rejects generic contract-style copy such as:

- “Food suggestions are limited to the approved candidates provided.”
- “Use the approved food suggestions.”
- “Choose from the listed candidates.”
- “Food options are available based on your plan.”

This prevents provider-approved output that technically follows the contract but is not useful to the user.

## Forbidden Copy

The provider must not:

- invent foods
- invent serving sizes
- invent calories/macros/nutrient values
- invent meal plans
- calculate macro gaps
- mutate targets
- recommend foods outside approved candidates
- imply the user failed
- use shame, restriction, or compensation language
- make medical, disease, supplement, or fat-loss guarantee claims
- mention raw data, SQL, providers, debug payloads, or validation internals

## Validation

The validator continues to reject:

- forbidden nutrition explanation language
- target mutation or calibration-applied claims
- meal-plan language
- shame/restriction language
- medical/supplement/fat-loss claims
- raw/internal/provider/debug language
- unapproved food mentions where detectable from current approved candidate structure
- unapproved serving-size mentions in `food_suggestion_context`
- unapproved nutrition numbers
- missing approved food candidate names when candidates exist
- vague contract-style food suggestion copy when candidates exist

Invalid provider output falls back deterministically.

## Public/Debug Behavior

Normal preview remains public-safe and does not expose runtime metadata or debug candidate context.

The debug endpoint may expose a sanitized candidate projection for QA:

```json
{
  "approved_food_suggestion_candidates": [
    {
      "display_name": "Chicken Breast, Cooked, Skinless",
      "suggested_grams": 150,
      "macro_gap_addressed": "protein_g",
      "suggestion_summary": "150 g chicken breast can support the protein gap."
    }
  ]
}
```

The debug projection must not expose:

- raw source payloads
- raw nutrient rows
- unbounded metadata
- provider internals
- raw model output

## Non-Goals

- no meal-planning engine
- no multi-day meal plans
- no recipe generation
- no grocery lists
- no target mutation
- no AI-calculated nutrition values
- no parser relaxation
- no messy JSON extraction
- no markdown/code-fence acceptance
- no Streamlit provider controls
- no report changes
- no workout changes
- no DailyCoachSynthesis changes
