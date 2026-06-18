# DailyCoachSynthesis Nutrition Calibration Context Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines how `DailyCoachSynthesis` can later reference nutrition trend and calibration readiness context in the Coach's Read without implying that nutrition targets have changed or that calibration has been applied.

## Purpose

The nutrition system now has deterministic trend and calibration visibility:

```text
Formula-derived targets
→ Target-vs-Actual
→ NutritionTrendWindow
→ NutritionTargetCalibrationResult
→ Streamlit Trend & Calibration Readiness visibility
```

Those calibration results are assessment/context only. They do not mutate targets, overwrite formula targets, or change user profile, activity, or goal fields.

DailyCoachSynthesis should eventually be able to summarize that readiness context at a high level, for example:

> Targets are still formula-derived, but trend evidence is improving.

or:

> Calibration is not ready yet because more consistent logs or weigh-ins are needed.

The Coach's Read should not duplicate the Nutrition tab, expose raw trend windows, or make calibration sound active before target application is explicitly designed and accepted.

## Core principle

AI does not determine nutrition targets.

AI does not modify targets.

AI does not infer maintenance calories.

AI does not invent trend conclusions.

DailyCoachSynthesis may summarize approved calibration readiness only. It must not apply calibration, mutate targets, claim exact maintenance calories, or imply formula targets have been replaced.

## Existing accepted flow

The accepted trend/calibration flow is:

```text
ApprovedMacroTargets
→ logged nutrition actuals
→ logging completeness
→ bodyweight trend
→ profile / goal / training context
→ NutritionTrendWindow
→ NutritionTargetCalibrationResult
→ Trend & Calibration Readiness UI
```

A future DailyCoachSynthesis integration should consume this flow after approval:

```text
NutritionTargetCalibrationResult
→ bounded synthesis-facing projection
→ existing DailyCoachSynthesis fields
→ concise Coach's Read wording
```

DailyCoachSynthesis should not call the HTTP calibration endpoint internally. It should use direct service composition or a small internal projection helper.

## Non-goals

This design does not implement:

- code changes
- Streamlit changes
- public response-shape changes
- target mutation
- calibrated target application
- formula target overwrite
- profile, activity, or goal mutation
- AI nutrition explanation
- meal planning
- barcode scanning
- external food import
- report changes
- workout changes
- CrewAI/Ollama paths
- exact maintenance-calorie claims
- aggressive target changes
- medical, fat-loss guarantee, or restriction language

## Should DailyCoachSynthesis consume NutritionTargetCalibrationResult?

Yes, but only after implementation is explicitly approved.

`DailyCoachSynthesis` should consume `NutritionTargetCalibrationResult` or a bounded internal projection derived from it. The synthesis layer does not need the full calibration object in public output. It only needs high-level facts such as:

- whether calibration is allowed
- readiness level
- recommended action
- confidence
- whether trend evidence is improving
- whether targets remain formula-derived
- whether logging or weigh-in consistency is limiting readiness
- public-safe reason codes
- public-safe limitations

The internal projection approach is preferred for v1 because it reduces the risk of exposing implementation details or making the Coach's Read too verbose.

### Recommended internal projection

Potential future internal model:

```text
DailyCoachNutritionCalibrationContext
- available: bool
- calibration_allowed: bool
- readiness_level: not_ready | early_signal | usable | strong
- recommended_action: insufficient_data | keep_current_targets | maintain_broad_range | eligible_for_future_refinement
- confidence: Limited | Low | Moderate | High
- targets_remain_formula_derived: bool
- concise_summary: str | None
- reason_codes: list[str]
- limitations: list[str]
```

This projection should remain internal unless Architecture explicitly approves a response-shape change.

## Should DailyCoachSynthesis also consume NutritionTrendWindow?

Prefer consuming `NutritionTargetCalibrationResult` first.

The calibration result should already summarize readiness, reason codes, limitations, confidence, and metadata. For v1 synthesis, this is enough to say whether:

- calibration is not ready
- early trend evidence exists
- the current target range should remain broad
- trend evidence may support future refinement
- targets remain formula-derived

Direct use of `NutritionTrendWindow` should be reserved for implementation cases where the calibration result is missing a safe field needed for concise wording.

If `NutritionTrendWindow` is consumed later, it should also be via direct service composition and should be projected into bounded synthesis context. The Coach's Read should not expose raw trend days, raw logs, raw weigh-ins, or detailed trend calculations.

## Response-shape recommendation

Do not change the public DailyCoachSynthesis response shape for v1.

Calibration context should enrich existing fields only:

- `today_summary`
- `logging_focus`
- `recommended_focus`
- `limitations`
- `reason_codes`

A new public field such as `nutrition_calibration_context` should only be added if Architecture explicitly approves a response-shape change.

## Field-level guidance

### today_summary

May include concise calibration readiness context when useful:

- “Targets are still formula-derived, but trend evidence is improving.”
- “Early nutrition trend evidence is available, but more data is needed before calibration can be trusted.”
- “Nutrition calibration is not ready yet because more consistent logs or weigh-ins are needed.”

