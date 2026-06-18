# Workout Execution Completion and Planned-vs-Actual Summary Design

## Purpose

This document defines how an in-progress planned workout should eventually be completed and summarized.

The current system can preview, select, start, and log actual performed sets against a planned workout. Actual sets are stored in `workout_execution_set_actuals`, which acts as the execution-specific bridge between persisted planned exercises and actual performance.

This is a design document only. It does not implement completion endpoints, planned-vs-actual endpoints, Streamlit completion UI, CrewAI workout generation, weekly periodization, automatic progression, or recommendation-engine awareness of execution results.

## Current stable flow

The current workout execution flow is:

```text
Workout Plan Preview
→ POST /workout-plans/{user_id}/select
→ selected WorkoutPlanInstance
→ selected WorkoutExecutionSession
→ POST /workout-plans/{plan_instance_id}/start
→ started WorkoutPlanInstance
→ started WorkoutExecutionSession
→ draft workout_session row
→ POST /workout-plans/{plan_instance_id}/actual-sets
→ workout_plan_instance.status in_progress
→ workout_execution_session.status in_progress
→ workout_execution_set_actuals rows
```

The preview endpoint remains stateless:

```text
GET /workout-plans/preview/{user_id}
```

A preview must not create durable execution records.

## Design principles

1. Completion should finalize a selected/started plan instance, not regenerate or mutate the original preview.
2. `workout_execution_set_actuals` should remain the source of truth for planned-execution summaries in v1.
3. Manual workout logging must remain independent.
4. Completion should preserve actual-set rows exactly as logged.
5. Planned-vs-actual summaries should be derived from persisted planned exercises and actual sets.
6. Skipped and substituted work should be explicit, not inferred from missing data alone.
7. Empty or near-empty completions should require intentional user action.
8. Completion should not trigger automatic progression changes in v1.
9. CrewAI should not generate completion summaries or workout execution outcomes in this flow.
10. Recommendation-engine awareness of actual execution should come after the completion summary contract is stable.

## Completion endpoint shape

Recommended endpoint:

```text
POST /workout-plans/{plan_instance_id}/complete
```

Reason:

- the user-facing workflow starts from a plan instance
- current select/start APIs are already plan-instance oriented
- the UI will likely have `plan_instance_id` available
- the execution session is an internal bridge object

Alternative internal endpoint:

```text
POST /workout-execution-sessions/{execution_session_id}/complete
```

This may be useful later for worker/internal APIs, but it should not be the primary v1 UI-facing route unless Architecture decides to expose execution sessions directly.

## Completion eligibility

### Recommended v1 eligibility

A workout can be completed when:

- `workout_plan_instance` exists
- `workout_execution_session` exists
- plan status is `started` or `in_progress`
- execution session status is `started` or `in_progress`

A workout cannot be completed when:

- plan does not exist
- execution session does not exist
- plan is already `completed`
- plan is `abandoned`
- execution session is already `completed`
- execution session is `abandoned`

### Completing from in_progress

This should be the normal path.

`in_progress` means at least one actual set, skip, or substitution has been logged. Completion from this state should not require every planned exercise to have an actual row. Missing planned exercises should be surfaced in the summary as not logged or incomplete.

### Completing from started with no actual sets

This should be allowed only with explicit confirmation.

Recommended v1 request option:

```json
{
  "allow_empty": true,
  "completion_notes": "Ended session without logging sets."
}
```

If `allow_empty` is not true and no actual-set rows exist, the API should reject completion with a clear error.

Reason:

- it prevents accidental completion from a started-but-unused plan
- it still allows users to intentionally close a started session
- it avoids forcing users to create fake skipped rows just to clean up the workflow

### Empty completion behavior

If `allow_empty = true`, completion should:

- mark the plan and execution session completed
- set completed timestamps
- produce a summary with zero actual/completed sets
- mark completion percentage as 0
- preserve the linked draft `workout_session` row if it exists
- include a deviation flag such as `empty_completion`

## Completion behavior

Completion should:

1. Verify plan and execution session existence.
2. Verify eligible statuses.
3. Load planned exercises.
4. Load actual-set rows.
5. If no actual rows exist, require explicit `allow_empty = true`.
6. Compute planned-vs-actual summary.
7. Set `workout_plan_instances.status = completed`.
8. Set `workout_execution_sessions.status = completed`.
9. Set `workout_execution_sessions.completed_at`.
10. Set `workout_plan_instances.updated_at` and, if the schema has it, `completed_at`.
11. Preserve all actual-set rows.
12. Preserve the linked `workout_session_id`.
13. Optionally write a completion note to the execution session or future summary table.
14. Return plan instance, execution session, planned exercises, actual sets, and summary.

