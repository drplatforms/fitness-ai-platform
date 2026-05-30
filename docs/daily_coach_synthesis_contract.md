# Daily Coach Synthesis Contract v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

This document defines the first public-safe contract for a single daily coaching synthesis layer that can combine the currently separate daily coaching signals into one concise user-facing summary.

## Purpose

The app now has several strong, validated coaching modules:

- recovery check-ins and `UserHealthState`
- Daily Grounded Recommendation / `ApprovedActionPlan`
- deterministic workout preview / `ApprovedWorkoutPlan`
- workout explanation / `ApprovedWorkoutExplanation`
- completed workout execution history / `TrainingExecutionSummary`
- post-workout review / `ApprovedPostWorkoutReviewSummary`
- planned-vs-actual workout execution summaries

The next product step is to make these feel like one cohesive daily coach experience without letting any one layer overreach.

`DailyCoachSynthesis` should summarize what matters today, explain why, and point the user toward the safest near-term focus. It should not generate workout structure, prescribe progression, diagnose health conditions, rewrite nutrition targets, or replace the existing approved contracts.

## Proposed future flow

```text
Recovery Check-In / UserHealthState
→ Daily Grounded Recommendation
→ ApprovedWorkoutPlan
→ ApprovedWorkoutExplanation
→ TrainingExecutionSummary
→ latest ApprovedPostWorkoutReviewSummary
→ DailyCoachSynthesis
→ optional AI synthesis later
→ Today tab display
```

For v1, the synthesis should be deterministic-only and read-only. It should consume approved/summarized contracts, not raw execution rows, raw notes, raw AI output, or provider diagnostics.

## Core principle

`DailyCoachSynthesis` is a presentation and synthesis contract. It is not a decision engine.

The synthesis may say:

> Recent effort has been a little harder than planned, so use the RIR target as the anchor today.

It must not say:

> Deload this week.

The synthesis may say:

> Recent substitutions are useful context for reviewing plan fit.

It must not say:

> Your adherence is poor.

The synthesis may say:

> Incomplete logging limits how much the system should infer from recent workouts.

It must not say:

> Your training is causing stalled progress.

## Contract owner

Backend should own the approved synthesis contract.

Streamlit should render only approved synthesis fields. Streamlit should not independently decide which execution, recovery, nutrition, or workout-plan claims are safe to show.

CrewAI should not be involved in v1. A later AI synthesis provider may propose a candidate synthesis only after the deterministic contract and validator are stable.

## Proposed model

Suggested model name:

```python
DailyCoachSynthesis
```

Suggested fields:

```text
user_id
synthesis_date
scenario
confidence
today_summary
recovery_signal
training_signal
workout_guidance
execution_context
logging_focus
plan_fit_note
recommended_focus
reason_codes
limitations
```

### Field definitions

#### `user_id`

The user the synthesis was built for.

#### `synthesis_date`

The local date the synthesis describes. This should normally be today's date in the app's configured/user timezone.

#### `scenario`

The current `CoachingDecision.scenario`, such as:

```text
aligned_managed
recovery_limited
nutrition_training_mismatch
improving_after_deload
data_quality_limited
```

This is context for the backend and may be exposed only if product/UX wants scenario visibility. User-facing copy should translate scenario into natural language.

#### `confidence`

Overall synthesis confidence.

Suggested values:

```text
Limited
Low
Moderate
High
```

Confidence should be the conservative minimum of the underlying safe signals when data quality is incomplete.

#### `today_summary`

A concise user-facing summary of the day.

Allowed examples:

```text
Today’s workout is set up to stay controlled and consistent.
Today’s recommendation is mostly about keeping the session manageable while logging improves.
Today looks appropriate for a normal training session with controlled effort.
```

#### `recovery_signal`

A concise recovery-focused statement grounded in `UserHealthState` and the current daily recommendation.

Allowed examples:

```text
Recovery inputs suggest keeping effort controlled today.
Recovery looks supportive enough for normal training, while still keeping the planned RIR range.
Completing today’s recovery check-in will improve the recommendation.
```

#### `training_signal`

A concise training-focused statement grounded in `TrainingConstraints`, `ApprovedWorkoutPlan`, and `TrainingExecutionSummary`.

Allowed examples:

```text
The current plan keeps effort inside the approved RIR range.
Recent completed workouts were generally close to the plan.
Recent effort has been a little harder than planned, so use the RIR target as the anchor today.
```

#### `workout_guidance`