Should not say targets changed.

Should not include numeric maintenance calorie claims.

Should not duplicate the Nutrition tab.

### logging_focus

May mention data quality blockers:

- “More consistent nutrition logs will make calibration readiness more useful.”
- “Calibration is limited because the trend window has incomplete logging.”
- “More weigh-ins are needed before bodyweight trend evidence can support calibration.”

Should keep language neutral and practical.

Should not imply failure or blame.

### recommended_focus

May point the user toward the Nutrition tab for details:

- “Review the Nutrition tab for trend and calibration readiness details.”
- “Keep logging consistently so the app can build more useful trend evidence over time.”
- “Targets remain formula-derived for now; focus on consistent logs and weigh-ins.”

Should not prescribe a calorie cut, calorie increase, or target change.

### limitations

Should include public-safe limitations when calibration is not ready or limited:

- “Targets are still formula-derived.”
- “Calibration is not ready because more trend data is needed.”
- “The target range remains broad because bodyweight trend data is limited.”
- “Calibration context is limited because logging consistency is incomplete.”

Should not expose raw internals or database details.

### reason_codes

May include bounded public-safe reason codes, for example:

- `nutrition_calibration_context_available`
- `targets_still_formula_derived`
- `calibration_not_ready`
- `calibration_early_signal`
- `calibration_usable`
- `calibration_strong`
- `trend_evidence_improving`
- `calibration_limited_by_logging`
- `calibration_limited_by_bodyweight_trend`
- `calibration_limited_by_window_length`

The synthesis layer should not expose raw service/debug codes unless they are intentionally public-safe.

## Readiness-level behavior

### not_ready

The Coach's Read may mention only that calibration is not ready and why, using cautious language.

Allowed examples:

- “Calibration is not ready yet because more consistent logs or weigh-ins are needed.”
- “Targets are still formula-derived while the app collects more trend evidence.”
- “The Nutrition tab has more detail on calibration readiness.”

Not allowed:

- saying the user failed
- saying targets are wrong
- suggesting a calorie cut or increase
- implying a calibrated target exists

### early_signal

The Coach's Read may mention early trend evidence but should emphasize that more data is needed.

Allowed examples:

- “Early trend evidence is available, but more data is needed before target calibration can be trusted.”
- “Trend evidence is starting to build, while targets remain formula-derived.”

The phrase “early signal” should not be treated as a recommendation to change targets.

### usable

The Coach's Read may mention that trend evidence is becoming useful, while still making clear that targets have not changed.

Allowed examples:

- “Nutrition trend evidence is usable, but targets are still formula-derived for now.”
- “Current data supports keeping the existing formula-derived target range under review.”

If `recommended_action` is `keep_current_targets`, the synthesis may say:

- “Current data supports keeping formula-derived targets unchanged.”

### strong

The Coach's Read may mention that trend evidence may support future refinement, but must not imply target application.

Allowed examples:

- “The current trend window may support future target refinement, but targets are still formula-derived.”
- “Trend evidence is strong enough to review calibration readiness; the Nutrition tab has more detail.”

Even strong readiness does not mean targets have changed.

## Recommended-action behavior

### insufficient_data

Use limitation language only.

Allowed:

- “Calibration is not ready because the trend window is incomplete.”
- “More consistent logs and weigh-ins are needed before calibration context is useful.”

### keep_current_targets

Use reassurance without certainty claims.

Allowed:

- “Current data supports keeping formula-derived targets unchanged.”
- “Targets remain formula-derived, and current trend evidence does not suggest a change.”

### maintain_broad_range

Use broad-range language.

Allowed:

- “The target range remains broad because trend evidence is still limited.”
- “Targets are still formula-derived, with a broad range preserved for safety.”

### eligible_for_future_refinement

Use future-oriented wording.

Allowed:

- “The current trend window may support future target refinement.”
- “Trend evidence is improving, but targets have not been changed.”

Never say that refinement has happened unless a later target-application milestone explicitly implements it.

## Confidence rules

### High or Moderate confidence

High/Moderate calibration confidence may support concise mention in `today_summary` or `recommended_focus`.

Allowed style:

- “Trend evidence is improving, but targets are still formula-derived.”
- “The Nutrition tab has more detail on calibration readiness.”

### Low confidence

Low confidence should produce limitation or context language only.

Allowed style:

- “Calibration context is limited because logging or weigh-in data is incomplete.”

### Limited confidence

Limited confidence should not produce positive calibration/readiness claims. It may only describe blockers.

Allowed style:

- “Calibration is not ready yet because more trend data is needed.”

## What not to include in Coach's Read

The Coach's Read should not include:

- raw trend-window day rows
- raw food log details
- raw daily check-in rows
- detailed bodyweight trend math
- formula internals
- calibration service internals
- `calibrated_targets` payloads
- target mutation fields
- exact maintenance-calorie estimates
- aggressive calorie changes
- medical or fat-loss claims
- instructions to compensate, restrict, or burn off intake

