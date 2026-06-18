# Nutrition Food Suggestion Macro Expansion Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how deterministic nutrition food suggestions can expand beyond protein-first suggestions into carbohydrate, calorie-support, and fat-support suggestions while preserving canonical-food-only behavior, public safety, and practical serving bounds.

## Purpose

The current Nutrition Food Suggestion flow is intentionally protein-first. That was the right v1 boundary because protein targets can often be approved when calorie, carbohydrate, and fat targets are blocked or limited.

The next architecture question is how to expand suggestion coverage without turning the feature into meal planning, dieting advice, AI-generated food matching, or unrestricted macro prescription.

This design answers:

- when non-protein suggestions are allowed
- which macro gaps v1 expansion should support first
- how serving sizes stay practical
- how suggestions avoid worsening already-above macros
- how reason codes and limitations should remain public-safe
- how to preserve the current protein-first behavior

## Core principle

AI does not determine nutrition targets.

AI does not determine nutrition actuals.

AI does not invent foods.

AI does not invent serving amounts.

AI does not invent nutrient values.

Food suggestions must come from `canonical_food_id` and `canonical_food_nutrients` only. The backend computes approved targets, logged actuals, gaps, candidate servings, ranking, validation, approval, reason codes, and limitations.

## Existing accepted flow

```text
ApprovedMacroTargets
→ NutritionActuals
→ TargetVsActualNutritionSummary
→ macro gaps
→ canonical food catalog
→ deterministic food suggestion candidates
→ ApprovedNutritionFoodSuggestions
→ Food Suggestions API/UI
```

The expansion should keep this flow. It should add additional supported gap categories only after the target, logging, and canonical-nutrient gates pass.

## Non-goals

This design does not implement:

- service changes
- API changes
- Streamlit changes
- AI nutrition explanation
- meal plans
- meal templates
- barcode scanning
- Open Food Facts import
- large USDA import
- supplement recommendations
- medical nutrition advice
- Target-vs-Actual behavior changes
- DailyCoachSynthesis changes
- report changes
- workout changes
- CrewAI/Ollama paths
- automatic dieting rules
- automatic compensation or restriction logic

## Expansion order

Recommended implementation order:

1. Carbohydrate suggestions.
2. Calorie-support suggestions.
3. Fat-support suggestions.

Rationale:

- Carbohydrate suggestions are usually simple canonical foods with practical serving ranges.
- Calorie support requires more context because foods can move multiple macros at once.
- Fat suggestions require the tightest serving controls because small amounts can add calories quickly.

Protein-first behavior should remain the default priority when a protein gap exists.

## Macro priority

Recommended default priority:

```text
protein → carbohydrate → calorie_support → fat
```

This does not mean every request should produce every category. It means the backend should pick the safest and most useful primary gap first, then optionally include secondary suggestions when they do not conflict with approved targets.

### Why protein remains first

Protein suggestions remain the safest default because:

- protein can be approved independently of calories
- practical servings are easy to bound
- lean protein options can address protein without dramatically increasing fat or calories
- protein suggestions already passed v1 QA

### When carbohydrates outrank calorie support

Carbohydrate suggestions should outrank generic calorie support when:

- carbohydrate target is approved
- calories are approved or at least not above target
- logged carbs are below target
- logging quality supports cautious comparison
- protein is near or above target

### When calorie support outranks carbohydrates

Calorie-support suggestions may outrank carbohydrate suggestions when:

- calorie target is approved
- logged calories are below target
- carbohydrate/fat targets are unavailable but calorie comparison is allowed
- a simple canonical food can provide moderate energy without pushing an already-above macro further out of range

### When fat is primary

Fat should rarely be the primary suggestion category in v1. Fat suggestions should appear only when:

- fat target is approved
- logged fat is below target
- calories are not above target
- the practical serving is small and bounded
- the suggestion does not create a large calorie add-on

## Required gates for all expanded suggestions

All non-protein suggestions require:

1. Approved target display for the macro being addressed.
2. Logged actual value available for the macro.
3. Target-vs-Actual comparison not blocked.
4. Logging quality high enough for cautious comparison.
5. Active canonical food.
6. Required canonical nutrient rows present.
7. Practical serving size within bounds.
8. No forbidden language.
9. No raw/source-only foods.
10. No AI-generated nutrient estimates or serving sizes.

If any gate fails, the service should return limitations and reason codes instead of a food suggestion.

## Carbohydrate suggestions

### Allowed when

Carbohydrate suggestions may be generated when:

- carbohydrate target is approved and displayable
- calorie target is approved and not blocked
- logged carbohydrates are below target
- calories are below or near target
- logging completeness does not block macro comparison
- canonical carbohydrate foods have calorie and carbohydrate nutrient rows

### Blocked when

Carbohydrate suggestions should be blocked when:

- calorie target is blocked
- carbohydrate target is blocked
- calorie actuals are above target enough that additional carbs would conflict with the calorie comparison
- logging completeness is too incomplete for calorie/carb comparison
- canonical nutrient data is incomplete

### Candidate foods

Examples:

- White Rice, Cooked
- Jasmine Rice, Cooked
- Basmati Rice, Cooked
- Oats, Dry
- Potato, Baked
- Sweet Potato, Baked
- Pasta, Cooked
- Whole Wheat Pasta, Cooked
- Banana
- Black Beans, Cooked
- Pinto Beans, Cooked
- Lentils, Cooked
- Flour Tortilla
- Whole Wheat Bread

### Practical serving bounds

| Food family | Suggested bounds |
| --- | ---: |
| Cooked rice | 100–250g |
| Cooked pasta | 100–250g |
| Oats, dry | 30–80g |
| Potato/sweet potato | 150–300g |
| Banana/fruit | 100–200g |
| Beans/lentils | 100–250g |
| Tortilla/wrap | 40–80g |
| Bread | 30–80g |

### Reason codes

Suggested reason codes:

- `carbohydrate_gap_available`
- `carbohydrate_suggestion_available`
- `carbohydrate_target_approved`
- `calorie_target_supports_carb_suggestion`
- `carbohydrate_suggestion_limited_by_calories`
- `carbohydrate_suggestion_limited_by_logging_quality`
- `carbohydrate_gap_suggestions_not_enabled_v1` only until implementation enables this category

### Limitations

Example public-safe limitations:

- “Carbohydrate suggestions are limited because calorie comparison is not currently approved.”
- “Carbohydrate suggestions are limited because logging appears incomplete.”
- “Carbohydrate suggestions are not shown because calories are already near or above target.”

## Calorie-support suggestions

Calorie-support suggestions should be framed as optional energy support, not a command to eat more.

### Allowed when

Calorie-support suggestions may be generated when:

- calorie target is approved and displayable
- logged calories are below target
- logging completeness supports cautious comparison
- the candidate does not worsen an already-above protein, carb, or fat state in an unreasonable way
- canonical food has enough macro nutrient rows to estimate calories and major macros

### Blocked when

Calorie-support suggestions should be blocked when:

- calorie target is blocked or limited
- logging completeness is too incomplete
- calories are near or above target
- the candidate food is highly fat-dense and would overshoot calories quickly
- the candidate would worsen an already-above macro without clear benefit

### Candidate foods

Single-food v1 examples:

- White Rice, Cooked
- Jasmine Rice, Cooked
- Potato, Baked
- Sweet Potato, Baked
- Oats, Dry
- Pasta, Cooked
- Banana
- Greek Yogurt, Plain 2%
- Cottage Cheese, Low Fat
- Peanut Butter
- Almonds
- Avocado

Balanced meal-combination suggestions should wait for a later meal-template milestone.

### Practical serving bounds

| Food family | Suggested bounds |
| --- | ---: |
| Cooked starches | 100–250g |
| Oats, dry | 30–80g |
| Fruit | 100–250g |
| Dairy | 150–250g |
| Nut butter | 16–32g |
| Nuts/seeds | 15–35g |
| Avocado | 50–100g |

### Wording

Allowed framing:

- “Calories are below target based on logged meals. These optional foods can add moderate energy.”
- “A 150g serving of cooked rice can add a moderate amount of carbohydrates and calories.”
- “Calorie-support suggestions are limited because logging appears incomplete.”

Avoid:

- “You need to eat more.”
- “You must add calories.”
- “You are undereating.”
- “Compensate with this food.”

### Reason codes

Suggested reason codes:

- `calorie_gap_available`
- `calorie_support_suggestion_available`
- `calorie_target_approved`
- `calorie_suggestion_limited_by_logging_quality`
- `calorie_suggestion_limited_by_macro_conflict`
- `calorie_gap_suggestions_not_enabled_v1` only until implementation enables this category

## Fat-support suggestions

Fat suggestions should be conservative because fat-dense foods can add calories quickly.

### Allowed when

Fat suggestions may be generated when:

- fat target is approved and displayable
- calorie target is approved and not blocked
- logged fat is below target
- logged calories are below or near target
- practical serving size is small
- canonical food has fat and calorie nutrient rows

### Blocked when

Fat suggestions should be blocked when:

- calorie target is blocked
- fat target is blocked
- calories are near/above target and the fat add-on would likely conflict
- logging quality is too incomplete
- the serving required to address the gap would be extreme

### Candidate foods

Examples:

- Olive Oil
- Avocado Oil
- Peanut Butter
- Almond Butter
- Almonds
- Walnuts
- Cashews
- Avocado
- Cheddar Cheese
- Butter

### Practical serving bounds

| Food family | Suggested bounds |
| --- | ---: |
| Oils | 5–15g |
| Butter | 5–15g |
| Nut butter | 16–32g |
| Nuts/seeds | 15–35g |
| Avocado | 50–100g |
| Cheese | 20–40g |

### Reason codes

Suggested reason codes:

- `fat_gap_available`
- `fat_suggestion_available`
- `fat_target_approved`
- `fat_suggestion_limited_by_calories`
- `fat_suggestion_limited_by_logging_quality`
- `fat_gap_suggestions_not_enabled_v1` only until implementation enables this category

### Limitations

Example public-safe limitations:

- “Fat suggestions are limited because calorie comparison is not currently approved.”
- “Fat suggestions are limited because small fat servings can add calories quickly.”
- “Fat suggestions are not shown because calories are already near or above target.”

## Avoiding macro conflicts

Suggestions should avoid worsening already-above macros.

Examples:

- If protein is above target and calories are below target, avoid protein-heavy calorie suggestions unless no better option exists.
- If fat is above target and calories are below target, prefer carbohydrate-heavy calorie support instead of peanut butter or oil.
- If carbs are above target and calories are below target, prefer protein or fat-balanced options only if those targets allow.
- If calories are above target, do not suggest calorie-support, carb, or fat additions even if one sub-macro appears below target.

This should not become punitive. The system should simply withhold suggestions and explain the limitation.

## Ranking rules

Expanded ranking should remain deterministic.

Suggested scoring factors:

1. Primary macro fit.
2. Does not worsen approved above-target macros.
3. Practical serving size.
4. Complete nutrient data.
5. Food simplicity/commonness.
6. Existing canonical `search_priority`.
7. Serving stays within category bounds.
8. Calorie efficiency for the macro being addressed.
9. Scenario safety from Target-vs-Actual confidence and logging completeness.
10. Stable tie-breaking by display name or canonical ID.

### Protein ranking

Prefer lean, high-protein foods when protein is the gap:

- chicken breast
- turkey breast
- tuna
- shrimp
- Greek yogurt
- cottage cheese
- egg whites
- whey protein powder, generic

Avoid high-fat protein options unless they are explicitly useful and targets support them.

### Carbohydrate ranking

Prefer simple starchy/carbohydrate foods that do not add excessive fat:

- rice
- potato
- oats
- pasta
- banana
- beans/lentils
- tortillas/bread

### Calorie-support ranking

Prefer foods that add moderate energy without creating large macro conflicts.

Calorie support should not always choose the highest-calorie food. It should choose a practical and context-compatible food.

### Fat ranking

Prefer small servings and avoid large calorie jumps:

- oils in small amounts
- nut butters in small amounts
- nuts in small portions
- avocado
- cheese

## Serving-size rules

All serving sizes should be:

- positive
- deterministic
- bounded
- rounded for display
- based on grams
- calculated from canonical nutrients only

Suggested rounding:

| Food family | Rounding |
| --- | ---: |
| Oils/butter | nearest 5g |
| Nut butter | nearest 5g |
| Nuts/seeds | nearest 5g |
| Protein powder | nearest 5g |
| Cooked grains/starches | nearest 25g |
| Fruit/vegetables | nearest 25g |
| Dairy | nearest 25g |
| Meat/fish | nearest 25g |

Do not produce hyper-specific grams such as 173.428g.

## Reason-code model additions

Potential additional reason codes:

- `carbohydrate_suggestion_available`
- `calorie_support_suggestion_available`
- `fat_suggestion_available`
- `macro_conflict_limits_suggestions`
- `calorie_target_required_for_carb_suggestions`
- `calorie_target_required_for_fat_suggestions`
- `calories_near_or_above_target_limits_suggestions`
- `serving_size_capped_by_practical_bounds`
- `suggestion_category_not_enabled_v1`
- `single_food_suggestions_only`
- `meal_template_required_for_combined_suggestion`

