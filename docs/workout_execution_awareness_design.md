# Workout Execution Awareness Design

## Purpose

This document defines how completed planned-vs-actual workout execution summaries should eventually inform `UserHealthState`, `RecommendationContext`, `CoachingDecision`, and `ApprovedActionPlan` without jumping directly to automatic progression, weekly periodization, CrewAI workout generation, or recommendation-engine execution decisions.

The current system can preview, select, start, log actual performed sets, edit/correct actual sets, complete a workout, dynamically compute planned-vs-actual summaries, and display execution history. This document describes the next architecture boundary: how execution history should become an input signal for coaching awareness.

This is a design document only. It does not implement execution-aware user state, recommendation logic, API changes, Streamlit UI, automatic progression, CrewAI workout generation, weekly periodization, or workout-set mirroring.

## Current stable flow

The current planned workout execution flow is:

```text
Workout Plan Preview
→ Select plan
→ Start plan
→ Actual Set Logging UI
→ Actual Set Editing UI
→ execution review updates
→ planned-vs-actual summary updates
→ Complete Workout UI
→ completed workout
→ Workout Execution History UI
```

The current execution data sources are:

- `workout_plan_instances`
- `planned_workout_exercises`
- `workout_execution_sessions`
- `workout_execution_set_actuals`
- dynamic `WorkoutPlannedVsActualSummary`

The current manual workout logging workflow remains independent and should not be replaced by planned workout execution awareness.

## Design principles

1. Execution awareness should be descriptive before it becomes prescriptive.
2. Completed planned workouts should inform context, not automatically drive progression.
3. One incomplete or poor workout should not cause strong coaching conclusions.
4. Dynamic planned-vs-actual summaries remain the source of execution awareness for v1.
5. Manual workout logging remains independent.
6. Edited/corrected actual sets should be reflected dynamically, but recommendation logic should not consume correction-sensitive data until the correction/audit model is stable.
7. Incomplete execution data should reduce confidence rather than produce stronger claims.
8. Execution awareness should be scenario-safe and must not contradict the existing `CoachingDecision` layer.
9. CrewAI should not receive raw execution data until the deterministic boundary is designed and tested.

## Which completed workouts should be included?

Recommended v1 policy:

- include only completed planned workout executions by default
- use a recent rolling window, such as the latest 3 to 5 completed planned workouts
- optionally cap by date range, such as the last 14 to 30 days
- exclude selected and started workouts from execution-awareness conclusions
- treat in-progress workouts as live execution state only, not trend evidence
- exclude abandoned/cancelled workouts from completion/adherence conclusions unless a later abandonment-specific signal is designed

Reason:

Completed executions are the safest first input because they have a stable completion boundary and a completed planned-vs-actual summary. Selected, started, and in-progress plans are useful for UI state, but they should not drive longitudinal coaching claims.

Recommended future filters:

- `status = completed`
- `completed_at IS NOT NULL`
- same user id
- latest N completions, newest first
- ignore or down-rank summaries with `empty_completion` or severe missing-data flags

## What planned-vs-actual fields matter?

The most useful v1 fields from `WorkoutPlannedVsActualSummary` are:

- `planned_exercise_count`
- `completed_exercise_count`
- `skipped_exercise_count`
- `substituted_exercise_count`
- `planned_set_count`
- `actual_set_count`
- `completed_set_count`
- `skipped_set_count`
- `completion_percentage`
- `average_planned_rir`
- `average_actual_rir`
- `rir_deviation`
- `sets_below_planned_reps`
- `sets_inside_planned_reps`
- `sets_above_planned_reps`
- `deviation_flags`

Useful derived awareness signals:

- execution completion consistency
- frequent skipped planned work
- frequent substitutions
- actual effort harder than planned
- actual effort easier than planned
- actual reps often below planned range
- actual reps often above planned range
- incomplete actual logging
- missing RIR quality
- missing reps quality

These should be interpreted conservatively. For example, a single workout with `actual_effort_harder_than_planned` should not trigger a deload recommendation by itself.

## Proposed future model boundary

Use a separate execution-awareness model rather than overloading `UserTrainingState` immediately.

Recommended future dataclass:

```python
@dataclass
class TrainingExecutionSummary:
    user_id: int
    completed_execution_count: int
    recent_plan_instance_ids: list[int]
    average_completion_percentage: float | None
    average_planned_rir: float | None
    average_actual_rir: float | None
    average_rir_deviation: float | None
    skipped_exercise_count: int
    substituted_exercise_count: int
    sets_below_planned_reps: int
    sets_inside_planned_reps: int
    sets_above_planned_reps: int
    incomplete_logging_count: int
    missing_actual_rir_count: int
    missing_actual_reps_count: int
    execution_quality: str
    execution_effort_trend: str
    execution_completion_trend: str
    confidence: str
    reason_codes: list[str]
```

