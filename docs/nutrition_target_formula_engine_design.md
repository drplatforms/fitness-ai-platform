# Nutrition Target Formula Engine Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines the deterministic formula-engine contract for calculating safe calorie, protein, carbohydrate, and fat targets. It complements the existing `NutritionTargets` and nutrition target-vs-actual contracts by defining how future numeric targets should be calculated, audited, gated, displayed, and explained.

## Purpose

Design a deterministic, auditable macro target calculation engine that can produce safe user-facing nutrition targets using documented formulas, assumptions, confidence gates, and display rules.

The formula engine should make macro targets easier to trust and review by recording:

- the formula version used
- the exact approved inputs used
- the assumptions applied when inputs are missing or coarse
- the computed target ranges
- confidence and display permissions
- reason codes and limitations
- validation outcomes

The engine should not introduce AI-generated targets, meal planning, medical nutrition advice, supplement recommendations, or eating-disorder-style restriction language.

## Core principle

AI does not determine macro targets.

Backend formula code computes targets. Backend records formula version, inputs, assumptions, confidence, limitations, and display permissions. AI may later quote or explain only approved backend target values after validation.

The system may say:

> Your calorie target is estimated from your profile and activity inputs.

It must not say:

> You need exactly 2,143 calories or you will fail your goal.

The system may say:

> This target is shown as a coaching estimate, not a medical requirement.

It must not say:

> Cut calories aggressively to fix stalled fat loss.

## Relationship to existing nutrition contracts

The current system already has:

- `NutritionTargets`: approved target display contract used by recommendations
- `NutritionActuals`: deterministic logged-intake totals
- `TargetVsActualNutritionSummary`: deterministic target-vs-actual comparison
- `ApprovedNutritionGuidance`: public-safe deterministic nutrition copy
- `DailyCoachSynthesis`: public-safe daily coaching synthesis

This design defines the future calculation layer that should sit upstream of `NutritionTargets`.

Proposed future flow:

```text
UserProfile / Recovery / Training Context / Goal Context
→ NutritionTargetFormulaInputs
→ NutritionTargetFormulaEngine
→ NutritionTargetFormulaResult
→ ApprovedMacroTargets
→ NutritionTargets
→ TargetVsActualNutritionSummary
→ ApprovedNutritionGuidance
→ DailyCoachSynthesis
→ optional AI explanation later
```

For v1 implementation, the formula engine should be deterministic and read-only. It should not call external services, mutate user goals, or generate meal plans.

## Target types

### V1 targets

The engine should calculate these targets first:

- calories
- protein grams
- carbohydrate grams
- fat grams

### Later/optional targets

These may be designed later only when tracking and product requirements are ready:

- fiber
- sodium
- hydration
- micronutrients
- meal timing

Fiber, sodium, and hydration should not block v1 macro-target calculation.

## Input contract

### Proposed model: `NutritionTargetFormulaInputs`

Suggested fields:

```text
user_id
calculation_date
body_weight_lb
height_in
age_years
sex
activity_level
training_frequency_per_week
training_load
primary_goal
goal_weight_lb
recovery_status
nutrition_logging_quality
recent_weight_trend
formula_version_requested
input_source_metadata
```

### Required vs optional inputs

#### Required for confident calorie targets

- body weight
- height
- age
- sex, if using a sex-specific BMR formula
- activity level or activity multiplier
- primary goal

If any of these are missing, the engine should either:

- reduce confidence and show broad ranges only, or
- block calorie target display if the estimate would be misleading.

#### Required for confident protein targets

- body weight
- primary goal or training context
- target basis, such as grams per pound of body weight

Protein targets can often be supported with fewer inputs than calorie targets, but should still record the basis and assumptions.

#### Useful but optional context

- training frequency/load
- recovery status
- goal weight
- recent weight trend
- nutrition logging quality

Optional context may adjust confidence or reason codes. It should not produce aggressive target changes by itself.

### Input source rules

Every input should be traceable to a source, such as:

```text
user_profile
recovery_check_in
training_summary
user_goal
manual_setting
default_assumption
not_available
```

The engine should record source metadata so future debugging can answer:

- what inputs were used?
- what inputs were missing?
- which defaults were applied?
- why was confidence lowered?

