# Nutrition Gap Food Suggestion Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how the backend can eventually suggest simple canonical foods that help close approved macro gaps without AI inventing foods, serving sizes, nutrition values, or targets.

## Purpose

The app now has the core nutrition pieces needed to support a safer food-suggestion layer:

- formula-derived macro targets
- target validation and display approval
- Target-vs-Actual comparisons
- canonical app-facing foods
- canonical food search
- canonical food logging write-through
- seeded user profile and goal data

The next step is not full meal planning. The next step is a narrow deterministic helper that answers a smaller question:

> Based on approved target gaps and logged actuals, what simple canonical foods could help move the user closer to target today?

This should be useful for daily logging without becoming prescriptive, medical, shame-based, or AI-invented.

## Core principle

AI does not determine nutrition targets.

AI does not determine nutrition actuals.

AI does not invent foods, servings, or nutrient values.

Backend formula code computes approved targets. Backend nutrition services compute actuals. Backend gap logic computes eligible macro gaps. Backend deterministic suggestion logic selects canonical foods and practical serving amounts from known canonical nutrient data.

AI may later explain approved food suggestions only after backend validation exists.

## Proposed future flow

```text
ApprovedMacroTargets
→ NutritionActuals
→ TargetVsActualNutritionSummary
→ macro gaps
→ canonical food catalog
→ deterministic food suggestion candidates
→ suggestion validation/approval
→ ApprovedNutritionFoodSuggestions
→ Streamlit display / optional AI explanation later
```

The suggestion layer should consume existing approved outputs rather than recomputing or overriding them.

## Non-goals

This design does not implement:

- code changes
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
- automatic dietary rules
- fasting, restriction, or compensation logic

## V1 supported gaps

### Protein first

Protein is the safest and most useful first gap because:

- protein targets can be approved even when calorie targets are limited
- canonical protein foods are easy to seed and validate
- practical serving sizes are straightforward
- suggestions can be framed as optional support, not restriction

Protein suggestions should only be generated when:

- protein target display is approved
- logged protein is available
- target-vs-actual indicates a meaningful protein shortfall
- canonical candidate foods have protein nutrient data

### Calories only with stronger gates

Calorie suggestions should require stronger gates than protein suggestions.

Calories may be considered only when:

- calorie target display is approved
- logging completeness is adequate enough for cautious comparison
- Target-vs-Actual does not mark calorie comparison as limited due to incomplete logging
- suggested calories come from canonical nutrient rows, not inferred values

If calorie comparison is blocked or limited, the suggestion layer may explain:

> Calorie suggestions are limited because logging appears incomplete.

It should not suggest eating or restricting calories from incomplete logs.

### Carbohydrates and fats

Carbohydrate and fat suggestions may be considered later in v1 only when:

- those target displays are approved
- calorie target display is approved
- logging quality supports cautious comparison
- the suggestion can be made with practical serving sizes

Carbs should remain blocked when calorie targets are blocked.

Fat suggestions should be cautious because fat-dense foods can quickly add calories. Fat suggestions should prefer small, bounded serving ranges.

### Blocked targets

No suggestions should be generated for blocked or unavailable targets.

If a target is unavailable, the suggestion result should include a limitation rather than a food recommendation.

## Proposed model contracts

### `NutritionMacroGap`

Represents an approved and displayable macro gap derived from Target-vs-Actual.

Suggested fields:

- `macro_name`
- `actual_amount`
- `target_min`
- `target_max`
- `gap_to_min`
- `gap_to_max`
- `unit`
- `comparison_status`
- `confidence`
- `reason_codes`
- `limitations`

Rules:

- `gap_to_min` and `gap_to_max` must be non-negative when a gap exists.
- Gaps should not be computed from blocked targets.
- Gaps should not be computed from missing actuals.
- Calorie, carbohydrate, and fat gaps should respect logging quality gates.

### `CanonicalFoodSuggestionCandidate`

Represents a deterministic candidate before final approval.

Suggested fields:

- `canonical_food_id`
- `display_name`
- `suggested_grams`
- `estimated_calories`
- `estimated_protein_g`
- `estimated_carbohydrates_g`
- `estimated_fat_g`
- `macro_gap_addressed`
- `candidate_score`
- `confidence`
- `reason_codes`
- `limitations`

Rules:

- `canonical_food_id` must exist and be active.
- Nutrient estimates must come from `canonical_food_nutrients`.
- Missing nutrient rows should remain missing; do not coerce to zero.
- Candidate score should be deterministic.
- Candidate text should not be rendered directly until approved.

### `ApprovedFoodSuggestion`

Represents a public-safe suggestion.

Suggested fields:

- `canonical_food_id`
- `display_name`
- `suggested_grams`
- `estimated_calories`
- `estimated_protein_g`
- `estimated_carbohydrates_g`
- `estimated_fat_g`
- `macro_gap_addressed`
- `confidence`
- `reason_codes`
- `limitations`
- `display_message`