Potential classification values:

```text
execution_quality:
- no_planned_execution_data
- limited_execution_data
- inconsistent_logging
- mostly_completed
- consistently_completed

execution_effort_trend:
- unknown
- easier_than_planned
- aligned_with_plan
- harder_than_planned
- mixed

execution_completion_trend:
- unknown
- low_completion
- moderate_completion
- high_completion
- mixed
```

Alternative name:

```text
WorkoutExecutionState
```

Recommended name: `TrainingExecutionSummary`, because this should be a summarized signal, not a raw execution state object.

## How this connects to UserHealthState

Recommended staged connection:

1. Add `TrainingExecutionSummary` as a separate model/service.
2. Build it from completed workout plan executions.
3. Attach it to `UserHealthState` only after tests prove the model is stable.
4. Keep existing `UserTrainingState` unchanged initially.
5. Later, decide whether selected fields should be copied into `UserTrainingState`.

Reason:

`UserTrainingState` currently summarizes broad workout history and training load. Planned execution data is more specific: it compares intended training against performed training. Keeping it separate avoids overloading training state and makes it easier to reason about confidence.

Potential future health-state shape:

```python
@dataclass
class UserHealthState:
    ...
    training_execution_summary: TrainingExecutionSummary | None = None
```

Recommended initial behavior when no completed planned workouts exist:

- `completed_execution_count = 0`
- `execution_quality = "no_planned_execution_data"`
- `confidence = "Limited"`
- no coaching claims based on planned-vs-actual execution

## How this connects to RecommendationContext

`RecommendationContext` should receive a safe, summarized execution signal, not raw actual-set rows.

Recommended future fields:

```python
@dataclass
class RecommendationContext:
    ...
    training_execution_summary: TrainingExecutionSummary | None = None
```

LLM-safe serialization should expose only high-level, validated fields. Do not expose raw actual-set notes or raw execution rows to CrewAI or final report generation in v1.

Example safe payload:

```json
{
  "completed_execution_count": 4,
  "average_completion_percentage": 87.5,
  "execution_quality": "mostly_completed",
  "execution_effort_trend": "harder_than_planned",
  "execution_completion_trend": "high_completion",
  "confidence": "Moderate",
  "reason_codes": [
    "recent_completed_planned_workouts",
    "actual_effort_harder_than_planned"
  ]
}
```

Forbidden in the LLM-safe context:

- raw set notes
- raw corrected values before audit semantics are stable
- unbounded history
- unsupported causality claims
- automatic progression instructions

## How this connects to CoachingDecision

`CoachingDecision` may eventually use execution awareness as a tie-breaker or confidence modifier, not as the primary scenario classifier.

Recommended v1 usage:

- if execution data is incomplete, reduce confidence rather than changing scenario
- if actual effort is repeatedly harder than planned and recovery is poor, support recovery-limited or controlled-progression language
- if completion is consistently high and recovery/nutrition are aligned, support gradual progression language
- if planned work is frequently skipped or substituted, recommend reviewing plan fit/equipment/preferences before intensifying
- if actual reps are often below plan, recommend reviewing load selection or recovery before increasing demand

Do not use execution awareness alone to claim:

- overtraining
- stalled progress
- poor adherence
- lack of discipline
- readiness to progress aggressively
- need for deload

The existing scenario layer should remain the primary safety boundary:

```text
UserHealthState
→ CoachingDecision
→ TrainingConstraints
→ RecommendationContext
→ ApprovedActionPlan
```

Execution awareness can become an additional signal feeding the same boundary, not a replacement for it.

## How daily recommendations should use execution history

Daily recommendations should use completed execution summaries conservatively.

Examples of acceptable usage:

- “Your recent planned workouts are mostly being completed, so keep progression gradual while recovery remains stable.”
- “Recent execution logs show several skipped sets, so keep the next session manageable and review whether the plan fits today’s recovery and equipment.”
- “Actual RIR has been lower than planned across recent completed sessions, so avoid turning every set into near-failure work.”
- “Execution logging is incomplete, so keep using the plan as a guide and improve set-level logging before drawing stronger conclusions.”

Examples of unacceptable usage:

- “You are overtraining because one session had low RIR.”
- “Your progress has stalled because you skipped one exercise.”
- “Increase volume next week because you completed one workout.”
- “You failed the workout.”
- “You lack adherence.”
- “The plan is ineffective” based only on one incomplete execution.

Recommended daily recommendation behavior:

- include execution awareness only when at least two completed planned workouts exist, unless the copy is explicitly framed as limited
- use confidence labels
- prefer “review,” “monitor,” and “adjust conservatively” language
- avoid automatic progression decisions
- never expose internal reason codes in user-facing copy

