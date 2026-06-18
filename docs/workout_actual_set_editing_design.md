# Workout Actual-Set Editing and Correction Flow Design

## Purpose

This document defines how users should eventually correct logged actual sets for a planned workout execution without corrupting completed workout history, planned-vs-actual summaries, manual workout logging, or future recommendation logic.

The current system can preview, select, start, log actual performed sets, complete a planned workout, expose planned-vs-actual summaries, and display workout execution history. Actual performed sets are stored in `workout_execution_set_actuals`, while manual workout logging remains independent.

This is a design document only. It does not implement actual-set editing, voiding, Streamlit edit UI, workout-set mirroring, recommendation-engine execution awareness, CrewAI workout generation, weekly periodization, or automatic progression.

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
→ POST /workout-plans/{plan_instance_id}/complete
→ workout_plan_instance.status completed
→ workout_execution_session.status completed
→ planned_vs_actual_summary returned/displayed
→ GET /workout-plans/history/{user_id}
→ execution history displayed
```

The existing read-only summary endpoint is:

```text
GET /workout-plans/{plan_instance_id}/planned-vs-actual
```

The summary is dynamically recomputed from:

- `planned_workout_exercises`
- `workout_execution_set_actuals`

Summary snapshots are not persisted in v1.

## Design principles

1. In-progress actual sets should be correctable without ceremony.
2. Completed workout actual sets may be corrected, but the system should preserve a correction trail before those corrections influence broader coaching logic.
3. Planned-vs-actual summaries should remain dynamically recomputed after corrections.
4. Actual-set corrections should not mutate the original `ApprovedWorkoutPlan` snapshot.
5. Planned exercise rows should remain immutable once selected.
6. Manual workout logging should remain independent.
7. Avoid hard deletes; prefer voiding actual rows.
8. Skipped, substituted, and completed states should remain explicit.
9. A correction should never silently change a workout execution status from completed back to in_progress.
10. Recommendation-engine awareness should wait until correction semantics are stable and auditable.

## Can actual sets be edited while the workout is in_progress?

Yes.

In-progress actual-set edits should be supported first because they are the lowest-risk correction path. A user may need to fix:

- actual reps
- actual weight
- actual RIR
- set notes
- accidental skipped/completed state
- substitution metadata
- exercise name for a substitution

Recommended v1 behavior:

- allow direct `PATCH` updates while plan/session status is `in_progress`
- validate the updated row using the same rules used for actual-set creation
- update `updated_at`
- keep the execution status as `in_progress`
- dynamically reflect corrections in `/planned-vs-actual` and history summaries

The correction should not create a new workout session or planned exercise row.

## Can actual sets be edited after workout completion?

Yes, but completed-workout corrections should be more intentional than in-progress edits.

Recommended policy:

- allow correction of completed workouts
- keep `workout_plan_instance.status = completed`
- keep `workout_execution_session.status = completed`
- keep original `completed_at` timestamps
- recompute planned-vs-actual summaries dynamically after correction
- require a correction note/reason once an edit occurs after completion, or add that requirement in the first audit-trail milestone

Reason:

Completed workouts often need typo fixes. Preventing all correction would make history brittle. But silent completed-workout mutation can distort future adherence, progression, and recommendation logic. The system should support correction while making the fact of correction visible internally.

## Should planned-vs-actual summary dynamically update after completed edits?

Yes.

The accepted architecture already makes `WorkoutPlannedVsActualSummary` a dynamic read-only layer over persisted planned rows and actual rows. That should continue.

If a completed workout actual set is corrected:

- `/planned-vs-actual` should reflect the corrected actual data
- workout execution history should reflect the corrected summary
- the completed status should not change
- completed timestamps should not change
- future audit metadata should indicate that completed workout actuals were edited after completion

Do not persist summary snapshots yet.

## Hard updates vs audit trail

### Recommended staged approach

Use two layers:

1. **V1 correction behavior:** update the actual-set row in place and refresh `updated_at`.
2. **Future audit behavior:** add an audit table before using corrected execution summaries for recommendations, progression, or long-term coaching decisions.

This keeps the first editing implementation small while preserving the architecture path for safer correction history.

### Future audit table

Potential table:

```text
workout_execution_set_actual_revisions
```

Suggested fields:

- id
- workout_execution_set_actual_id
- workout_execution_session_id
- plan_instance_id
- changed_at
- changed_by_user_id
- changed_after_completion
- previous_values_json
- new_values_json
- correction_reason
- source

Suggested `source` values:

- streamlit_ui
- api
- migration
- admin_tool

Audit rows should be created for completed-workout edits before recommendation logic consumes execution summaries.

## Should skipped rows be editable back into completed rows?

Yes.

A user may accidentally mark a planned exercise or set as skipped, then correct it after realizing they performed it.

Recommended behavior:

- allow `skipped: false` and `completed: true`
- require enough actual data for a completed row, at minimum actual reps and actual RIR under current validation policy
- allow actual weight to be zero for bodyweight or unloaded movements
- preserve the same actual-set row id
- update `updated_at`
- recompute the summary dynamically

If the row was skipped as an exercise-level placeholder rather than a set-level actual, the UI should make the correction clear and ask for performed set details.

## Should completed rows be editable into skipped rows?

Yes, but it should be intentional.

A completed row may represent an accidental log. The user should be able to correct it into a skipped row.

Recommended behavior:

- allow `completed: false` and `skipped: true`
- clear or ignore actual reps/weight/RIR for summary calculations
- preserve notes and allow a skip reason in notes
- preserve row id
- update `updated_at`
- dynamically reduce completed set counts and completion percentage

The API should continue to reject `completed: true` and `skipped: true` together.

## How should substitutions be corrected?

Substitution corrections should preserve both the planned intent and the performed exercise.

A normal planned set uses:

- `planned_workout_exercise_id`
- `exercise_name` matching the planned exercise
- `substitution_for_planned_exercise_id = null`

A substitution should use:

- `planned_workout_exercise_id = null` or the planned exercise id only if the implementation intentionally uses it as the replaced plan reference
- `substitution_for_planned_exercise_id` pointing to the planned exercise being replaced
- `exercise_name` containing the performed substitute exercise

Recommended v1 rule:

- use `substitution_for_planned_exercise_id` as the authoritative planned exercise being replaced
- require it to belong to the same plan instance
- allow `exercise_name` to differ from the planned exercise name
- count substitution rows in `substituted_exercise_count`

Correction examples:

1. Substitute was logged against the wrong planned exercise.
   - update `substitution_for_planned_exercise_id`
   - verify the new planned exercise belongs to the same plan

2. Substitute exercise name was wrong.
   - update `exercise_name`
   - preserve substitution pointer

3. Substitute should have been normal planned work.
   - clear `substitution_for_planned_exercise_id`
   - populate `planned_workout_exercise_id`
   - set `exercise_name` to the planned exercise or the corrected performed name

4. Normal planned row should have been a substitution.
   - clear or reinterpret `planned_workout_exercise_id`
   - set `substitution_for_planned_exercise_id`
   - set performed `exercise_name`

The summary should dynamically update substitution counts.

## Should deleting an actual set be allowed?

Hard delete should not be the default.

Recommended future endpoint:

```text
POST /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}/void
```

Void behavior should:

- mark the row as voided/deleted instead of deleting it
- exclude voided rows from planned-vs-actual summary calculations
- preserve the row for audit/debug history
- require a reason after completion, or for all voids if simple enough
- leave plan/session status unchanged

Potential future fields on `workout_execution_set_actuals`:

- voided
- voided_at
- void_reason
- voided_by_user_id

Potential alternative:

```text
DELETE /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}
```

If `DELETE` is exposed, it should still perform a soft delete/void internally. Avoid physical deletion except for test cleanup, migrations, or admin-only maintenance.

## How should correction affect execution status?

### selected

Selected plans should not have actual-set rows. Editing actual sets should be rejected because execution has not started.

### started

Started plans usually have no actual-set rows. If a row exists due to a partial/inconsistent state, editing should either:

- reject and require plan to be `in_progress`, or
- transition to `in_progress` if the row becomes a completed/skip/substitution row

Recommended v1 behavior: reject started-state edits unless actual-set logging has already transitioned the plan/session to `in_progress`.

### in_progress

Edits are allowed. Status remains `in_progress`.

### completed

Edits are allowed as corrections. Status remains `completed`; `completed_at` remains unchanged. Summary recomputes dynamically.

### abandoned/cancelled

Edits should be rejected by default. If later supported, they should require explicit restore/reopen behavior first.

## Should manual workout logging correction remain separate?

Yes.

Manual workout logging and planned workout execution should remain separate workflows.

Manual correction should apply to:

- `workout_sessions`
- `workout_sets`

Planned execution correction should apply to:

- `workout_execution_set_actuals`

Do not couple planned actual-set editing to manual workout-set editing until a deliberate mirroring/linking milestone is approved.

If `workout_execution_set_actuals.workout_set_id` is populated later, edits need a synchronization policy:

- execution actual edits update mirrored `workout_sets`, or
- mirrored workout sets are read-only projections, or
- execution actuals remain source of truth for planned-vs-actual while workout_sets remain general history

Recommended current position: no mirroring yet.

## Future API shape

Recommended future endpoints:

```text
PATCH /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}
POST /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}/void
```

Potential request shape for `PATCH`:

```json
{
  "planned_workout_exercise_id": 12,
  "exercise_name": "Goblet Squat",
  "set_number": 1,
  "actual_reps": 10,
  "actual_weight": 35,
  "actual_rir": 3,
  "completed": true,
  "skipped": false,
  "substitution_for_planned_exercise_id": null,
  "notes": "Corrected reps from 8 to 10.",
  "correction_reason": "Typo during logging."
}
```

Potential request shape for `void`:

```json
{
  "void_reason": "Duplicate set logged accidentally."
}
```

Recommended response shape:

```json
{
  "success": true,
  "actual_set": {},
  "workout_plan_instance": {},
  "execution_session": {},
  "planned_vs_actual_summary": {}
}
```

Returning the dynamic summary helps the UI refresh immediately without a second request, but the source of truth should remain the actual-set rows.

## Validation rules

Editing should reuse existing actual-set creation validation where possible.

Recommended validation:

- plan exists
- execution session exists
- actual set exists
- actual set belongs to the plan's execution session
- plan status is `in_progress` or `completed`
- execution session status is `in_progress` or `completed`
- selected plans cannot edit actual sets
- abandoned/cancelled plans cannot edit actual sets by default
- `planned_workout_exercise_id`, when provided, belongs to the plan
- `substitution_for_planned_exercise_id`, when provided, belongs to the plan
- `completed` and `skipped` cannot both be true
- skipped rows do not require reps/weight/RIR
- completed rows require enough useful actual data
- actual reps must be non-negative when provided
- actual weight must be non-negative when provided
- actual RIR must be between 0 and 10 when provided
- set number must be positive when provided
- completed-workout edits should preserve completed status and completed timestamps

## Planned-vs-actual summary behavior after corrections

Because summaries are dynamic, corrections should immediately affect:

- completed set count
- skipped set count
- actual set count
- completion percentage
- average actual RIR
- RIR deviation
- rep deviation
- missing_actual_rir flag
- missing_actual_reps flag
- skipped_exercises_present flag
- substitutions_present flag
- incomplete_logging flag

Voided rows, once supported, should be excluded from summary calculations and may add a future flag such as:

- voided_actual_sets_present

Completed workout summaries should be allowed to change after corrections. This is acceptable because v1 summary is descriptive only and not yet used for automatic progression or recommendation logic.

## Streamlit sequencing

Do not add Streamlit edit UI until the API contract is accepted.

Recommended future UI sequence:

1. Read-only execution review remains stable.
2. Add simple edit controls for in-progress actual sets.
3. Add completed-workout correction controls behind an explicit “Correct completed workout” expander.
4. Add void duplicate set action.
5. Refresh planned-vs-actual summary after every correction.

Completed-workout correction UI should communicate that corrections update the summary.

## Recommendation-engine awareness

Do not feed edited execution summaries into recommendation logic yet.

Recommended order:

1. Actual-set editing contract.
2. Actual-set editing API.
3. Actual-set editing UI.
4. Audit trail or voiding support.
5. Stable planned-vs-actual history.
6. Only then consider recommendation-engine execution awareness.

Reason:

Recommendation logic should not consume correction-sensitive execution data until edit, void, and audit semantics are stable.

## Testing strategy

Future tests should cover:

- in_progress actual set can be edited
- completed actual set can be corrected without changing completed status
- completed_at timestamps are preserved after correction
- selected plan actual-set edit is rejected
- abandoned plan actual-set edit is rejected
- actual set from another plan is rejected
- planned exercise from another plan is rejected
- substitution pointer from another plan is rejected
- completed row can become skipped
- skipped row can become completed when required actual data is provided
- completed and skipped together is rejected
- invalid actual RIR is rejected
- negative actual reps are rejected
- negative actual weight is rejected
- hard delete is not used for user-facing correction
- voided row is excluded from summary once voiding exists
- planned-vs-actual summary updates after correction
- manual workout logging remains independent
- preview/select/start/actual-set/complete/history flows remain stable
- `/recommendations/daily/{user_id}` remains stable
- full report safety path remains stable

Automated tests should not call CrewAI/Ollama.

## Non-goals

This design does not implement:

- actual-set edit endpoint
- actual-set void endpoint
- actual-set audit table
- Streamlit actual-set edit UI
- recommendation-engine execution awareness
- automatic progression engine
- workout_sets mirroring
- CrewAI workout generation
- weekly periodization
- manual workout logging correction

## Recommended next implementation milestone

If Architecture accepts this design, the next narrow implementation milestone should be:

```text
Actual-Set Editing API v1
```

Suggested scope:

- add `PATCH /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}`
- allow edits for `in_progress` and `completed` workout executions
- preserve completed status and completed timestamps
- recompute planned-vs-actual summary dynamically
- do not add void endpoint yet unless Architecture wants it bundled
- do not add Streamlit edit UI yet
- keep manual workout logging independent