Recommended response shape:

```json
{
  "success": true,
  "workout_plan_instance": {},
  "execution_session": {},
  "planned_exercises": [],
  "actual_sets": [],
  "planned_vs_actual_summary": {}
}
```

## Abandon/cancel behavior

Abandoned/cancelled should be separate from completed.

Recommended endpoint for a later milestone:

```text
POST /workout-plans/{plan_instance_id}/abandon
```

### When abandonment is appropriate

Use `abandoned` when:

- the user started the wrong plan
- the user decided not to do the session
- the execution flow should close without being treated as completed

### Actual rows during abandonment

If actual rows exist, abandonment should not delete them.

Recommended behavior:

- preserve actual rows
- preserve linked `workout_session` if it contains real work
- mark plan and execution session `abandoned`
- do not count it as completed in planned-vs-actual completion rates
- optionally still allow a separate partial-work summary later

### Do abandoned workouts count in summaries?

For v1 planned-vs-actual summaries:

- abandoned plans should not count as completed workouts
- abandoned plans may appear in execution history with status `abandoned`
- abandoned plans with actual rows may still be useful for workout history, but not for completion adherence metrics

## Planned-vs-actual summary contract

A planned-vs-actual summary should compare persisted `planned_workout_exercises` against `workout_execution_set_actuals`.

Recommended summary fields:

- planned_exercise_count
- completed_exercise_count
- skipped_exercise_count
- substituted_exercise_count
- planned_set_count
- actual_set_count
- completed_set_count
- skipped_set_count
- completion_percentage
- average_planned_rir
- average_actual_rir
- rir_deviation
- rep_deviation
- notes
- deviation_flags

### Field definitions

`planned_exercise_count`
: Number of persisted planned exercise rows for the plan instance.

`completed_exercise_count`
: Number of planned exercises with at least one completed actual set, plus substitutions that count toward a planned exercise.

`skipped_exercise_count`
: Number of planned exercises explicitly marked skipped.

`substituted_exercise_count`
: Number of actual-set rows or planned exercises where `substitution_for_planned_exercise_id` is populated.

`planned_set_count`
: Sum of `planned_workout_exercises.sets`.

`actual_set_count`
: Count of execution actual rows that represent performed work. Skipped-only rows should not count as actual performed sets.

`completed_set_count`
: Count of actual rows where `completed = true` and `skipped = false`.

`skipped_set_count`
: Count of actual rows where `skipped = true`.

`completion_percentage`
: Suggested v1 calculation:

```text
completed_set_count / planned_set_count * 100
```

If `planned_set_count` is zero, completion percentage should be null or 0 with a `missing_planned_sets` deviation flag.

`average_planned_rir`
: Average planned RIR midpoint across planned sets. For each planned exercise, use `(rir_min + rir_max) / 2` weighted by planned set count.

`average_actual_rir`
: Average `actual_rir` across completed actual sets where actual RIR is present.

`rir_deviation`
: Suggested v1 calculation:

```text
average_actual_rir - average_planned_rir
```

Interpretation:

- negative value means actual effort was harder than planned
- positive value means actual effort was easier than planned
- zero means actual effort matched the planned average

`rep_deviation`
: Suggested v1 calculation compares each actual set's `actual_reps` to the planned rep range copied onto the actual row.

Possible representation:

```json
{
  "sets_below_planned_reps": 1,
  "sets_inside_planned_reps": 4,
  "sets_above_planned_reps": 2
}
```

`notes`
: Human-readable system summary or user completion notes. For v1, keep this simple and deterministic.

`deviation_flags`
: Machine-readable flags for future UI and coaching logic.

Suggested v1 flags:

- empty_completion
- incomplete_logging
- skipped_exercises_present
- substitutions_present
- actual_effort_harder_than_planned
- actual_effort_easier_than_planned
- reps_below_plan
- reps_above_plan
- missing_actual_rir
- missing_actual_reps

## Summary interpretation rules

Planned-vs-actual summary should be descriptive, not judgmental.

Allowed interpretations:

- actual effort was harder than planned
- actual effort was easier than planned
- actual reps were below, within, or above planned ranges
- user skipped or substituted exercises
- logging is incomplete

Avoid v1 interpretations such as:

- automatic progression increase
- automatic deload
- failure judgment
- overtraining claims
- stalled progress claims
- recommendation-engine decisions

The summary is a measurement layer. Coaching implications should come later through an approved recommendation pathway.

## Relationship to workout_sessions and workout_sets

For v1 completion summary, keep `workout_execution_set_actuals` as the summary source.

