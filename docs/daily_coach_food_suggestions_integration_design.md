# DailyCoachSynthesis Food Suggestions Integration Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how approved Nutrition Food Suggestions can later be incorporated into DailyCoachSynthesis so the Coach's Read can reference useful nutrition support options without inventing foods, serving sizes, macros, or recommendations.

## Purpose

The nutrition pipeline now has deterministic, backend-approved food suggestions for supported macro gaps. Those suggestions are already available through the Nutrition tab and are bounded by approved targets, logged actuals, canonical foods, canonical nutrients, practical serving ranges, and public-safe wording.

DailyCoachSynthesis should eventually be able to reference that context at a high level. The goal is not to duplicate the Nutrition tab or turn the Coach's Read into a meal planner. The goal is to add concise context such as:

> The Nutrition tab has approved food suggestions based on today's logged macro gaps.

or:

> Protein is below target based on logged meals, so a protein-focused option may be useful.

The synthesis layer must never create foods, quantities, macro estimates, or meal plans on its own.

## Core principle

AI does not determine nutrition targets.

AI does not determine nutrition actuals.

AI does not invent foods.

AI does not invent serving amounts.

AI does not invent nutrient values.

DailyCoachSynthesis may summarize approved food suggestion context only. It must consume `ApprovedNutritionFoodSuggestions` or an equivalent backend-approved summary. It must not independently compute macro gaps, select foods, estimate nutrients, or produce unapproved nutrition instructions.

## Existing accepted flow

```text
Formula-derived macro targets
→ Nutrition Target Validation
→ Target-vs-Actual
→ Nutrition Food Suggestion Service
→ ApprovedNutritionFoodSuggestions
→ Food Suggestions API/UI
```

The future DailyCoachSynthesis integration should consume this flow after approval:

```text
ApprovedNutritionFoodSuggestions
→ DailyCoachSynthesis context
→ concise Coach's Read wording
```

## Non-goals

This design does not implement:

- code changes
- Streamlit changes
- public response-shape changes
- AI nutrition explanation
- meal plans
- meal templates
- barcode scanning
- Open Food Facts import
- large USDA import
- supplement recommendations
- medical nutrition advice
- Target-vs-Actual behavior changes
- report changes
- workout changes
- CrewAI/Ollama paths
- new food suggestion categories
- automatic dietary rules
- restriction, compensation, or shame-based language

## Integration recommendation

DailyCoachSynthesis should eventually use direct service composition rather than calling the food suggestions HTTP endpoint internally.

Recommended future composition:

```text
build_daily_coach_synthesis(user_id, date)
→ build_target_vs_actual_nutrition_summary(user_id, date)
→ build_approved_nutrition_food_suggestions(user_id, date)
→ synthesize public-safe Coach's Read fields
```

Reasons:

- avoids internal HTTP coupling
- preserves backend ownership of targets, actuals, and suggestions
- keeps the API layer thin
- makes tests deterministic
- avoids leaking endpoint/debug concerns into synthesis logic

## Should DailyCoachSynthesis consume ApprovedNutritionFoodSuggestions?

Yes, but only after the integration service rules are implemented and tested.

DailyCoachSynthesis should consume either:

1. The full `ApprovedNutritionFoodSuggestions` object internally, or
2. A bounded synthesis-facing projection derived from it.

The projection approach is safer for v1 because the Coach's Read does not need the full suggestion list. It only needs high-level facts such as:

- whether suggestions are available
- the primary supported gap
- the number of approved suggestions
- the highest-confidence suggestion category
- whether suggestions are limited due to logging quality
- whether unsupported gaps exist
- public-safe reason codes and limitations

### Recommended internal projection

Potential future internal model:

```text
DailyCoachFoodSuggestionContext
- available: bool
- primary_gap: str | None
- suggestion_count: int
- top_macro_categories: list[str]
- confidence: Limited | Low | Moderate | High
- reason_codes: list[str]
- limitations: list[str]
- summary_hint: str | None
```

This projection should be internal. It does not need to be exposed as a new API field in v1.

## Response-shape recommendation

Avoid changing the public DailyCoachSynthesis response shape for v1 if possible.

Food suggestion context should enrich existing fields first:

- `today_summary`
- `logging_focus`
- `recommended_focus`
- `limitations`
- `reason_codes`

