# Nutrition Target-vs-Actual Architecture v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

## Purpose

Define how logged nutrition intake should compare to approved nutrition targets safely, accurately, and conservatively.

The nutrition pillar should follow the same source-of-truth pattern used in the workout and daily-coach flows:

- deterministic/backend contracts own facts, calculations, confidence, limits, and validation
- AI may later explain approved facts, but must not determine nutrition actuals
- public responses must separate user-facing guidance from debug/runtime internals
- sparse or low-confidence logging must produce limitations, not certainty

## Core principle

AI does not determine nutrition actuals.

Logged foods plus verified nutrition data determine actuals. The backend computes targets, actuals, deltas, confidence, reason codes, and limitations. AI may later explain and synthesize approved nutrition facts within confidence limits.

The system may say:

> Based on logged meals, protein is below today's target.

It must not say:

> Your nutrition is inadequate and caused today's workout to suffer.

The system may say:

> Nutrition logging is incomplete, so calorie conclusions should stay limited.

It must not say:

> You failed your calorie target.

## Proposed future flow

```text
NutritionTargets
→ logged food actuals
→ NutritionActuals
→ TargetVsActualNutritionSummary
→ confidence/logging quality
→ ApprovedNutritionGuidance
→ DailyCoachSynthesis
→ optional AI Nutrition Explanation later
```

For v1 implementation, the flow should be deterministic and read-only. It should not introduce meal planning, external food database imports, AI nutrition explanations, or Streamlit redesign.

## Proposed models

### `NutritionActuals`

Represents the deterministic totals from logged food entries for a specific date/window.

Suggested fields:

- `user_id`
- `logging_date`
- `logging_window`
- `logged_calories`
- `logged_protein_grams`
- `logged_carbohydrate_grams`
- `logged_fat_grams`
- `logged_fiber_grams`
- `logged_sodium_mg`
- `logged_fluid_oz`
- `logged_meal_count`
- `entry_count`
- `source_count`
- `has_logged_nutrition`
- `reason_codes`
- `limitations`

Field notes:

- Calories, protein, carbohydrate, and fat should be supported first.
- Fiber, sodium, and hydration should be optional/later unless already tracked reliably.
- Missing nutrient values should not be coerced to zero unless the entry explicitly has a verified zero value.
- Actuals should be calculated from persisted logs/verified nutrition data, not AI estimates.

### `NutritionLoggingSummary`

Represents logging completeness and reliability for the date/window.

Suggested fields:

- `user_id`
- `logging_date`
- `logging_completeness`
- `confidence`
- `logged_meal_count`
- `entry_count`
- `missing_macro_entry_count`
- `missing_calorie_entry_count`
- `has_partial_entries`
- `reason_codes`
- `limitations`

Suggested `logging_completeness` values:

- `no_logs`
- `partial_day`
- `likely_incomplete`
- `reasonably_complete`
- `complete_enough_for_guidance`

Completeness should be conservative. A low meal count, missing macro fields, or partial entries should reduce confidence.

### `NutritionTargetComparison`

Represents one target/actual comparison.

Suggested fields:

- `nutrient`
- `target_min`
- `target_max`
- `actual`
- `delta_to_min`
- `delta_to_max`
- `percent_of_target`
- `target_status`
- `target_range_status`
- `comparison_allowed`
- `confidence`
- `reason_codes`
- `limitations`

Suggested `target_status` values:

- `below_target`
- `near_target`
- `inside_target_range`
- `above_target`
- `unavailable`

Suggested `target_range_status` values:

- `below_range`
- `inside_range`
- `above_range`
- `unavailable`

`comparison_allowed` should be false when the target is not approved for user-facing comparison or when logging confidence is too limited for a meaningful comparison.

### `TargetVsActualNutritionSummary`

Represents the full public-safe nutrition comparison for a date/window.

Suggested fields:

- `user_id`
- `date`
- `logging_window`
- `nutrition_actuals`
- `logging_completeness`
- `confidence`
- `calorie_comparison`
- `protein_comparison`
- `carbohydrate_comparison`
- `fat_comparison`
- `fiber_comparison`
- `sodium_comparison`
- `hydration_comparison`
- `reason_codes`
- `limitations`