User-facing guidance for today's approved workout plan. This must reference the approved workout plan rather than inventing new exercise programming.

Allowed examples:

```text
Follow the approved workout plan and keep the listed RIR targets as the main guardrail.
Use the planned session as written; avoid turning accessory work into a max-effort test.
Keep the session simple and repeatable so the logged data stays useful.
```

Forbidden in this field:

```text
Add another set.
Increase load.
Reduce volume.
Replace the plan with...
Deload today.
```

#### `execution_context`

A concise summary of recent completed planned workouts if enough data exists.

Allowed examples:

```text
Recent completed workouts were generally close to the plan.
Recent completed sessions are still sparse, so the system should avoid trend claims.
Incomplete logging limits how much the system should infer from recent workouts.
```

#### `logging_focus`

A simple logging or check-in focus for the day.

Allowed examples:

```text
Log reps, weight, and RIR as completely as possible today.
Complete the recovery check-in before training if possible.
If you substitute an exercise, note the replacement so plan fit can be reviewed later.
```

#### `plan_fit_note`

A neutral note about substitutions, skips, or plan fit. It should not judge the user.

Allowed examples:

```text
Recent substitutions are useful context for reviewing plan fit.
If substitutions keep appearing, equipment fit or exercise preference may be worth reviewing.
No recent plan-fit issues stand out from the completed workouts.
```

Forbidden examples:

```text
Your adherence is poor.
You failed to complete the plan.
The programming failed.
```

#### `recommended_focus`

The single highest-priority near-term focus for the user today.

Allowed examples:

```text
Keep effort controlled and log the session clearly.
Complete the workout as planned and keep RIR targets honest.
Improve logging completeness before stronger training conclusions are made.
```

This field should not contain automatic progression, deload, nutrition target changes, or medical claims.

#### `reason_codes`

Backend-facing reason codes explaining why the synthesis was built. These may appear in debug endpoints but should not be primary user-facing copy.

Suggested examples:

```text
daily_recommendation_available
approved_workout_plan_available
training_execution_summary_available
post_workout_review_available
incomplete_logging_limits_confidence
recent_effort_harder_than_planned
recent_substitutions_present
recovery_checkin_missing
```

#### `limitations`

User-safe limitations and backend/debug limitations.

Allowed examples:

```text
Nutrition confidence is limited because recent logging is incomplete.
Execution trends are limited because only one completed planned workout is available.
Recovery confidence is limited until today's check-in is completed.
```

## Input boundaries

### Allowed inputs for v1

`DailyCoachSynthesis` may use:

- `UserHealthState`
- `CoachingDecision`
- `ApprovedActionPlan`
- `NutritionTargets`
- `TrainingConstraints`
- `ApprovedWorkoutPlan`
- `ApprovedWorkoutExplanation`
- `TrainingExecutionSummary`
- latest `ApprovedPostWorkoutReviewSummary`
- latest public-safe planned-vs-actual summary fields
- equipment profile confidence and safe display context if already approved elsewhere

### Inputs to avoid in v1

`DailyCoachSynthesis` should not consume:

- raw actual-set rows
- raw free-text user notes
- raw CrewAI output
- runtime metadata
- validator internals
- prompt text
- unbounded workout history
- unbounded report history
- internal debug payloads

The synthesis should operate on approved summaries and public-safe contracts.

## Endpoint design

Proposed endpoint:

```text
GET /daily-coach/{user_id}/synthesis
```

Suggested response:

```json
{
  "success": true,
  "user_id": 102,
  "synthesis_date": "2026-05-30",
  "scenario": "aligned_managed",
  "confidence": "Moderate",
  "daily_coach_synthesis": {
    "user_id": 102,
    "synthesis_date": "2026-05-30",
    "scenario": "aligned_managed",
    "confidence": "Moderate",
    "today_summary": "Today looks appropriate for a normal training session with controlled effort.",
    "recovery_signal": "Recovery looks supportive enough for normal training while still respecting the planned RIR range.",
    "training_signal": "Recent completed workouts were generally close to the plan.",
    "workout_guidance": "Follow the approved workout plan and keep the listed RIR targets as the main guardrail.",
    "execution_context": "Recent completed workouts were generally close to the plan.",
    "logging_focus": "Log reps, weight, and RIR as completely as possible today.",
    "plan_fit_note": "No recent plan-fit issues stand out from the completed workouts.",
    "recommended_focus": "Complete the approved session with controlled effort and clear logging.",
    "reason_codes": [
      "daily_recommendation_available",
      "approved_workout_plan_available",
      "training_execution_summary_available"
    ],
    "limitations": []
  }
}
```

