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

Candidate fields may include:

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
- bounded reason/limitation context

The provider may quote these values only when they are present in `value_aware_context`.

## Allowed Copy

The provider may use `food_suggestion_context` to write concise copy such as:

- approved food options in the Nutrition tab may help with the current supported gap
- a listed approved food can be used as a practical option
- an approved serving amount or macro contribution may be quoted only when present in the approved candidate payload
- no food suggestions are available or suggestions are limited when no approved candidates exist

Suggestions must be framed as practical options, not rigid prescriptions.

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
- unapproved nutrition numbers

Invalid provider output falls back deterministically.

## Public/Debug Behavior

Normal preview remains public-safe and does not expose runtime metadata.

Debug endpoints may expose runtime metadata, parse status, validation status, fallback reason, and bounded raw output diagnostics.

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