The v1 implementation may include only calories, protein, carbohydrates, and fat if those are the only sufficiently supported fields.

### `ApprovedNutritionGuidance`

Represents deterministic user-facing nutrition guidance based on approved targets and actuals.

Suggested fields:

- `user_id`
- `date`
- `confidence`
- `nutrition_summary`
- `protein_guidance`
- `calorie_guidance`
- `macro_guidance`
- `logging_guidance`
- `training_support_note`
- `reason_codes`
- `limitations`

This is a copy/guidance layer, not a target-generation layer. It must not rewrite targets.

## Approved target comparison rules

Use the existing `NutritionTargets` contract as the source for which targets may be shown.

### Calories

Calories may be compared only when:

- calorie targets exist
- `allow_calorie_targets` is true
- target confidence is sufficient
- logging completeness is not `no_logs` or too limited for the claim being made

When logging completeness is low, calorie copy should be framed as limited:

> Nutrition logging is incomplete, so calorie conclusions should stay limited.

### Protein

Protein may be compared when:

- protein targets exist
- `allow_protein_targets` is true
- the target basis exists, such as body weight or another approved target basis
- logged protein has enough confidence to compare

Protein is usually the safest first target-vs-actual comparison because it is directly useful for training support and less likely to require a full-day calorie estimate.

### Carbohydrates and fat

Carbohydrate and fat targets may be compared only when:

- targets exist
- the corresponding `allow_*_targets` flag is true
- target confidence and logging quality are sufficient

If macro confidence is limited, avoid strong macro conclusions:

> Macro comparisons are limited until logging is more complete.

### Fiber, sodium, and hydration

These should be later/optional unless tracked reliably. In v1, they may be included as unavailable/limited fields if the model is designed to support them without user-facing claims.

## Actual calculation rules

Actuals should be calculated from logged nutrition entries for the requested date/window.

Initial window:

- default: local calendar day
- future option: explicit `date=YYYY-MM-DD`
- future option: user timezone-aware day boundaries

Suggested calculation behavior:

1. Load logged food entries for the user/date.
2. Sum verified numeric fields independently.
3. Track missing nutrient values per entry.
4. Track meal/entry counts.
5. Do not estimate missing nutrient values with AI.
6. Do not infer full-day actuals from partial-day logs.
7. Mark partial or incomplete logs with reason codes and limitations.

If an entry has calories but no macros, calories may contribute to logged calories, while macro comparison confidence should be reduced.

If an entry has macros but no calories, macros may contribute to macro totals, while calorie comparison confidence should be reduced unless calories can be calculated from verified macro values by a deterministic rule approved later.

## Delta and status rules

For each comparable nutrient:

- `actual < target_min`: `below_target` / `below_range`
- `target_min <= actual <= target_max`: `inside_target_range`
- `actual > target_max`: `above_target` / `above_range`
- missing target or disallowed target: `unavailable`
- missing actual or no logs: `unavailable`

For single-point targets, represent as a min/max range with the same value or define a later `target_value` field. Prefer ranges where possible because existing target contracts already use min/max fields.

Percent-of-target should be calculated only when a meaningful denominator exists. For ranges, percent can use the midpoint or the lower bound, but the implementation must document which value is used. For v1, avoid making percent-of-target the primary user-facing phrase.

## Confidence model

Suggested confidence values:

- `Limited`
- `Low`
- `Moderate`
- `High`

Confidence should consider:

- target confidence
- target display flags
- logging completeness
- number of entries/meals
- missing nutrient fields
- date/window completeness
- whether the user is still logging during the day
- whether the comparison is calorie/macro/protein-specific

Confidence should not exceed the lower of target confidence and actual/logging confidence.

Examples:

- High target confidence + complete logs → `High` or `Moderate`
- High target confidence + partial logs → `Low`
- Limited target confidence + complete logs → `Limited` or `Low`
- No logs → `Limited`

## Logging completeness rules

Suggested initial heuristics:

### `no_logs`

Use when no nutrition entries exist for the date/window.

Allowed copy:

> No nutrition logs are available for this date yet.

Forbidden copy:

> You missed your targets.

### `partial_day`