### Debug endpoint

A debug endpoint may be added later if needed:

```text
GET /daily-coach/{user_id}/synthesis/debug
```

Debug output may include the component summaries used to build the synthesis, but should still avoid raw AI output and raw notes unless explicitly approved.

## Response-shape guidance

Do not change `/recommendations/daily/{user_id}` in v1 unless Architecture explicitly approves adding this synthesis to that response.

Recommendation for v1:

- add a separate endpoint first
- validate the contract independently
- later decide whether the Today tab should call this endpoint
- later decide whether `/recommendations/daily/{user_id}` should reference or embed it

## Deterministic behavior for v1

`DailyCoachSynthesis` should be deterministic-only for v1.

Suggested deterministic precedence:

1. Start with `CoachingDecision.scenario`.
2. Apply current daily recommendation / `ApprovedActionPlan` as the highest-level daily coaching decision.
3. Add `ApprovedWorkoutPlan` guidance only as plan-following context.
4. Add `TrainingExecutionSummary` only if confidence gates allow.
5. Add latest `ApprovedPostWorkoutReviewSummary` only as reflective context, not future programming.
6. Apply safety validator before returning public response.
7. Fall back to a minimal safe synthesis if any source is missing or invalid.

## Confidence gates

### 0 completed planned workouts

Behavior:

- no execution-aware trend copy
- no plan-fit trend copy
- may mention that execution context is not available yet

Allowed:

```text
No completed planned workout history is available yet, so today's guidance should stay anchored to the approved plan and current check-in data.
```

### 1 completed planned workout

Behavior:

- context only
- no trend claims
- no "usually", "consistently", "repeated", or "pattern" language

Allowed:

```text
The most recent completed workout gives some context, but it is not enough for a trend.
```

### 2+ completed planned workouts

Behavior:

- cautious pattern language allowed
- still no automatic progression or deload

Allowed:

```text
Recent completed workouts were generally close to the plan.
```

### Incomplete logging

Behavior:

- uncertainty language required
- avoid strong effort, volume, or plan-fit conclusions

Allowed:

```text
Incomplete logging limits how much the system should infer from recent workouts.
```

### Low confidence

Behavior:

- soft/contextual language only
- prioritize logging/check-in quality and plan-following

Allowed:

```text
Keep today's focus simple: follow the approved plan and improve logging completeness.
```

## Scenario-specific synthesis rules

### `aligned_managed`

Allowed:

- normal training language
- controlled progression language if already present in approved recommendation/plan
- no unnecessary intervention framing

Avoid:

- deload
- reduce intensity
- cut volume
- recovery crisis language

### `recovery_limited`

Allowed:

- controlled effort
- recovery-priority language
- RIR target anchoring
- sleep/check-in/logging focus

Avoid:

- overtraining claims
- medical/injury claims
- automatic deload logic

### `nutrition_training_mismatch`

Allowed:

- nutrition support/logging context
- training demand context
- controlled-session framing

Avoid:

- zero-intake assumptions
- hard calorie/macro claims beyond approved nutrition target confidence
- aggressive conditioning claims

### `improving_after_deload`

Allowed:

- controlled progression
- avoid ramping too quickly
- maintain recovery trend

Avoid:

- overreacting to older poor data
- automatic load increases
- automatic deloads

### `data_quality_limited`

Allowed:

- logging/verification language
- incomplete-data uncertainty
- manageable baseline framing

Avoid:

- overtraining
- stalled progress
- intake adequacy claims
- supplement assumptions
- hard nutrition targets
- strong causality

## Allowed synthesis language

Examples:

```text
Today’s workout is set up to stay controlled and consistent.
Recent completed workouts were generally close to the plan.
Recent effort has been a little harder than planned, so use the RIR target as the anchor today.
Recent substitutions are useful context for reviewing plan fit.
Incomplete logging limits how much the system should infer from recent workouts.
Completing today’s recovery check-in will improve the recommendation.
```

## Forbidden synthesis language

The synthesis validator should reject or fall back on:

```text
overtraining
stalled progress
poor adherence
lack of discipline
failed programming
automatic deload
automatic load increase
automatic progression
medical claims
injury claims
strong trend claims from one workout
skipped work as discipline/failure framing
nutrition adequacy claims beyond existing nutrition target confidence
```

Additional forbidden patterns:

```text
you failed
you did not adhere
your discipline
this proves
this means you should increase
increase load next time
add weight next session
deload this week
cut volume
training is causing
nutrition is inadequate
```

## Validator expectations

Add a `validate_daily_coach_synthesis(...)` function in the future implementation.

It should check:

1. Required fields are present.
2. String fields are concise enough for the Today tab.
3. No forbidden terms are present.
4. One-workout summaries do not contain trend language.
5. Low/Limited confidence outputs remain soft/contextual.
6. `data_quality_limited` does not contain strong causal or adequacy claims.
7. Workout guidance does not alter approved workout structure.
8. Nutrition language does not exceed approved `NutritionTargets` confidence.
9. Reason codes are backend-safe and do not become primary user-facing content.
10. Missing component data produces limitations, not hallucinated certainty.

## Streamlit placement recommendation

Do not add Streamlit UI in this design milestone.

Future placement:

- Today tab
- near Daily Grounded Recommendation
- above Workout Plan Preview
- concise card format
- optional details expander for limitations/reason codes
- no raw debug payloads in the main UI

Suggested card sections:

```text
Today Summary
Workout Guidance
Recovery Signal
Execution Context
Logging Focus
Recommended Focus
```

## Future AI synthesis

CrewAI should not be involved in v1.

Later, after deterministic synthesis is stable:

```text
DailyCoachContext
→ CrewAI CandidateDailyCoachSynthesis JSON
→ backend parse/schema validation
→ synthesis validator
→ ApprovedDailyCoachSynthesis
→ deterministic fallback if invalid/slow
```

Hard requirements for later AI synthesis:

- AI returns JSON only.
- AI does not render final UI copy directly.
- Backend validates and approves everything.
- Invalid/malformed output falls back deterministically.
- No live CrewAI/Ollama calls in pytest.
- No same-process hard timeout hacks unless isolated runtime strategy is used.

## Non-goals

This milestone does not include:

- automatic progression
- weekly periodization
- workout generator changes
- nutrition redesign
- report changes
- Streamlit changes
- CrewAI daily synthesis
- live CrewAI/Ollama in tests
- public response-shape changes unless explicitly approved
- persistence/caching
- workout plan mutation
- nutrition target mutation
- deload logic
- medical/injury advice

## Staged implementation plan

After Architecture accepts this design:

### 1. Daily Coach Synthesis Service v1

Add:

```text
models/daily_coach_synthesis_models.py
services/daily_coach_synthesis_service.py
tests/test_daily_coach_synthesis_service.py
```

Implement deterministic synthesis only.

### 2. Daily Coach Synthesis API v1

Add:

```text
api/routes/daily_coach.py
GET /daily-coach/{user_id}/synthesis
```

Keep `/recommendations/daily/{user_id}` unchanged.

### 3. Streamlit Today Coach Synthesis Card v1

Add a concise Today-tab card that renders only approved synthesis fields.

### 4. AI Daily Coach Synthesis v1

Optional later milestone. Add candidate JSON, parse/validate/approve/fallback boundary.

## Test strategy

Future tests should cover:

1. No recovery check-in available.
2. No completed planned workouts.
3. One completed planned workout does not create trend claims.
4. Multiple completed workouts can produce cautious pattern language.
5. Incomplete logging produces limitation language.
6. Low confidence produces soft/contextual copy only.
7. Harder-than-planned effort anchors to RIR, not overtraining/deload claims.
8. Easier-than-planned effort does not produce automatic progression/load increase claims.
9. Substitutions/skips use plan-fit context, not poor-adherence language.
10. `data_quality_limited` avoids nutrition adequacy, supplement, and stalled-progress claims.
11. Synthesis does not change approved workout exercise/sets/reps/RIR.
12. Synthesis does not change nutrition targets.
13. `/recommendations/daily/{user_id}` response shape remains stable if a separate endpoint is used.
14. Seeded users 101–105 produce safe scenario-aligned synthesis.
15. No live CrewAI/Ollama calls occur in tests.

## Acceptance criteria for future implementation

- Deterministic synthesis service returns a complete `DailyCoachSynthesis`.
- Missing component data produces safe limitations.
- Public endpoint exposes approved synthesis only.
- Existing daily recommendation endpoint remains stable.
- Existing workout preview/execution/history flows remain stable.
- Existing post-workout review endpoint remains stable.
- Existing reports remain stable.
- No forbidden language appears.
- No automatic progression, deload, workout mutation, or nutrition target changes occur.
- Full pytest passes.