## Claims forbidden from incomplete execution data

When planned execution data is missing, incomplete, edited, or based on only one workout, user-facing outputs should not claim:

- overtraining
- stalled progress
- inadequate adherence
- failed workout
- poor discipline
- strength regression
- workout plan failure
- automatic need to deload
- automatic need to increase volume
- automatic need to decrease volume
- readiness for aggressive progression
- nutrition failure based on workout execution alone

Allowed safer language:

- “execution data is limited”
- “logging is incomplete”
- “one workout is not enough to establish a trend”
- “review plan fit before making stronger changes”
- “keep progression conservative while more execution history accumulates”
- “actual effort appeared harder than planned in the logged sets”

## How to avoid overreacting to one bad or incomplete workout

Recommended safeguards:

1. Require a minimum completed workout count before trend claims.
2. Use rolling averages across recent completed planned workouts.
3. Track confidence separately from the signal.
4. Treat incomplete logging as lower confidence, not negative performance.
5. Do not let one skipped exercise change the scenario by itself.
6. Do not let one low-RIR set trigger a deload recommendation by itself.
7. Require cross-domain agreement before stronger coaching changes.

Cross-domain agreement examples:

- low recovery score + repeated actual effort harder than planned + high soreness may support recovery-aware language
- high completion + aligned nutrition + stable recovery may support gradual progression language
- frequent substitutions + equipment constraints may support plan-fit/equipment review language
- incomplete execution logs + incomplete nutrition logs should produce data-quality language, not performance conclusions

## Future service design

Recommended future service:

```text
services/training_execution_summary_service.py
```

Potential functions:

```python
build_training_execution_summary(user_id: int) -> TrainingExecutionSummary
get_recent_completed_execution_summaries(user_id: int, limit: int = 5) -> list[WorkoutPlannedVsActualSummary]
classify_execution_quality(summary: TrainingExecutionSummary) -> str
```

The service should depend on the existing workout plan persistence/summary layer and should not query raw manual workout logs for planned-vs-actual conclusions.

Potential future tests should monkeypatch or seed planned execution rows directly. Tests should not call CrewAI/Ollama.

## Future integration order

Recommended staged implementation:

1. `TrainingExecutionSummary` model/service.
2. Unit tests for completed planned workout summary aggregation.
3. Attach `TrainingExecutionSummary` to `UserHealthState` behind a safe default.
4. Add execution summary to `RecommendationContext`.
5. Update deterministic daily recommendation logic to use execution summary conservatively.
6. Add validator tests for forbidden execution-based claims.
7. Only later consider recommendation-engine execution awareness in full reports.
8. Only after that consider automatic progression design.

## Test strategy

Future tests should cover:

- no completed planned workouts returns no/limited execution data
- one completed workout creates limited-confidence execution awareness
- multiple completed workouts create moderate/high-confidence execution awareness
- incomplete actual logging produces limited confidence
- skipped sets increase skipped counts but do not imply poor adherence alone
- substitutions increase substitution counts and suggest plan-fit review when repeated
- repeated harder-than-planned actual RIR creates harder-than-planned execution trend
- repeated easier-than-planned actual RIR creates easier-than-planned execution trend
- reps below plan create below-plan signal without claiming strength regression
- completed workout corrections update dynamic summary before aggregation
- manual workout logging remains independent
- daily recommendation output does not overreact to one incomplete workout
- data_quality_limited users receive logging/verification language
- aligned_managed users do not receive unnecessary deload/reduce-intensity language
- recovery_limited users can receive conservative effort guidance when execution and recovery agree
- `/recommendations/daily/{user_id}` remains stable
- full report safety path remains stable

Seeded-user strategy:

- create planned execution histories for users 101–105 only in tests or seed scripts dedicated to execution-awareness QA
- avoid modifying real user data
- ensure seeded users still preserve their existing scenario expectations
- add scenario-specific execution histories gradually, not all at once

## Non-goals

This design does not implement:

- `TrainingExecutionSummary` model/service
- `UserHealthState` changes
- `RecommendationContext` changes
- `CoachingDecision` changes
- `ApprovedActionPlan` changes
- Streamlit UI changes
- automatic progression
- weekly periodization
- CrewAI workout generation
- recommendation-engine execution awareness
- workout_sets mirroring
- audit trail or voiding

## Recommended next implementation milestone

If Architecture accepts this design, the next narrow implementation milestone should be:

```text
Training Execution Summary Service v1
```

Suggested scope:

- add `TrainingExecutionSummary` model
- add `build_training_execution_summary(user_id)` service
- aggregate recent completed planned workout summaries
- classify execution quality, effort trend, completion trend, and confidence
- do not connect it to `UserHealthState` yet unless Architecture explicitly approves
- do not change recommendation output yet
- preserve manual workout logging independence