A new field such as `food_suggestion_context` should only be added after Architecture explicitly approves a response-shape change.

## Field-level guidance

### today_summary

May include a concise mention when suggestions are available and confidence is sufficient:

- “The Nutrition tab has approved food suggestions based on today's logged macro gaps.”
- “Protein is below target based on logged meals, and approved food suggestions are available in the Nutrition tab.”

Should avoid listing multiple foods or servings.

### logging_focus

May include suggestion limitations when logging quality affects the suggestion layer:

- “Food suggestions are limited because logging is incomplete.”
- “Complete logging will make nutrition support options more useful.”

Should not imply failure or blame.

### recommended_focus

May point the user to the Nutrition tab when useful:

- “Review the Nutrition tab for approved food options that may help close today's supported macro gap.”
- “Use the Nutrition tab suggestions as optional support, not a required meal plan.”

Should not instruct the user to eat a specific food unless that exact approved suggestion is intentionally allowed by a later design.

### limitations

Should include public-safe limitations when suggestions are blocked or limited:

- “Food suggestions are limited because logging is incomplete.”
- “No supported food suggestion gap is available for this date.”
- “Some macro gaps are not enabled for suggestion support in this version.”

### reason_codes

May include bounded public-safe reason codes, for example:

- `food_suggestions_available`
- `food_suggestions_limited_by_logging`
- `food_suggestions_no_supported_gap`
- `protein_food_suggestions_available`
- `carbohydrate_food_suggestions_available`
- `calorie_support_food_suggestions_available`
- `fat_support_food_suggestions_available`

The synthesis layer should not expose validator internals or raw service/debug codes if they are not public-safe.

## Confidence rules

Food suggestion context should follow the confidence of the approved suggestion object.

### High or Moderate confidence

High/Moderate suggestion confidence may support concise mention in `today_summary` or `recommended_focus`.

Allowed style:

- “Approved food suggestions are available in the Nutrition tab.”
- “A protein-focused option may be useful based on today's logged gap.”

### Low confidence

Low confidence should produce contextual or limitation language only.

Allowed style:

- “Food suggestions are available, but logging quality keeps the read cautious.”
- “Food suggestions are limited because logging appears incomplete.”

Avoid strong claims about gap magnitude or certainty.

### Limited confidence

Limited confidence should not produce affirmative food-suggestion coaching beyond limitation/context.

Allowed style:

- “Food suggestions are limited for this date.”
- “More complete logging is needed before food suggestions should be emphasized.”

### No suggestions

No-suggestion states should not become negative or judgmental.

Allowed style:

- “No approved food suggestions are available for this date.”
- “No supported suggestion gap is available right now.”

Forbidden style:

- “You failed to log enough.”
- “You did not need food suggestions.”
- “You should compensate.”

## Macro-priority guidance

Food suggestions should not overwhelm the Coach's Read. Even if multiple macro categories have suggestions, the synthesis should mention only the highest-value context.

Recommended priority:

```text
protein → carbohydrate → calorie_support → fat_support
```

### Protein

Protein suggestions are usually the most actionable and safest to mention when available.

Example:

- “Protein is below target based on logged meals, so a protein-focused option may be useful.”

### Carbohydrate

Carbohydrate suggestions may be mentioned when approved and useful, especially when training support is relevant.

Example:

- “Carbohydrate suggestions are available because logged carbs are below target and calorie context allows comparison.”

Avoid tying one day of carbohydrate logging directly to performance outcomes.

### Calorie support

Calorie-support suggestions should be framed as optional energy support.

Example:

- “Calorie-support options are available in the Nutrition tab if you want a simple way to add energy.”

Avoid “eat more,” “must,” “bulk,” or exact calorie-prescription language.

### Fat support

Fat-support suggestions should be modest and optional.

Example:

- “A small fat-support option is available, but it should stay optional and practical.”

Avoid implying that dietary fat must be forced or that large high-fat servings are required.

## Suggested future wording rules

### Allowed language

- “The Nutrition tab has approved food suggestions based on today's logged macro gaps.”
- “Protein is below target based on logged meals, so a protein-focused option may be useful.”
- “Carbohydrate suggestions are available because logged carbs are below target and calorie context allows comparison.”
- “Food suggestions are limited because logging is incomplete.”
- “No food suggestions are available yet because no approved supported gap is available.”
- “These are optional support options, not required meals.”

