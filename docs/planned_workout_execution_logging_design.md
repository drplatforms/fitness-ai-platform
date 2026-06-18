# Planned Workout Execution Logging Design

## Purpose

This document defines how a started workout plan should eventually become actual logged workout data.

The current system can preview, select, and start an `ApprovedWorkoutPlan`. Starting a plan creates a draft `workout_sessions` row and links it to a `WorkoutExecutionSession`, but it does not yet log actual performed sets, complete the workout, or calculate planned-vs-actual results.

This is a design document only. It does not implement actual-set logging, completion endpoints, planned-vs-actual summaries, Streamlit execution controls, CrewAI workout generation, or progression automation.

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
→ draft workout_sessions row
→ workout_execution_sessions.workout_session_id populated
```

The current preview endpoint remains stateless:

```text
GET /workout-plans/preview/{user_id}
```

A preview should not create durable records. Durable records begin only when the user selects or starts a plan.

## Design principles

1. Manual workout logging must continue to work independently.
2. Planned workout execution should reuse or bridge to existing `workout_sessions` and `workout_sets` instead of replacing them.
3. Planned work and actual work should remain distinguishable.
4. A started plan should be able to become `in_progress` on the first actual set log.
5. Skipped and substituted exercises should be represented explicitly.
6. Planned-vs-actual comparison should be derived from persisted planned rows and actual set rows, not from regenerated previews.
7. CrewAI should not generate or render workout execution data in this flow.
8. Completion should preserve logged work even when the user deviates from the plan.

## Mapping planned exercises to actual performed sets

The selected plan currently persists exercise-level rows in `planned_workout_exercises`.

Each actual set logged during a planned execution should be associated with:

- one `workout_execution_session`
- one draft or finalized `workout_session`
- optionally one `planned_workout_exercise`
- the performed exercise name
- actual reps, weight, and RIR
- skipped/substitution metadata when applicable

Recommended v1 mapping:

```text
workout_plan_instances
→ planned_workout_exercises
→ workout_execution_sessions
→ workout_execution_set_actuals
→ workout_sessions / workout_sets bridge
```

The new actual-set table should be the execution-specific source of truth for planned-vs-actual comparison. Existing `workout_sets` can remain the general workout-history table.

## Reuse, extend, or bridge existing workout_sets

There are three possible strategies:

### Option A — Extend workout_sets directly

Add planned-execution fields directly to `workout_sets`, such as:

- workout_execution_session_id
- planned_workout_exercise_id
- skipped
- substitution_for_planned_exercise_id

Advantages:

- fewer tables
- actual history and execution history live together

Drawbacks:

- risks complicating manual workout logging
- may require broader migration of existing workout-set workflows
- harder to keep planned execution separate from manual logging

### Option B — Add workout_execution_set_actuals and bridge to workout_sets

Create a dedicated execution table, while optionally linking each actual set to a general `workout_sets` row.

Advantages:

- preserves manual workout logging independently
- keeps execution-specific state isolated
- supports planned-vs-actual summaries cleanly
- allows v1 implementation without changing every existing workout logging path

Drawbacks:

- requires synchronization between execution actuals and general workout history
- slightly more model complexity

### Option C — Separate execution actuals only, no workout_sets bridge

Keep planned execution actuals entirely separate from existing workout history.

Advantages:

- simplest execution-specific implementation
- minimal risk to manual logging

Drawbacks:

- completed planned workouts may not appear naturally in existing workout history
- future health state and recent exercise logic may miss planned workouts unless it reads both sources

## Recommended v1 persistence approach

Use **Option B**:

```text
workout_execution_set_actuals
```

as the execution-specific table, with an optional link to `workout_sets`.

This keeps existing manual workout logging stable while giving the planned execution flow enough structure to represent skipped exercises, substitutions, set-level actuals, and planned-vs-actual summaries.

## Recommended future table: workout_execution_set_actuals

Suggested fields:

- id
- workout_execution_session_id
- planned_workout_exercise_id
- workout_session_id
- workout_set_id
- exercise_name
- set_number
- planned_reps_min
- planned_reps_max
- planned_rir_min
- planned_rir_max
- actual_reps
- actual_weight
- actual_rir
- completed
- skipped
- substitution_for_planned_exercise_id
- notes
- created_at
- updated_at

### Field notes

`workout_execution_session_id` should always be populated.

`planned_workout_exercise_id` should be populated when the actual set maps to a planned exercise.

`workout_session_id` should point to the draft or finalized session created when the plan was started.

`workout_set_id` can be populated when an execution actual is also mirrored into the existing `workout_sets` table.

`exercise_name` should store the performed exercise name. For normal planned work, this matches the planned exercise. For substitutions, this is the substituted exercise.

`substitution_for_planned_exercise_id` should be populated when the user performs a different exercise instead of the planned one.

`completed` and `skipped` should not both be true.

## Should workout_sets reference planned_workout_exercise_id?

Eventually, yes, but not necessarily in the first implementation.

Recommended staged approach:

1. Add `workout_execution_set_actuals` first.
2. Write execution actuals there.
3. Optionally mirror completed actual sets into `workout_sets` for existing history views.
4. Add a nullable `planned_workout_exercise_id` to `workout_sets` only if the manual logging service and history views need a direct link.

This avoids forcing the existing manual workout logger to understand planned execution immediately.

## Skipped planned exercises

A skipped planned exercise should be represented explicitly, either by:

1. one skipped row in `workout_execution_set_actuals`, or
2. an exercise-level future table such as `workout_execution_exercise_actuals`.

Recommended v1 approach:

Use one `workout_execution_set_actuals` row with:

```text
planned_workout_exercise_id = planned exercise id
exercise_name = planned exercise name
set_number = null or 0
completed = false
skipped = true
notes = user-entered or system-generated reason
```

This is enough to support planned-vs-actual summaries without adding another table immediately.

Potential skipped reasons can stay in `notes` for v1. A structured `skip_reason` field can be added later if needed.

## Substituted exercises

A substituted exercise means the user did not perform the planned exercise but performed a replacement.

Recommended representation:

```text
planned_workout_exercise_id = original planned exercise id
substitution_for_planned_exercise_id = original planned exercise id
exercise_name = actual substituted exercise name
completed = true
skipped = false
actual_reps / actual_weight / actual_rir populated
notes = optional substitution reason
```

The original planned exercise should not also need a separate skipped row unless the UI wants to show both:

- planned exercise was not performed
- substituted exercise was performed

For v1, the substitution row is enough.

## Changed weights, reps, and actual RIR

Actual values should be logged per set:

- actual_reps
- actual_weight
- actual_rir

Planned values should be copied onto each actual row at creation time:

- planned_reps_min
- planned_reps_max
- planned_rir_min
- planned_rir_max

This allows planned-vs-actual summaries to remain stable even if the original planned exercise rows are later expanded or migrated.

A user can perform:

- fewer reps than planned
- more reps than planned
- different load than expected
- lower RIR / higher effort than planned
- higher RIR / easier effort than planned

All should be preserved as actual performance, not rejected by default.

Validation should reject invalid data, not normal deviation:

- negative reps
- negative weight
- RIR outside a supported range, such as 0-10
- missing planned session
- actual set attached to another user's execution session

## First actual set log behavior

When the first actual set is logged for a started plan:

1. Verify the `WorkoutPlanInstance` exists.
2. Verify the `WorkoutExecutionSession` exists.
3. Verify the session status is `started` or `in_progress`.
4. Verify a draft `workout_session_id` exists.
5. If status is `started`, transition:

```text
started → in_progress
```

6. Insert the execution actual row.
7. Optionally insert or mirror a row into existing `workout_sets`.
8. Return the updated execution session and actual set.

This keeps `started` meaningful: the user opened/began the plan, but has not yet logged work.

`in_progress` means at least one actual set, skip, or substitution has been recorded.

## Completion behavior

Completion should finalize the planned workout execution.

Recommended endpoint:

```text
POST /workout-plans/{plan_instance_id}/complete
```

Reason:

- the current select/start API is plan-instance oriented
- the UI will likely already have `plan_instance_id`
- the parent plan instance and execution session should complete together

Alternative endpoint:

```text
POST /workout-execution-sessions/{execution_session_id}/complete
```

This is also valid, but it exposes the lower-level execution-session identity directly. It may be useful later for internal APIs, but for v1 the plan-instance endpoint is simpler for UI flow.

Completion should:

1. verify the plan exists
2. verify the execution session exists
3. allow completion from `started` or `in_progress`
4. optionally reject completion with no actual rows, unless the user confirms an empty completion
5. set `workout_plan_instances.status = completed`
6. set `workout_execution_sessions.status = completed`
7. set completed timestamps
8. finalize the linked `workout_sessions` row
9. compute planned-vs-actual summary metadata or make it available through a summary endpoint

## Abandon/cancel behavior

A future abandon endpoint can be added separately:

```text
POST /workout-plans/{plan_instance_id}/abandon
```

Recommended behavior:

- if no actual sets exist, mark plan and execution session abandoned
- if actual sets exist, preserve the linked workout session and actual rows
- do not delete manually meaningful workout history
- do not count abandoned plan as completed for progression logic

## Future API shape

Recommended future API shape:

```text
GET /workout-plans/{plan_instance_id}/execution
POST /workout-plans/{plan_instance_id}/actual-sets
PATCH /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}
POST /workout-plans/{plan_instance_id}/complete
GET /workout-plans/{plan_instance_id}/planned-vs-actual
```

### GET /workout-plans/{plan_instance_id}/execution

Returns the selected or started execution state:

- workout_plan_instance
- execution_session
- planned_exercises
- actual_sets
- approved_workout_plan
- rendered plan if useful

### POST /workout-plans/{plan_instance_id}/actual-sets

Logs one actual set, skip, or substitution.

Potential request body:

```json
{
  "planned_workout_exercise_id": 123,
  "exercise_name": "Goblet Squat",
  "set_number": 1,
  "actual_reps": 10,
  "actual_weight": 45.0,
  "actual_rir": 3,
  "completed": true,
  "skipped": false,
  "substitution_for_planned_exercise_id": null,
  "notes": "Felt controlled."
}
```

Skip request example:

```json
{
  "planned_workout_exercise_id": 123,
  "exercise_name": "Goblet Squat",
  "set_number": null,
  "actual_reps": null,
  "actual_weight": null,
  "actual_rir": null,
  "completed": false,
  "skipped": true,
  "substitution_for_planned_exercise_id": null,
  "notes": "Skipped due to knee discomfort."
}
```

Substitution request example:

```json
{
  "planned_workout_exercise_id": 123,
  "exercise_name": "Leg Press",
  "set_number": 1,
  "actual_reps": 12,
  "actual_weight": 180.0,
  "actual_rir": 3,
  "completed": true,
  "skipped": false,
  "substitution_for_planned_exercise_id": 123,
  "notes": "Substituted because rack was unavailable."
}
```

### PATCH /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}

Updates a previously logged actual set.

Should support correcting:

- reps
- weight
- RIR
- notes
- completed/skipped state
- substitution fields

### POST /workout-plans/{plan_instance_id}/complete

Completes a started or in-progress plan.

Returns:

- workout_plan_instance
- execution_session
- planned_vs_actual_summary
- completed workout_session

### GET /workout-plans/{plan_instance_id}/planned-vs-actual

Returns comparison summary for a plan instance.

## Planned-vs-actual summary

A future planned-vs-actual summary should be computed from persisted planned rows and actual rows.

Suggested summary fields:

- planned_exercise_count
- completed_exercise_count
- skipped_exercise_count
- substituted_exercise_count
- planned_set_count
- completed_set_count
- completion_rate
- sets_above_planned_reps
- sets_below_planned_reps
- sets_inside_planned_reps
- sets_below_planned_rir
- sets_above_planned_rir
- average_actual_rir
- notes

Important interpretation rules:

- lower actual RIR than planned means higher effort than planned
- higher actual RIR than planned means easier effort than planned
- substitutions should count as completed work but should remain visible as substitutions
- skipped exercises should reduce completion rate but should not be treated as failure automatically
- planned-vs-actual should support coaching insight later, but should not trigger automatic progression changes in v1

## Relationship to existing manual workout logging

Manual workout logging must remain independent.

Existing manual logging should continue to create:

```text
workout_sessions
workout_sets
```

without requiring:

- workout_plan_instance_id
- workout_execution_session_id
- planned_workout_exercise_id

Planned execution logging should create or use a linked `workout_sessions` row so completed planned workouts appear in normal workout history.

The planned execution flow should not require users to use the plan preview system. Manual logging should remain a first-class workflow.

## Validation expectations

Future actual-set logging should validate:

- plan exists
- execution session exists
- plan belongs to the user
- plan status is `started` or `in_progress`
- actual set belongs to the selected plan instance
- planned exercise belongs to the selected plan instance
- actual reps are non-negative when provided
- actual weight is non-negative when provided
- actual RIR is in range when provided
- completed and skipped are not both true
- skipped rows do not require reps/weight/RIR
- completed rows should include enough actual data to be useful
- substitutions reference a valid planned exercise from the same plan

## Staged implementation plan

Recommended stages after this design:

1. Planned Workout Execution Logging Design v1
2. workout_execution_set_actuals schema v1
3. execution read endpoint
4. actual set log endpoint
5. transition started → in_progress on first actual log
6. update actual set endpoint
7. complete workout endpoint
8. planned-vs-actual summary endpoint
9. Streamlit actual-set logging UI
10. planned-vs-actual display UI

## Test strategy

Future tests should cover:

- started plan can read execution state
- actual set can be logged against a planned exercise
- first actual set transitions execution session to `in_progress`
- actual set can differ from planned reps/RIR without being rejected
- skipped planned exercise can be recorded
- substituted exercise can be recorded
- completed and skipped cannot both be true
- invalid RIR is rejected
- negative reps/weight are rejected
- actual set cannot reference a planned exercise from another plan
- complete endpoint updates plan and execution statuses
- planned-vs-actual summary counts completed, skipped, and substituted work correctly
- manual workout logging still works independently
- workout preview remains stateless
- selected/started plan records remain stable

Automated tests should not call CrewAI/Ollama.

## Non-goals

This design does not implement:

- actual set logging
- complete workout endpoint
- planned-vs-actual endpoint
- Streamlit actual-set UI
- CrewAI workout generation
- weekly periodization
- automatic progression engine
- recommendation-engine execution awareness
- replacement of manual workout logging
