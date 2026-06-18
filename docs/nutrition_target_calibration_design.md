# Nutrition Target Calibration Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how formula-derived nutrition targets can eventually become more personalized over time using deterministic trend evidence such as logged intake, bodyweight trend, goal direction, training context, and logging completeness.

## Purpose

The current nutrition target system is intentionally formula-derived and backend-approved. That is the correct baseline because it keeps target calculation deterministic, auditable, and independent from AI/CrewAI output.

Formula-derived targets are still estimates. A future calibration layer can improve target confidence over time by evaluating whether logged intake, bodyweight trend, training context, and logging completeness support keeping the current target range broad, widening it due to uncertainty, or cautiously narrowing it after enough consistent data exists.

The calibration layer should not make aggressive adjustments, silently mutate targets, or claim exact physiological certainty. It should provide explainable, versioned, reversible calibration context.

## Core principle

AI does not determine nutrition targets.

AI does not modify macro targets.

AI does not infer bodyweight trends, maintenance calories, activity multipliers, or macro prescriptions.

Backend deterministic calibration logic may propose target confidence adjustments or range refinements only when sufficient data quality exists.

AI may later explain approved calibration context only after validation, and only in public-safe language.

## Existing accepted baseline

The current accepted nutrition target flow is:

```text
User profile / goal / activity context
→ NutritionTargetFormulaInputs
→ deterministic formula service
→ NutritionTargetFormulaResult
→ formula validation
→ ApprovedMacroTargets
→ Formula API / Target-vs-Actual / Streamlit transparency
```

Future calibration should sit after formula targets and trend summaries:

```text
ApprovedMacroTargets
→ NutritionActuals history
→ NutritionLoggingSummary history
→ bodyweight trend window
→ training/recovery context
→ NutritionTargetCalibrationResult
→ optional calibrated target display context
```

The original formula target should remain traceable even if a future calibrated target range is approved.

## Non-goals

This design does not implement:

- code changes
- target mutation
- database schema changes
- Streamlit changes
- AI nutrition explanation
- meal planning
- barcode scanning
- external food import
- report changes
- workout generation changes
- CrewAI/Ollama paths
- automatic aggressive calorie reductions
- exact maintenance-calorie claims
- medical nutrition advice
- supplement recommendations
- eating-disorder-style restriction language

## Calibration responsibilities

The future calibration layer may:

- evaluate whether data quality is sufficient for calibration
- summarize nutrition logging completeness over an observation window
- summarize bodyweight trend over an observation window
- summarize training frequency or execution context when available
- compare observed trend direction to stated goal direction
- decide whether formula targets should remain unchanged, remain broad, be widened, or be cautiously tightened
- produce confidence, reason codes, limitations, and metadata
- produce public-safe language for transparency

The future calibration layer must not:

- silently overwrite formula targets
- infer missing profile values
- use AI-generated target changes
- use one day or one week of logs as proof
- calibrate from bodyweight alone
- calibrate from incomplete nutrition logs
- treat scale fluctuations as proof of target accuracy
- produce exact maintenance claims
- recommend aggressive restrictions or compensations

## Required input data

Calibration should require a combination of formula target context, logged actuals, bodyweight trend data, goal direction, and data-quality metadata.

### Formula target context

Required:

- approved calorie target range, when calorie calibration is considered
- approved protein target range, when protein confidence is considered
- approved carbohydrate/fat targets, if those are calibrated later
- formula confidence
- formula reason codes and limitations
- formula name/version
- display flags for each target

If a target is not formula-approved/displayable, calibration should not create a calibrated target for it.

### Logged intake data

Required for calorie calibration:

- daily logged calories
- daily logged protein, carbohydrate, and fat when available
- meal count / entry count
- logging completeness classification
- missing nutrient counts
- no-log days
- partial-log days
- abnormal or suspicious entries if already detected

Calibration should evaluate logged actuals only from verified backend nutrition data. Missing nutrient values remain missing, not zero.

### Bodyweight data

Required for calorie target confidence improvements:

- timestamped bodyweight entries
- enough weigh-ins across the calibration window
- recent average bodyweight
- trend direction
- estimated trend rate using bounded logic
- weight-data completeness and variability

Calibration should not infer calorie accuracy from bodyweight alone. Bodyweight trend only becomes useful when paired with adequate nutrition logging and stable profile context.

### Goal direction

Required:

- primary goal
- goal weight, if applicable
- whether the goal implies loss, gain, recomposition, maintenance, or performance support

Calibration should not assume fat-loss intent unless the user profile explicitly supports it.

### Training and recovery context

Useful but not sufficient by itself:

- training frequency
- recent training execution summary
- completed planned workout counts
- average actual RIR / planned-vs-actual context
- recovery/readiness context
- major changes in training load

Training context should usually affect confidence/limitations rather than directly changing targets in v1.

## Observation windows

Calibration should use minimum windows and avoid short-term overreaction.

### Less than 14 days

Use only for context. Do not calibrate target ranges.

Expected output:

- keep formula targets
- confidence Limited or Low
- limitation: more trend data is needed