Existing no-supported-suggestion semantics should continue to distinguish:

- no true macro gaps
- macro gaps unsupported by the current version
- targets blocked or limited
- no suitable canonical foods found

## Public-safe limitations

Examples:

- “Carbohydrate suggestions are not available because calorie targets are currently limited.”
- “Calorie-support suggestions are limited because logging appears incomplete.”
- “Fat suggestions are limited because small servings can add calories quickly.”
- “No supported suggestion category is available for the current approved gaps.”
- “Suggestions are limited to single canonical foods in this version.”

## Forbidden behavior and language

Reject or avoid:

- “you must eat”
- “you failed”
- “burn this off”
- “skip meals”
- “compensate tomorrow”
- medical/disease claims
- supplement claims beyond generic canonical food entries
- fat-loss guarantees
- exact physiological certainty
- AI-generated foods/macros/servings
- suggestions from non-canonical foods
- suggestions that ignore blocked targets
- suggestions that ignore logging-quality limitations
- extreme serving sizes
- shame, restriction, punishment, or compensation framing

## Model and service implications

The existing model contracts likely remain usable, but future implementation may need:

- additional reason codes
- macro-specific suggestion category support
- category-specific serving bounds
- macro-conflict limitation handling
- primary vs secondary suggestion distinction

`ApprovedFoodSuggestion.macro_gap_addressed` should remain the public macro category, but the service may internally distinguish:

- `protein_g`
- `carbohydrate_g`
- `calories`
- `fat_g`
- `calorie_support`

If `calorie_support` is added internally, the public response should still be clear that the suggestion is optional energy support, not a hard calorie instruction.

## Future endpoint behavior

The existing endpoint can remain stable:

```text
GET /nutrition/{user_id}/food-suggestions?date=YYYY-MM-DD
```

Response shape should remain stable. Expanded categories should appear as additional approved suggestions and reason codes, not as a breaking schema change.

Suggested future response behavior:

- protein gap → protein suggestions
- carbohydrate gap with approved calorie context → carb suggestions
- calorie gap with adequate logging → calorie-support suggestions
- fat gap with approved calorie context → conservative fat suggestions
- unsupported/blocked category → no-supported-suggestion reason codes and limitations

## Streamlit implications

No Streamlit changes in this design milestone.

Future Streamlit behavior should remain simple:

- show food name
- show suggested grams
- show estimated macros
- show macro addressed
- show limitations when category is not enabled or target is blocked

The UI should not turn suggestions into commands or meal plans.

## AI/CrewAI implications

No AI involvement in this flow.

Future AI explanation may only summarize approved suggestions after backend validation. AI must not choose foods, serving sizes, or nutrient values.

## Recommended implementation sequence

1. Macro Expansion Design v1.
2. Add reason-code/model support if needed.
3. Implement carbohydrate suggestions.
4. Add service tests for carb gaps and blocked calorie targets.
5. Implement calorie-support suggestions.
6. Add macro-conflict tests.
7. Implement conservative fat suggestions.
8. Add UX QA for public wording.
9. Only then consider AI explanation design.

## Required tests before implementation acceptance

Future implementation should test:

1. Protein behavior remains unchanged.
2. Carbohydrate gap produces carb suggestions only when calorie context is approved.
3. Carbohydrate suggestions are blocked when calories are blocked.
4. Calorie-support suggestions require approved calorie targets and adequate logging.
5. Calorie-support suggestions are blocked when calories are near/above target.
6. Fat suggestions require approved fat and calorie targets.
7. Fat suggestions are conservative and bounded.
8. Suggestions avoid worsening already-above macros.
9. Serving sizes stay inside macro-category practical bounds.
10. Nutrient estimates are non-negative and canonical-derived.
11. Missing nutrients exclude or limit candidate foods.
12. No non-canonical foods appear.
13. No meal-template behavior appears.
14. Existing Food Suggestions API response shape remains stable.
15. Streamlit Food Suggestions UI remains stable.
16. Target-vs-Actual behavior remains stable.
17. DailyCoachSynthesis behavior remains stable.
18. Forbidden language does not appear.
19. Full pytest passes.

## Architecture decision request

Architecture should confirm whether implementation should proceed in one narrow category at a time.

Recommended next implementation milestone after acceptance:

> Nutrition Food Suggestion Carbohydrate Expansion v1

This keeps expansion controlled and avoids introducing calorie/fat suggestion complexity before carbohydrate behavior is validated.