Use when logs exist but the date/window is likely incomplete, such as very few entries or an in-progress day.

Allowed copy:

> Current logs are partial, so target comparisons should stay cautious.

### `likely_incomplete`

Use when meal count is low or important nutrients are missing from several entries.

Allowed copy:

> Logged intake is incomplete, so calorie and macro conclusions should stay limited.

### `reasonably_complete`

Use when there are enough entries/meals and most key nutrient fields are present.

Allowed copy:

> Based on logged meals, protein is close to today's target.

### `complete_enough_for_guidance`

Use when the day/window has enough logged entries and nutrient completeness to support practical guidance. This still does not permit medical or extreme restriction advice.

## Reason codes

Suggested reason codes:

- `no_nutrition_logs_today`
- `partial_nutrition_logging`
- `likely_incomplete_nutrition_logging`
- `complete_enough_for_guidance`
- `protein_target_available`
- `protein_target_unavailable`
- `calorie_target_available`
- `calorie_target_limited`
- `carbohydrate_target_available`
- `carbohydrate_target_limited`
- `fat_target_available`
- `fat_target_limited`
- `macro_targets_limited_by_logging_quality`
- `meal_count_low`
- `entry_count_low`
- `missing_calorie_values`
- `missing_macro_values`
- `training_day_context_available`
- `target_confidence_limited`
- `logged_intake_near_protein_target`
- `logged_protein_below_target`
- `logged_protein_above_target`
- `logged_calories_below_target`
- `logged_calories_near_target`
- `logged_calories_above_target`
- `calorie_delta_not_available`
- `protein_delta_not_available`
- `nutrition_actuals_unavailable`
- `comparison_limited_by_partial_day`

Reason codes are backend diagnostics and should not become the primary user-facing content.

## Limitations

The summary should carry limitations whenever data is missing, confidence is low, or comparison is intentionally suppressed.

Examples:

- `no_logged_nutrition_for_date`
- `nutrition_logging_incomplete`
- `calorie_target_not_approved_for_display`
- `protein_target_not_available`
- `macro_targets_not_approved_for_display`
- `missing_nutrition_values_in_logged_entries`
- `partial_day_logging_limits_calorie_claims`
- `target_confidence_limited`
- `food_database_verification_limited`

## Approved user-facing language

Allowed examples:

- “Based on logged meals, protein is below today’s target.”
- “Nutrition logging is incomplete, so calorie conclusions should stay limited.”
- “Protein is close to target based on current logs.”
- “A protein-centered meal may help support today’s training.”
- “Logged intake is incomplete, so avoid making bigger nutrition changes from this day alone.”
- “Calories are not compared because calorie targets are currently limited.”
- “Macro comparisons are limited until logging is more complete.”

## Forbidden language

The nutrition target-vs-actual layer must not produce:

- hard calorie claims when logging is incomplete
- exact macro certainty from partial logs
- shame or judgment language
- “you failed”
- eating-disorder-style language
- medical or disease claims
- supplement assumptions
- stalled fat-loss claims from sparse data
- “nutrition is inadequate” unless target confidence clearly supports it and Architecture approves that phrase
- extreme restriction advice
- unsupported meal timing claims
- unsupported causality between one meal/day and workout performance
- “your workout suffered because of this meal”
- “you must cut calories”
- “skip meals”
- “compensate tomorrow”
- “burn this off”
- “good food” / “bad food” morality framing

## Approved guidance examples

### Protein below target with adequate logging

```text
Based on logged meals, protein is below today's target. A protein-centered meal may help support today's training.
```

### Calories unavailable because target confidence is limited

```text
Calories are not compared today because calorie targets are currently limited.
```

### Partial logging

```text
Nutrition logging is incomplete, so calorie conclusions should stay limited.
```

### Near protein target

```text
Protein is close to target based on current logs.
```

### No logs

```text
No nutrition logs are available for today yet, so target-vs-actual guidance is limited.
```

## Proposed endpoint

Future endpoint:

```text
GET /nutrition/{user_id}/target-vs-actual?date=YYYY-MM-DD
```

Potential public response:

```json
{
  "success": true,
  "user_id": 102,
  "date": "2026-06-04",
  "nutrition_actuals": {},
  "target_vs_actual_summary": {},
  "logging_completeness": "partial_day",
  "confidence": "Low",
  "reason_codes": [],
  "limitations": []
}
```

Public response must not include:

- raw AI output
- prompt text
- runtime metadata
- provider internals
- validator internals
- unbounded nutrition history
- raw notes beyond approved display fields
- food database debug payloads

## Integration with DailyCoachSynthesis

Future `DailyCoachSynthesis` should consume `ApprovedNutritionGuidance` or `TargetVsActualNutritionSummary`, not raw nutrition logs.

Allowed synthesis examples:

- “Protein is below target based on current logs, so a protein-centered meal may help support today’s training.”
- “Nutrition logging is incomplete, so today’s nutrition guidance should stay limited.”

Forbidden synthesis examples:

- “Your nutrition is inadequate.”
- “You failed your calorie target.”
- “This caused poor training performance.”

## AI involvement

No AI should be involved in this design milestone.

Recommended sequence:

1. Deterministic contracts and summary service.
2. API endpoint.
3. Streamlit nutrition UX.
4. Deterministic nutrition coaching copy.
5. Optional AI Nutrition Explanation later with strict parser/validator/fallback.

If AI is added later, it must receive only approved target-vs-actual facts and limitations. It must not infer actuals, estimate missing nutrition values, rewrite targets, or give medical/extreme restriction advice.

## External food databases

Do not integrate external food databases in this milestone.

Potential later candidates:

- USDA FoodData Central for generic/verified foods
- Open Food Facts for packaged/barcode foods

A later design should define:

- source priority
- verification status
- user-entered vs database-provided values
- barcode handling
- cache strategy
- attribution if needed
- privacy and persistence rules
- fallback behavior when a food cannot be found

## Streamlit

No Streamlit changes in this design milestone.

Future UI should likely include:

- a simple target-vs-actual card
- protein status first
- logging completeness indicator
- limitations displayed gently
- expandable details for calories/macros
- no shame framing
- no hard claims from partial logs

## Non-goals

- no AI meal planning
- no AI nutrition explanation yet
- no meal plan generation
- no large food database import yet
- no supplement recommendations
- no medical nutrition advice
- no weight-loss or stalled-fat-loss claims from sparse data
- no Streamlit redesign
- no report changes unless explicitly approved
- no changes to workout generation
- no automatic progression
- no deload logic
- no eating-disorder-style restriction language
- no external food database integration
- no barcode scanning
- no persistence schema changes in the design milestone

## Recommended implementation sequence

1. Nutrition Target-vs-Actual Architecture v1
2. Nutrition Target-vs-Actual Summary Service v1
3. Nutrition Target-vs-Actual API v1
4. Streamlit Nutrition UX v1
5. Nutrition Coaching Copy v1
6. AI Nutrition Explanation v1
7. Meal Template Catalog v1
8. AI Meal Candidate Design later

## Future service acceptance criteria

A future deterministic summary service should:

- calculate nutrition actuals from logged entries only
- compare only approved targets
- model logging completeness
- model confidence conservatively
- include reason codes and limitations
- avoid hard claims from partial logs
- avoid shame/judgment language
- avoid medical/disease claims
- avoid supplement assumptions
- avoid stalled-fat-loss claims from sparse data
- preserve existing nutrition targets
- not involve AI
- pass seeded-user and edge-case tests

## Future test strategy

Suggested tests:

1. no logs returns `no_logs`, Limited confidence, and no target miss claims
2. partial logging limits calorie conclusions
3. protein target comparison appears when protein target is approved
4. calorie comparison is hidden/limited when calorie targets are not approved
5. macro comparison is hidden when macro targets are limited
6. missing nutrient fields reduce confidence
7. protein below target produces safe protein guidance
8. protein near target produces safe near-target guidance
9. calories above target does not produce shame/restriction language
10. incomplete logging prevents hard calorie claims
11. data_quality_limited scenario avoids nutrition adequacy claims
12. training-day context can support protein-centered guidance without causality claims
13. reason codes are backend-safe
14. public response does not expose debug/provider internals
15. no AI/Ollama calls occur in tests