### 14 to 27 days

Early trend context may be available if logging and weigh-ins are consistent.

Allowed output:

- keep current targets
- maintain broad range
- flag target confidence improving
- possibly add limited calibration context

Not allowed:

- narrowing calorie ranges meaningfully
- declaring maintenance
- changing targets aggressively

### 28 to 41 days

Preferred minimum for stronger calibration review.

Allowed output when data quality is adequate:

- keep current targets with Moderate confidence
- cautiously tighten range within strict bounds
- maintain broad range if signals are mixed
- flag inconsistent logging or weight trend limitations

### 42+ days

Stronger trend context may support a more confident calibration result if data quality is high and profile context is stable.

Allowed output:

- maintain current targets with higher confidence
- cautiously narrow ranges
- keep targets broad if training, logging, or weight trend is unstable

High confidence should still avoid exact physiological certainty.

## Data-quality gates

Calibration requires adequate data quality across the observation window.

### Logging completeness gate

Calibration should remain Limited/Low when:

- many no-log days exist
- many partial-log days exist
- logged calories are frequently missing
- macro fields are frequently missing
- meal/entry counts suggest underlogging
- logging patterns change substantially during the window

Calibration may become Moderate only when:

- most days have complete-enough logs
- calories and macros are consistently present
- missing nutrient values are low enough not to distort interpretation
- no-log days are rare

### Bodyweight completeness gate

Calibration should remain Limited/Low when:

- no bodyweight trend exists
- weigh-ins are sparse
- weigh-ins are clustered too tightly
- trend window is too short
- day-to-day variability overwhelms trend direction

Calibration may become Moderate/High only when:

- weigh-ins cover enough of the observation window
- trend direction is stable enough to interpret cautiously
- scale trend aligns with or reasonably differs from logged intake context

### Profile stability gate

Calibration should remain limited when key profile context changed during the window, such as:

- goal direction changed
- activity level changed
- training frequency changed materially
- bodyweight entry source changed or appears inconsistent
- formula inputs were incomplete for part of the window

## Calibration outputs

A future calibration result should support the following outcomes.

### Keep current targets

Use when formula targets remain appropriate or data is insufficient to justify any change.

Reason codes may include:

- `calibration_not_needed`
- `current_targets_supported`
- `trend_data_consistent_with_targets`

### Maintain broad range

Use when data is promising but still uncertain.

Reason codes may include:

- `target_range_kept_broad`
- `trend_data_mixed`
- `logging_quality_moderate`
- `bodyweight_variability_present`

### Widen target range due to uncertainty

Use when the formula target is displayable but trend evidence is too noisy to narrow it.

Reason codes may include:

- `target_range_widened_for_uncertainty`
- `inconsistent_logging_limits_calibration`
- `bodyweight_trend_limited`

### Cautiously tighten range

Use only with adequate multi-week logging, bodyweight trend, stable profile context, and no major contradictions.

Reason codes may include:

- `target_confidence_improving`
- `sufficient_trend_window`
- `consistent_logging_supports_calibration`
- `bodyweight_trend_available`

Tightening must stay conservative. It should never produce exact single-number certainty.

### Insufficient data

Use when the required minimum evidence does not exist.

Reason codes may include:

- `insufficient_observation_window`
- `insufficient_logging_data`
- `insufficient_bodyweight_data`
- `formula_target_not_approved`

## Future model candidates

### NutritionCalibrationInput

Suggested fields:

- `user_id`
- `calibration_date`
- `observation_start_date`
- `observation_end_date`
- `approved_macro_targets`
- `nutrition_actuals_by_day`
- `logging_summaries_by_day`
- `bodyweight_entries`
- `goal_context`
- `training_context`
- `profile_context`
- `formula_metadata`
- `reason_codes`
- `limitations`

### NutritionTrendWindow

Suggested fields:

- `start_date`
- `end_date`
- `day_count`
- `logged_day_count`
- `complete_log_day_count`
- `partial_log_day_count`
- `no_log_day_count`
- `bodyweight_entry_count`
- `average_logged_calories`
- `average_logged_protein_g`
- `average_logged_carbohydrate_g`
- `average_logged_fat_g`
- `bodyweight_start_average`
- `bodyweight_end_average`
- `bodyweight_trend_direction`
- `bodyweight_trend_rate_per_week`
- `logging_completeness_confidence`
- `trend_confidence`
- `reason_codes`
- `limitations`

### CalibratedMacroTarget

Suggested fields:

- `macro_name`
- `original_target_min`
- `original_target_max`
- `calibrated_target_min`
- `calibrated_target_max`
- `unit`
- `calibration_action`
  - `keep_current`
  - `maintain_broad_range`
  - `widen_for_uncertainty`
  - `cautiously_tighten`
  - `insufficient_data`
- `display_allowed`
- `confidence`
- `reason_codes`
- `limitations`

### NutritionTargetCalibrationResult

Suggested fields:

- `user_id`
- `calibration_date`
- `observation_window`
- `calibrated_targets`
- `overall_action`
- `confidence`
- `metadata`
- `reason_codes`
- `limitations`