## Allowed language

Allowed wording includes:

- “Targets are still formula-derived.”
- “Trend evidence is improving.”
- “Calibration is not ready yet because more consistent logs or weigh-ins are needed.”
- “This trend window may support future target refinement.”
- “The Nutrition tab has more detail on calibration readiness.”
- “Current data supports keeping formula-derived targets unchanged.”
- “The target range remains broad because trend evidence is limited.”
- “More consistent logging will make trend evidence more useful.”

## Forbidden language

Forbidden wording includes:

- “Your true maintenance is exactly X calories.”
- “Your targets have been changed.”
- “You failed your target.”
- “You must cut calories.”
- “Your metabolism is damaged.”
- “Your body is in starvation mode.”
- “You need to compensate tomorrow.”
- “Burn this off.”
- “Skip meals.”
- medical or disease claims
- fat-loss guarantees
- eating-disorder-style restriction language
- AI-generated target changes
- exact physiological certainty
- target changes from one day or one incomplete week

## Recommended future implementation shape

Potential helper:

```text
build_daily_coach_nutrition_calibration_context(
    user_id: int,
    synthesis_date: date,
    window_days: int = 28,
) -> DailyCoachNutritionCalibrationContext
```

Potential composition:

```text
build_daily_coach_synthesis(user_id, date)
→ build_nutrition_target_calibration_result(user_id, end_date=date, window_days=28)
→ project result into DailyCoachNutritionCalibrationContext
→ enrich existing synthesis fields
```

The helper should:

- use direct service composition
- avoid internal HTTP calls
- keep target mutation impossible
- keep output bounded and public-safe
- avoid exposing raw trend/calibration internals
- preserve existing response shape

## Suggested synthesis reason-code mapping

Potential mapping from calibration result to DailyCoach reason codes:

```text
calibration_not_ready
→ nutrition_calibration_not_ready
→ targets_still_formula_derived

calibration_early_signal
→ nutrition_calibration_early_signal
→ targets_still_formula_derived

calibration_usable
→ nutrition_calibration_context_available
→ targets_still_formula_derived

calibration_strong
→ nutrition_calibration_context_available
→ nutrition_calibration_future_refinement_possible
→ targets_still_formula_derived
```

Reason codes should remain public-safe and should not imply target mutation.

## Scenario guidance

### No logs or poor logs

Expected Coach's Read behavior:

- mention that calibration is not ready
- point to consistent logging as useful
- keep targets formula-derived
- avoid judgment

### Logs present, missing weigh-ins

Expected behavior:

- mention that bodyweight trend data is limited
- do not infer target accuracy from logs alone
- keep targets formula-derived

### Early 14-day signal

Expected behavior:

- mention early trend evidence only if useful
- emphasize that more data is needed
- avoid any target-change wording

### Usable or strong 28-day window

Expected behavior:

- mention trend evidence is improving or useful
- mention future refinement only as a possibility
- state that targets remain formula-derived
- leave details in the Nutrition tab

### Existing target/action guidance conflict

If another DailyCoachSynthesis component is already warning about incomplete nutrition logging, recovery, or data quality, calibration language should be secondary and concise.

## Test expectations for future implementation

A future implementation milestone should add tests proving:

1. DailyCoachSynthesis composes calibration context internally.
2. Public DailyCoachSynthesis response shape remains unchanged.
3. Not-ready calibration adds cautious limitation language only.
4. Early-signal calibration is described as early and not applied.
5. Usable/strong readiness can be referenced without implying targets changed.
6. Existing today_summary/logging_focus/recommended_focus can be enriched safely.
7. Existing limitations/reason_codes can include calibration context safely.
8. No target mutation fields are exposed.
9. No calibrated targets are exposed through normal synthesis output unless explicitly approved later.
10. No exact maintenance-calorie claims appear.
11. No shame/restriction/medical/fat-loss language appears.
12. Existing DailyCoachSynthesis tests remain stable.
13. Existing trend/calibration tests remain stable.
14. Existing Target-vs-Actual and food suggestion tests remain stable.
15. Full pytest passes.

## Recommended staged implementation

1. Accept this design.
2. Add internal DailyCoach calibration projection helper.
3. Compose `NutritionTargetCalibrationResult` directly into synthesis.
4. Enrich existing fields only.
5. Add service tests for not_ready, early_signal, usable, and strong states.
6. Run UX QA to confirm wording does not imply target mutation.
7. Consider Streamlit changes only if Product wants more visibility beyond the Nutrition tab.
8. Consider AI explanation only after deterministic synthesis context is accepted.

## Summary

DailyCoachSynthesis should eventually summarize nutrition calibration readiness as concise context only. It should make clear that targets remain formula-derived unless a later, explicitly accepted target-application milestone changes that behavior.

The safest v1 implementation path is direct service composition into a bounded internal projection, enrichment of existing synthesis fields, and no public response-shape change.