## Formula strategy

The formula engine should support a documented strategy composed of independent steps.

### Step 1: Estimate BMR/RMR

Preferred future formula:

```text
Mifflin-St Jeor
```

Mifflin-St Jeor is widely used for adult BMR estimation, but it still produces estimates, not medical certainty.

If required sex/height/age inputs are missing, the engine should not fake them. It should either:

- use a less precise fallback formula only if Architecture approves it, or
- block calorie targets and return limitations.

Possible fallback strategy:

```text
body_weight_estimate_range
```

Example fallback concept:

```text
estimated maintenance range = body_weight_lb × broad activity factor range
```

This fallback should have `Low` or `Limited` confidence and should prefer range display over exact values.

### Step 2: Apply activity multiplier

Activity multiplier should be derived from approved app inputs, such as:

- activity level
- training frequency
- training load
- recent execution context, only if already summarized and approved

Suggested multiplier bands for future Architecture review:

```text
sedentary: 1.20
light: 1.35
moderate: 1.50
high: 1.70
very_high: 1.85
```

The engine should store the selected multiplier and reason codes.

### Step 3: Apply goal adjustment

Goal adjustment should be conservative and should avoid extreme restriction.

Possible goal categories:

```text
maintain
fat_loss
muscle_gain
recomposition
performance_support
unknown
```

Suggested design direction:

- `maintain`: no calorie adjustment
- `fat_loss`: small deficit range only when confidence supports it
- `muscle_gain`: small surplus range only when confidence supports it
- `recomposition`: near-maintenance range with protein emphasis
- `performance_support`: maintenance or slight support range, no aggressive deficit
- `unknown`: no goal adjustment or display-limited targets

The engine should not infer stalled progress or automatically change targets from sparse data.

### Step 4: Protein target

Protein should be calculated from body weight and goal/training context.

Suggested design range for later implementation review:

```text
0.7–1.0 g/lb body weight
```

Example target bases:

```text
body_weight_multiplier
lean_body_mass_multiplier_later
manual_override_later
```

The engine should prefer ranges where useful, for example:

```text
protein_grams_min
protein_grams_max
```

A single displayed value may be derived later from the range midpoint, but the calculation record should preserve the range.

### Step 5: Fat target

Fat should use a minimum floor or percent-of-calorie range.

Suggested design options:

```text
fat_min_from_body_weight
fat_percent_of_calories
hybrid_min_floor
```

The engine should avoid targets that create overly restrictive fat intake. If calorie confidence is limited, fat targets should usually be blocked or displayed only as broad guidance.

### Step 6: Carbohydrates as remainder

Carbohydrates should generally be calculated after calories, protein, and fat are known.

Conceptual formula:

```text
carb_calories = calories - protein_calories - fat_calories
carb_grams = carb_calories / 4
```

Carbohydrate targets should require calorie targets, protein targets, and fat targets to be approved. If calorie targets are blocked, carbohydrate targets should generally be blocked too.

### Step 7: Target ranges and rounding

The engine should prefer ranges over false precision.

Suggested rounding:

```text
calories: nearest 50 or 100 kcal
protein: nearest 5 g
carbohydrates: nearest 5 or 10 g
fat: nearest 5 g
```

The engine should avoid presenting values like:

```text
2143 calories
173.6 g protein
```

unless there is a clear internal reason and UI still rounds public display.

## Proposed models

### `NutritionTargetFormulaInputs`

Represents approved inputs available to the formula engine.

Suggested fields:

```text
user_id
calculation_date
body_weight_lb
height_in
age_years
sex
activity_level
training_frequency_per_week
training_load
primary_goal
goal_weight_lb
recovery_status
nutrition_logging_quality
recent_weight_trend
input_sources
missing_inputs
```

### `MacroTargetResult`

Represents one calculated macro target.

Suggested fields:

```text
nutrient
unit
target_min
target_max
target_value
calculation_method
input_values_used
assumptions
confidence
display_allowed
reason_codes
limitations
```

`target_value` should be optional. Ranges should be preferred for public display when confidence is not High.

### `NutritionTargetFormulaMetadata`

Represents audit metadata for the formula run.

Suggested fields:

```text
formula_name
formula_version
calculation_date
input_values_used
input_sources
assumptions
missing_inputs
confidence
display_allowed
reason_codes
limitations
```

### `NutritionTargetFormulaResult`

Represents the complete output of the formula engine.

Suggested fields:

```text
user_id
calculation_date
calorie_target
protein_target
carbohydrate_target
fat_target
confidence
display_flags
formula_metadata
reason_codes
limitations
```

### `ApprovedMacroTargets`

Represents the public-safe approved macro target set used downstream.

Suggested fields:

```text
user_id
calculation_date
calorie_target_min
calorie_target_max
protein_grams_min
protein_grams_max
carbohydrate_grams_min
carbohydrate_grams_max
fat_grams_min
fat_grams_max
confidence
allow_calorie_targets
allow_protein_targets
allow_carbohydrate_targets
allow_fat_targets
nutrition_display_message
formula_name
formula_version
reason_codes
limitations
```

`ApprovedMacroTargets` may later replace or feed the current `NutritionTargets` contract, but v1 implementation should be careful not to break existing response shapes.

## Display flags

The engine should produce explicit display permissions.

Suggested fields:

```text
allow_calorie_targets
allow_protein_targets
allow_carbohydrate_targets
allow_fat_targets
```

Display flags should be false when:

- required inputs are missing
- confidence is too limited
- formula assumptions are too broad
- target would imply false precision
- target would create unsafe or restrictive guidance
- a target depends on another blocked target, such as carbs depending on calories

## Confidence model

Suggested confidence levels:

```text
Limited
Low
Moderate
High
```

### Limited

Use when key inputs are missing or data quality is poor.

Typical behavior:

- do not display calorie targets
- protein target may be blocked or broad only
- macro targets blocked
- show limitations and reason codes

### Low

Use when enough inputs exist for broad guidance only.

Typical behavior:

- calorie range may remain hidden
- protein range may be displayed if body weight exists
- carbs/fat usually blocked unless approved
- public copy stays soft and contextual

### Moderate

Use when inputs are sufficient for cautious target display.

Typical behavior:

- calorie range may be displayed
- protein target may be displayed
- carbs/fat may be displayed if dependencies are satisfied
- target-vs-actual comparison may be allowed cautiously

### High

Use when inputs are complete enough for stronger target-vs-actual comparison.

Typical behavior:

- all core macro targets may be displayed if validator passes
- still no medical certainty
- still no exact physiological certainty

## Reason codes

Suggested reason codes:

```text
formula_inputs_complete
formula_inputs_limited
missing_body_weight
missing_height
missing_age
missing_sex
missing_activity_level
missing_primary_goal
body_weight_available
activity_level_available
training_context_available
goal_context_available
calorie_formula_available
calorie_formula_limited
protein_formula_available
protein_formula_limited
fat_formula_available
fat_formula_limited
carbohydrate_formula_available
carbohydrate_formula_limited
carbohydrate_depends_on_calorie_target
calorie_display_allowed
calorie_display_blocked
protein_display_allowed
protein_display_blocked
macro_display_limited_by_confidence
formula_assumption_used
formula_version_recorded
not_medical_nutrition_advice
```

Reason codes are backend/debug-friendly. User-facing copy should translate them into plain language.

## Limitations

Suggested limitation examples:

```text
Calorie targets are limited because height, age, or activity inputs are missing.
Macro targets are shown as coaching estimates, not medical requirements.
Carbohydrate targets are not shown because calorie targets are not approved yet.
Protein targets are based on body weight and training context.
Formula assumptions were used, so targets should be treated as estimates.
```

Limitations should be human-safe and should not shame the user.

## User-facing language rules

### Allowed language

Allowed examples:

```text
Your approved protein target is 180g.
Your calorie target is estimated from your profile and activity inputs.
This target is shown as a coaching estimate, not a medical requirement.
Carbohydrate and fat targets are based on the remaining approved calorie range after protein and fat minimums.
Protein targets are based on body weight and current training context.
Calorie targets are not shown yet because key profile inputs are missing.
```

### Forbidden language

Forbidden examples:

```text
you need exactly X calories
you must cut calories
skip meals
burn this off
compensate tomorrow
this will fix fat loss
your metabolism is damaged
you are noncompliant
you failed your macros
good foods / bad foods
supplements are required
medical nutrition treatment
```

Forbidden categories:

- exact physiological certainty
- medical/disease claims
- eating-disorder-style restriction language
- shame/judgment language
- supplement assumptions
- unsupported fat-loss/stalled-progress claims
- AI-generated numeric targets
- unsupported causality between one day of intake and training outcomes

## Numeric fidelity and future AI support

The design should prepare for future AI explanations without allowing numeric drift.

Rules for future AI nutrition explanation:

- AI may only quote approved numeric values from backend fields.
- AI must not invent calorie, protein, carbohydrate, or fat targets.
- AI must not round differently from the approved display contract unless explicitly provided a display value.
- AI must not convert a range into an exact requirement.
- AI must not change display permissions.
- AI must not explain blocked targets as if they are approved.

Future validator should reject:

- numeric targets not present in the approved backend payload
- numeric values outside approved ranges
- single exact claims when backend approved only a range
- calorie claims when `allow_calorie_targets` is false
- carb/fat claims when display flags are false
- forbidden language or medical/restriction claims

UI should render critical numeric targets directly from backend fields whenever possible. AI copy should be secondary explanatory text, not the source of numeric truth.

## Validation expectations

Future implementation should include validation for formula outputs and approved target copy.

Validator should confirm:

- required fields exist
- confidence is one of the approved values
- display flags match confidence and input completeness
- calorie targets are blocked when key inputs are missing
- carbohydrate targets are blocked when calorie targets are unavailable
- target ranges are sane and non-negative
- target ranges do not imply extreme restriction
- target values are rounded for public display
- formula metadata includes formula name and version
- limitations exist when assumptions/defaults were used
- user-facing copy contains no forbidden language

## Public response design direction

A future endpoint may look like:

```text
GET /nutrition/{user_id}/targets/formula
```

Potential response:

```text
success
user_id
calculation_date
approved_macro_targets
formula_metadata
confidence
display_flags
reason_codes
limitations
```

Public response should not expose:

- raw internal calculation scratchpad
- raw SQL rows
- private notes
- AI/provider metadata
- prompt text
- validator internals
- unapproved blocked target values unless Architecture explicitly approves debug-only exposure

A debug endpoint may later expose more formula details, but should stay separate from public endpoints.

## Non-goals

This milestone does not include:

- implementation
- Streamlit changes
- AI nutrition explanation
- AI meal planning
- meal plan generation
- external food database import
- barcode scanning
- medical nutrition advice
- supplement recommendations
- report changes
- workout changes
- automatic progression
- deload logic
- CrewAI/Ollama path
- nutrition target mutation
- persistence/schema changes
- formula runtime endpoint

## Recommended implementation sequence after design

1. Nutrition Target Formula Engine Design v1
2. Nutrition Target Formula Models v1
3. Nutrition Target Formula Service v1
4. Nutrition Target Formula Validation v1
5. Nutrition Target Formula API v1
6. Streamlit Target Transparency UI v1
7. Target-vs-Actual integration update, if needed
8. AI Nutrition Target Explanation Design v1

## Test strategy for future implementation

Future tests should cover:

- missing body weight lowers confidence and blocks protein/calorie targets as appropriate
- missing height/age/sex blocks or lowers calorie target confidence
- protein target can be calculated from body weight when approved
- carbs are blocked when calorie targets are blocked
- fat minimum prevents unrealistic fat targets
- formula metadata records formula name/version
- assumptions are recorded when defaults are used
- display flags match confidence gates
- target ranges are rounded and sane
- forbidden language is rejected
- AI-style drift from approved numeric values is rejected by validator
- existing `NutritionTargets` response shape remains stable until Architecture approves changes
- target-vs-actual service remains stable
- DailyCoachSynthesis remains stable

## Acceptance criteria for design approval

Architecture should confirm:

- target types are appropriate for v1
- formula strategy is acceptable as a deterministic/backend-owned path
- confidence and display rules are conservative enough
- proposed model boundaries fit existing `NutritionTargets`
- AI numeric-fidelity rules are sufficient for future AI explanation work
- non-goals are correctly preserved