### NutritionCalibrationMetadata

Suggested fields:

- `calibration_version`
- `formula_name`
- `formula_version`
- `inputs_used`
- `data_quality_summary`
- `trend_window_days`
- `rounding_rules`
- `safety_limits_applied`
- `created_at`

## Confidence rules

### Limited

Use when:

- observation window is under 14 days
- logs are missing or incomplete
- bodyweight trend is missing
- formula target was not approved
- profile context is incomplete or unstable

Allowed language:

- “Targets are still formula-derived because more trend data is needed.”
- “The target range remains broad because bodyweight trend data is limited.”

### Low

Use when:

- some logs exist but the observation window is short
- logging is inconsistent
- bodyweight entries exist but are sparse
- trend direction is noisy

Allowed language:

- “Logging consistency is improving, so target confidence may increase over time.”
- “Current data supports keeping the target range broad for now.”

### Moderate

Use when:

- at least 28 days of usable data exists
- logging quality is reasonably consistent
- bodyweight trend exists
- profile/goal context is stable
- trend evidence is not contradictory

Allowed language:

- “Current data supports keeping the existing target range.”
- “Trend context is becoming useful, but targets should remain conservative.”

### High

Use only when:

- multiple weeks of consistent logs exist
- bodyweight trend is stable and well-covered
- profile and training context are stable
- data quality is strong

Even at High confidence, the system must not say maintenance is exactly a single value.

## Safety limits

Future calibration should apply hard limits such as:

- no target changes from fewer than 14 days of data
- no meaningful calorie-range narrowing before 28 days
- no aggressive calorie reductions
- no target mutation without explicit approved flow
- no exact single-value calorie truth
- no calibration when logging completeness is poor
- no calibration when bodyweight trend is missing
- no calibration when the underlying formula target is blocked
- no scale-trend-only calibration
- no AI-generated target adjustment

Potential future numeric limits should be reviewed separately before implementation. Examples to consider later:

- maximum allowed calorie target adjustment per calibration review
- minimum calorie floor guardrails
- maximum range narrowing percentage
- minimum number of complete log days
- minimum number of weigh-ins

## Public-safe wording

Allowed future language:

- “Targets are still formula-derived because more trend data is needed.”
- “Logging consistency is improving, so target confidence may increase over time.”
- “Current data supports keeping the existing target range.”
- “The target range remains broad because bodyweight trend data is limited.”
- “After several weeks of consistent logs and weigh-ins, the app may be able to narrow the target range.”

Forbidden language:

- “Your true maintenance is exactly X calories.”
- “You failed your target.”
- “You must cut calories.”
- “Your metabolism is damaged.”
- medical/disease claims
- fat-loss guarantees
- supplement recommendations
- eating-disorder-style restriction language
- AI-generated target changes
- automatic aggressive calorie reductions
- target changes from one day or one week of data

## Interaction with existing systems

### Formula target service

Formula targets remain the baseline. Calibration should not replace or mutate formula output unless an explicit future milestone approves calibrated target selection and persistence.

### Target-vs-Actual

Target-vs-Actual should continue comparing logged actuals against currently approved/displayable targets. Calibration context can later inform display confidence only after implementation and validation are accepted.

### Streamlit

No Streamlit changes are included in this milestone. A future calibration transparency UI should show:

- whether targets are formula-derived or calibrated
- observation window
- data-quality limitations
- confidence
- reason codes
- plain-language explanation

It should not display raw rows by default.

### DailyCoachSynthesis

DailyCoachSynthesis may later reference calibration confidence only after deterministic calibration exists. It should not create target changes or claim exact calorie truths.

### AI/CrewAI

AI/CrewAI must not calculate or adjust targets. A future AI explanation may summarize approved calibration metadata only after deterministic calibration and validation are accepted.

## Recommended staged implementation

1. Nutrition Target Calibration Design v1.
2. Nutrition Trend Window Models v1.
3. Nutrition Trend Summary Service v1.
4. Nutrition Target Calibration Service v1.
5. Calibration QA with seeded multi-week data.
6. Streamlit calibration transparency UI.
7. AI explanation only after deterministic calibration exists.

## Required tests before implementation acceptance

Future implementation milestones should test:

- fewer than 14 days never calibrates targets
- incomplete logs block calibration
- bodyweight-only trend does not calibrate targets
- missing bodyweight trend blocks calorie calibration
- 28+ days of complete logs and weigh-ins can improve confidence
- noisy trend keeps ranges broad
- stable multi-week trend can cautiously tighten range within bounds
- formula-blocked targets cannot be calibrated into approved targets
- AI/CrewAI is not called
- no forbidden wording appears
- Target-vs-Actual remains stable
- DailyCoachSynthesis remains stable unless explicitly changed
- Streamlit compiles
- full pytest passes

## Architecture recommendation

Proceed next with **Nutrition Trend Window Models v1** before any calibration service implementation.

The trend-window model should be read-only and descriptive. It should summarize evidence quality without proposing target changes. Only after trend-window outputs are accepted should Backend implement calibration decisions.