### Forbidden language

DailyCoachSynthesis must not include food-suggestion wording that says or implies:

- “you must eat”
- “you failed”
- “you should compensate”
- “burn this off”
- “skip meals”
- shame or restriction language
- medical/disease claims
- supplement claims
- fat-loss guarantees
- exact physiological certainty
- AI-generated foods/macros/servings
- meal plans
- unsupported causality between one meal/day and performance
- judgmental adherence language

## What not to include in the Coach's Read

The Coach's Read should not duplicate the full Nutrition tab.

Avoid listing:

- full suggestion tables
- every suggested food
- exact serving amounts for multiple foods
- full macro estimates for each option
- canonical food IDs
- raw reason-code lists unless already part of public-safe response behavior
- raw Target-vs-Actual payloads
- raw food entries
- debug data

If exact suggestions need to be shown, the user should go to the Nutrition tab.

## Handling common states

### Approved suggestions exist

The synthesis can mention that approved options exist and name the primary macro category.

Example:

- “Approved protein-focused food suggestions are available in the Nutrition tab.”

### Suggestions limited by logging

The synthesis should keep the message cautious.

Example:

- “Food suggestions are limited because logging is incomplete, so use the Nutrition tab as a light reference rather than a precise plan.”

### No supported suggestion gap

The synthesis should avoid making this sound like success or failure.

Example:

- “No supported food suggestion gap is available for this date.”

### Unsupported macro gaps exist

If future service output reports unsupported gaps, the synthesis may say:

- “Some macro gaps exist, but the current suggestion rules do not support a food option for them yet.”

This should be rare once macro expansion is accepted, but it remains useful for edge cases.

### Data-quality-limited scenario

For data-quality-limited users, food suggestions should be mentioned only as limited/contextual support.

Example:

- “Food suggestions are limited until logging is more complete.”

Do not use food suggestions to make strong claims about intake adequacy, fat loss, or performance.

## Future implementation outline

### Step 1: Add internal projection helper

Add a helper that converts `ApprovedNutritionFoodSuggestions` into a bounded synthesis context.

Potential function:

```text
build_daily_coach_food_suggestion_context(approved_suggestions)
```

This helper should be unit-tested separately from the full synthesis service.

### Step 2: Compose food suggestions into DailyCoachSynthesis

Use direct service composition in the synthesis builder.

Do not call `GET /nutrition/{user_id}/food-suggestions` internally.

### Step 3: Enrich existing text fields

Update existing synthesis wording only where confidence and reason codes allow.

Avoid new public response fields unless explicitly approved.

### Step 4: Add validation rules

Add tests and/or validation for forbidden language in synthesis output.

### Step 5: QA with seeded and real users

QA should validate:

- protein-gap day
- carbohydrate-gap day
- calorie-support day
- fat-support day
- no-suggestion day
- incomplete-logging day
- data-quality-limited user

## Test strategy for future implementation

Required tests before implementation acceptance:

1. DailyCoachSynthesis remains stable when no food suggestions exist.
2. Protein suggestions produce concise Nutrition tab reference only.
3. Carbohydrate suggestions can be referenced without listing full food tables.
4. Calorie-support suggestions are framed as optional energy support.
5. Fat-support suggestions are modest and optional.
6. Low/Limited confidence produces limitation/context only.
7. Incomplete logging produces cautious language.
8. No-suggestion state is not judgmental.
9. Food suggestion context does not change CoachingDecision scenario.
10. Food suggestion context does not change Target-vs-Actual output.
11. Food suggestion context does not alter canonical logging behavior.
12. No raw food rows, raw source payloads, debug payloads, or internal IDs are included in normal synthesis text.
13. No forbidden language appears.
14. Existing DailyCoachSynthesis response shape remains stable if no response-shape change is approved.
15. Full pytest passes.

## Recommended next milestone

If this design is accepted, recommended next milestone:

```text
DailyCoachSynthesis Food Suggestions Context v1
```

Suggested scope:

- add an internal synthesis food-suggestion context/projection helper
- compose approved food suggestions into DailyCoachSynthesis internally
- enrich existing synthesis fields only
- preserve public response shape
- no Streamlit changes
- no AI/CrewAI changes
- no meal plans
- no Target-vs-Actual behavior changes