Do not overload manual `workout_sets` yet.

Recommended current policy:

- manual workout logging continues to use `workout_sessions` and `workout_sets`
- planned execution uses `workout_execution_set_actuals`
- started workout plans already link to a draft `workout_sessions` row
- `workout_set_id` on `workout_execution_set_actuals` remains nullable
- mirroring execution actuals into `workout_sets` can be designed later

Reason:

- preserves manual workout logging
- avoids premature coupling
- keeps planned-vs-actual summary stable
- allows actual-set UI to mature before changing workout history semantics

Future option:

When the execution workflow is stable, completed execution actuals can be mirrored to `workout_sets`, or `workout_sets` can gain nullable execution-link fields. That should be a separate milestone.

## Future API shape

### POST /workout-plans/{plan_instance_id}/complete

Completes an eligible started or in-progress workout plan.

Potential request body:

```json
{
  "allow_empty": false,
  "completion_notes": "Good session. Rows felt easier than planned."
}
```

Response:

- success
- workout_plan_instance
- execution_session
- planned_exercises
- actual_sets
- planned_vs_actual_summary

### GET /workout-plans/{plan_instance_id}/planned-vs-actual

Returns summary for a selected, started, in-progress, completed, or abandoned plan.

For selected/started plans with no actual rows, response should show planned counts and zero/null actual metrics.

For in-progress plans, response should show partial actual progress.

For completed plans, response should show final summary.

## Streamlit sequencing

Do not add a complete button until this contract is accepted and the backend completion endpoint exists.

Recommended UI order:

1. simple execution-state viewer
2. actual-set logging UI
3. completion button
4. planned-vs-actual display
5. later: summary-driven coaching insights

Do not add Streamlit completion UI in the design milestone.

## Recommendation-engine awareness

Do not feed execution actuals into recommendation logic yet.

Recommended sequence:

1. persist actual set data
2. design and implement completion summary
3. QA summary values for normal, skipped, substituted, and partial sessions
4. decide which summary fields are safe to expose to recommendation context
5. update recommendation logic only after the summary contract is stable

This prevents the recommendation engine from drawing conclusions from incomplete or unstable execution data.

## Non-goals

This milestone does not implement:

- complete workout endpoint
- planned-vs-actual endpoint
- Streamlit complete UI
- planned-vs-actual UI
- CrewAI workout generation
- weekly periodization
- automatic progression engine
- recommendation-engine execution awareness
- workout_sets mirroring
- workout history semantic changes
- wearable integration
- calendar scheduling

## Staged implementation plan

Recommended future sequence:

1. Workout Execution Completion + Planned-vs-Actual Summary Design v1
2. Planned-vs-Actual summary service v1
3. Complete workout endpoint v1
4. Planned-vs-actual endpoint v1
5. Execution-state viewer in Streamlit
6. Actual-set logging UI in Streamlit
7. Completion UI in Streamlit
8. Workout history integration/mirroring design
9. Recommendation-engine execution awareness design

## Test strategy

Future tests should cover:

- cannot complete missing plan
- cannot complete selected plan that has not started
- can complete in_progress plan
- can complete started plan only with `allow_empty = true`
- completion without actual rows is rejected without `allow_empty`
- completion sets plan status to completed
- completion sets execution session status to completed
- completion sets completed_at timestamp
- completion preserves actual-set rows
- completed plan cannot accept new actual sets unless Architecture explicitly allows reopening
- planned-vs-actual summary counts planned exercises
- planned-vs-actual summary counts completed exercises
- planned-vs-actual summary counts skipped exercises
- planned-vs-actual summary counts substitutions
- completion percentage is calculated correctly
- average planned RIR is calculated correctly
- average actual RIR is calculated correctly
- RIR deviation handles harder-than-planned and easier-than-planned sessions
- rep deviation handles below/inside/above planned rep ranges
- manual workout logging remains independent
- preview remains stateless
- select/start/actual-set behavior remains stable
- /recommendations/daily/{user_id} remains stable
- full report safety path remains stable

## Open questions for Architecture

1. Should completion from `started` with no actual sets require `allow_empty = true`, or should empty sessions be abandoned instead?
2. Should completed plans be immutable, or should users be allowed to add/correct actual sets after completion?
3. Should a future completion summary be persisted, or computed on demand from planned and actual rows?
4. Should abandoned sessions with actual sets appear in workout history?
5. Should the first implementation include `POST /complete` and `GET /planned-vs-actual` together, or split them into separate milestones?
6. When should execution actuals be mirrored into `workout_sets`?
7. Which summary fields are safe to expose to future recommendation context?