Rules:

- Only approved suggestions can be rendered.
- `display_message` must be optional/supportive, not prescriptive.
- No raw source payloads or internal validation details should appear.

### `ApprovedNutritionFoodSuggestions`

Container returned by a future service or endpoint.

Suggested fields:

- `user_id`
- `suggestion_date`
- `confidence`
- `macro_gaps`
- `suggestions`
- `reason_codes`
- `limitations`
- `display_message`

Rules:

- Empty suggestions are valid when no approved gaps exist.
- Limitations should explain why suggestions are unavailable.
- Public output should be bounded and concise.

## Candidate food pool

Only canonical app-facing foods should be eligible.

Eligible foods must:

- exist in `canonical_foods`
- be active
- have relevant `canonical_food_nutrients`
- have enough nutrient data to estimate the macro being suggested
- be simple/common enough for a daily suggestion
- support grams-first serving math

Foods should not be eligible when:

- inactive
- raw/source-only
- missing relevant nutrient data
- branded/supplement-like claims are ambiguous
- serving would require absurd grams
- the food would primarily address the wrong macro

## Serving-size strategy

Serving sizes should be deterministic, bounded, and practical.

V1 should use grams only. Common serving labels can come later.

Suggested default serving bands:

| Food type | Suggested grams |
| --- | ---: |
| Chicken breast, cooked | 100–200g |
| Turkey/chicken thigh/fish | 100–200g |
| Greek yogurt | 150–250g |
| Cottage cheese | 150–250g |
| Whey protein powder, generic | 25–35g |
| Rice, cooked | 100–250g |
| Pasta, cooked | 100–250g |
| Beans/lentils | 100–250g |
| Potato/sweet potato | 150–300g |
| Fruit | 100–250g |
| Nut butter | 16–32g |
| Oils/butter | 5–15g |
| Nuts/seeds | 15–35g |

Serving rules:

1. Start from a practical serving amount.
2. Estimate nutrient contribution from per-100g canonical nutrients.
3. Cap serving sizes to practical ranges.
4. Avoid suggestions that overshoot the gap dramatically unless they are clearly framed as a partial option.
5. Do not create fractional nonsense such as 173.428g for display.
6. Round grams to simple values such as 5g, 10g, 25g, or food-specific increments.

## Ranking strategy

Suggestions should be ranked deterministically.

Suggested scoring inputs:

1. Macro fit: how well the food addresses the primary gap.
2. Practical serving: suggested grams fall in a normal range.
3. Nutrient completeness: required nutrient rows exist.
4. Food simplicity: common foods rank above obscure foods.
5. Calorie appropriateness: avoid high-calorie add-ons for protein-only gaps unless useful.
6. Fat density: avoid high-fat options for protein gaps when lean options are available.
7. Search priority: reuse canonical food `search_priority` as a common-food signal.
8. Logging confidence: lower logging confidence reduces certainty and may reduce suggestions.

Protein-gap examples:

- Chicken Breast, Cooked, Skinless
- Greek Yogurt, Plain Nonfat
- Cottage Cheese, Low Fat
- Tuna, Canned in Water
- Shrimp, Cooked
- Whey Protein Powder, Generic
- Egg Whites

Carb-gap examples only when approved:

- White Rice, Cooked
- Jasmine Rice, Cooked
- Oats, Dry
- Potato, Baked
- Pasta, Cooked
- Banana
- Black Beans, Cooked

Fat-gap examples only when approved:

- Olive Oil
- Avocado Oil
- Peanut Butter
- Almonds
- Walnuts
- Avocado

## Validation and approval rules

Before rendering, a suggestion validator should reject suggestions that:

- use foods not in the canonical catalog
- use inactive canonical foods
- use raw/source records directly
- use missing nutrient values as zero
- generate unsupported macro estimates
- suggest absurd serving amounts
- suggest blocked macro targets
- suggest calories when calorie comparison is blocked
- suggest carbs when calorie targets are blocked
- use shame, restriction, compensation, or medical language
- imply exact physiological certainty
- imply AI invented foods, targets, or serving sizes

## Public-safe language

Allowed examples:

- “Protein is below target based on logged meals. These foods could help close the gap.”
- “A 150g serving of chicken breast would add about 46g protein.”
- “Greek yogurt is a smaller protein option if you do not want a full meal.”
- “Calorie suggestions are limited because logging appears incomplete.”
- “These are optional food ideas based on currently logged meals and approved targets.”

Forbidden examples:

- “You must eat this.”
- “You failed your macros.”
- “Burn this off.”
- “Skip meals.”
- “Compensate tomorrow.”
- “This will guarantee fat loss.”
- “This treats/prevents disease.”
- “You need exactly X calories.”
- “The AI recommends this food.”
- “Take this supplement.”

