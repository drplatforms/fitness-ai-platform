# Post-Workout Review Public Contract + Placement Design v1

## Status

Accepted implementation target for the post-workout review public-safe contract.

This milestone follows `AI Post-Workout Review Summary Debug v1`.

## Core principle

`ApprovedWorkoutPlan` and the completed `WorkoutExecutionSession` remain the
source of truth.

The post-workout review may summarize and reflect on completed work. It must not
prescribe, alter, or decide future programming.

## Backend endpoint contract

Public-safe endpoint:

```text
GET /workout-executions/{execution_id}/post-workout-summary
```

The endpoint is on-demand and read-only for v1.

### Public response

The public response includes only:

```text
success
user_id
execution_id
plan_instance_id
approved_post_workout_review_summary
```

### Public response exclusions

The public response must not include:

```text
approved_workout_plan
planned_vs_actual_summary
post_workout_review_runtime_metadata
provider source
raw output diagnostics
validation errors
fallback details
raw AI output
prompt/context
```

### Debug endpoint retained

Debug endpoint:

```text
GET /workout-executions/{execution_id}/post-workout-summary/debug
```

The debug response may include:

```text
approved_workout_plan
planned_vs_actual_summary
approved_post_workout_review_summary
post_workout_review_runtime_metadata
```

## Generation behavior

For v1:

- generation remains on-demand/read-only
- no persistence or caching
- no automatic generation at workout completion
- no recommendation or progression integration
- no TrainingExecutionSummary behavior changes

Provider behavior:

- `POST_WORKOUT_REVIEW_PROVIDER=deterministic` remains default
- `POST_WORKOUT_REVIEW_PROVIDER=crewai` remains optional/debug-oriented
- invalid AI output falls back deterministically
- public endpoint returns approved summary only regardless of provider source

## Streamlit placement design

Post-workout review summary should appear only after a workout is completed.

Recommended placement order:

1. Completed workout review screen after `Complete Workout` succeeds.
2. Workout history detail view for a completed planned workout.
3. Later, a compact card in a completed-workout summary area if the Today flow
   surfaces the most recent completed session.

Do not place post-workout review copy:

- during active workout execution
- inside set logging/editing controls
- before workout completion
- as a replacement for planned-vs-actual details
- as a source for automatic next-workout programming

The UI should label the copy as a review/reflection, not as a prescription.

## Copy boundaries

Approved post-workout review copy may:

- summarize completion
- compare actual effort to planned RIR in neutral language
- reflect on substitutions or skipped work as context
- encourage better logging
- provide a concise next-time focus cue without programming changes

Approved post-workout review copy must not:

- prescribe the next workout
- change exercises
- change sets, reps, RIR, or equipment
- recommend automatic progression
- recommend automatic load increases
- recommend deloads
- diagnose overtraining
- claim stalled progress
- criticize adherence or discipline
- make medical or injury claims
- make unsupported nutrition claims

## Deterministic fallback copy cleanup

The deterministic completion reflection should avoid failure framing.

Use:

```text
Most differences from the plan should be treated as session context, not as a judgment.
```

Do not use:

```text
Most differences from the plan should be treated as session context, not as a failure.
```

## Non-goals

Do not add in this milestone:

- Streamlit UI implementation
- persistence or caching
- automatic generation at workout completion
- automatic progression
- weekly periodization
- next-workout prescription
- recommendation behavior changes
- TrainingExecutionSummary changes
- nutrition changes
- report changes
- live CrewAI in pytest
- same-process timeout hacks