Generic food entries such as “Whey Protein Powder, Generic” can be treated as canonical foods when seeded and clearly labeled as generic, but the system should not make supplement claims or medical/performance promises.

## Future service shape

Potential service file:

- `services/nutrition_food_suggestion_service.py`

Potential service functions:

- `build_nutrition_macro_gaps(target_vs_actual_summary)`
- `build_food_suggestion_candidates(macro_gaps, canonical_foods)`
- `approve_food_suggestions(candidates, macro_gaps)`
- `build_approved_nutrition_food_suggestions(user_id, date)`

The service should compose existing services directly. It should not call public HTTP endpoints internally.

## Future endpoint shape

Potential endpoint:

```text
GET /nutrition/{user_id}/food-suggestions?date=YYYY-MM-DD
```

Suggested response:

```json
{
  "success": true,
  "user_id": 1,
  "suggestion_date": "YYYY-MM-DD",
  "confidence": "Moderate",
  "macro_gaps": [
    {
      "macro_name": "protein",
      "gap_to_min": 21.2,
      "unit": "g",
      "confidence": "Moderate"
    }
  ],
  "suggestions": [
    {
      "canonical_food_id": 1,
      "display_name": "Chicken Breast, Cooked, Skinless",
      "suggested_grams": 100,
      "estimated_calories": 165,
      "estimated_protein_g": 31,
      "estimated_carbohydrates_g": 0,
      "estimated_fat_g": 3.6,
      "macro_gap_addressed": "protein",
      "confidence": "Moderate",
      "reason_codes": ["protein_gap", "canonical_food_nutrients_available"],
      "limitations": []
    }
  ],
  "limitations": []
}
```

Public response should not include:

- raw source payload JSON
- raw database rows
- SQL/debug payloads
- validator internals
- stack traces
- AI/provider metadata
- unapproved target values
- foods outside the canonical catalog

## Scenario behavior

### No approved macro gaps

Return success with an empty suggestions list and a calm message.

Example:

> No food suggestions are needed from approved targets right now.

### Protein-only approved target

Return protein suggestions only.

Do not add calorie, carb, or fat suggestions if those targets are blocked.

### Incomplete logging

Show actuals and approved comparisons where allowed, but reduce suggestion confidence.

If logging quality is too incomplete for calories, do not suggest calorie-based additions.

### Missing canonical nutrients

Do not suggest that food for the affected macro.

Missing values remain missing, not zero.

### Data-quality-limited user

Suggestions should be very conservative or unavailable.

The system can say:

> Food suggestions are limited until logging quality improves.

It should not infer strong deficiencies or make large dietary changes.

## Interaction with existing systems

### Formula targets

Suggestions must consume approved formula target outputs through Target-vs-Actual or ApprovedMacroTargets. The suggestion layer does not compute targets.

### NutritionActuals

Suggestions must consume logged actuals. The suggestion layer does not change logged food entries.

### Canonical food catalog

Suggestions use canonical foods and canonical nutrients only. Raw/source records remain provenance/detail, not user-facing suggestion candidates.

### Streamlit

No Streamlit changes in this design milestone.

Future UI should display suggestions as optional food ideas, not commands.

### AI/CrewAI

No AI involvement in v1.

Future AI explanation can only quote or explain approved backend suggestions after validation.

## Recommended staged implementation

1. Nutrition Gap Food Suggestion Design v1.
2. Nutrition food suggestion model contracts.
3. Deterministic macro-gap service.
4. Deterministic canonical food candidate service.
5. Suggestion validation and approval service.
6. Public-safe food suggestion API.
7. Streamlit optional food suggestion panel.
8. Optional AI explanation design after deterministic behavior is accepted.

## Required tests before implementation acceptance

Future implementation should test:

1. Protein gap produces protein-focused canonical suggestions.
2. Protein-only target scenario produces protein suggestions only.
3. Blocked calories prevent calorie suggestions.
4. Blocked calories prevent carbohydrate suggestions.
5. Missing canonical nutrient rows prevent unsupported suggestions.
6. Suggested grams stay inside practical bounds.
7. Suggestions use canonical foods only.
8. Inactive canonical foods are rejected.
9. Missing nutrients remain missing, not zero.
10. Suggestions are ranked deterministically.
11. Data-quality-limited users receive limited/no suggestions.
12. Public response does not expose raw source payloads.
13. Forbidden language is rejected.
14. Target-vs-Actual behavior remains stable.
15. Canonical logging remains stable.
16. DailyCoachSynthesis remains stable.
17. Full pytest passes.

## Architecture decision request

Architecture should confirm whether the next implementation milestone should start with:

1. model contracts only, or
2. deterministic macro-gap service, or
3. full backend suggestion service + endpoint.

Recommended next milestone:

> Nutrition Food Suggestion Models v1

This keeps the same pattern used successfully for nutrition target formulas, workout plans, and recommendation contracts: define contracts first, then deterministic service, then API, then UI.
