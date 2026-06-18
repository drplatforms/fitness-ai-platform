# Exercise Substitution Apply Design

## Purpose

This document defines how a user should eventually apply a compatible exercise substitution to a selected, started, or in-progress planned workout without corrupting immutable plan snapshots, planned-vs-actual summaries, workout history, `TrainingExecutionSummary`, or future recommendation logic.

The current system can preview catalog-backed workout plans, select and start a plan, log actual sets, edit actual sets, complete workouts, view history, browse the exercise catalog, and request read-only substitution candidates for a planned exercise. The next implementation step should not overwrite the original plan. It should record the user's chosen replacement as a separate execution/planning adaptation.

This is a design document only. It does not implement substitution persistence, apply-substitution endpoints, Streamlit apply buttons, automatic substitutions, CrewAI workout generation, automatic progression, or recommendation behavior changes.

## Current accepted architecture

The current workout/catalog/substitution flow is:

```text
Exercise Catalog Seed v1
→ catalog-backed equipment metadata
→ deterministic workout preview exercise selection
→ equipment-profile filtering
→ movement-pattern variety tuning
→ optional accessory/core/conditioning slot
→ Exercise Catalog visibility/search in Streamlit
→ Exercise Substitution Contract Design v1
→ Exercise Substitution Candidate Service v1
→ read-only substitution candidates
→ Select/Start/Actual Set Logging/Editing/Completion/History flows remain stable
```

The existing design decisions remain in force:

- `ApprovedWorkoutPlan` JSON snapshots are immutable.
- Original `planned_workout_exercises` should be preserved.
- Candidate lookup is read-only.
- Replacement exercises must come from the exercise catalog.
- Replacement exercises must be compatible with the current equipment profile at the time the substitution is applied.
- Same movement pattern should be preferred for v1.
- Actual-set substitution fields should remain compatible with the planned substitution layer.
- Substitutions should be framed as plan-fit, equipment-fit, preference, or execution adaptation, not failure.

## Lifecycle decision

### Before plan selection

Substitution should not be durably applied before a workout plan is selected.

A preview is stateless and should stay stateless. Before selection, users may eventually request alternative preview candidates, regenerate a preview, or inspect compatible substitutions, but this should not create substitution records.

Allowed future behavior:

```text
previewed plan
→ user views candidates
→ no durable record yet
```

Non-goal for v1:

```text
previewed plan
→ persisted substitution
```

### Selected but not started

Substitution should be allowed after the plan is selected and before it is started.

This is the cleanest v1 use case because the user has committed to a specific plan instance, but execution has not begun. Applying a substitution here should create a durable substitution record linked to the selected plan instance and planned exercise.

Allowed v1 behavior:

```text
selected plan instance
→ apply substitution
→ substitution record created
→ original planned exercise remains unchanged
→ effective exercise for execution becomes replacement
```

### Started but not in-progress

Substitution should be allowed after start and before actual sets are logged.

This supports realistic training behavior: a user may start a session, then realize an exercise is not practical or equipment is unavailable. Applying a substitution should still be recorded separately without mutating the original plan.

Allowed v1 behavior:

```text
started plan instance
→ apply substitution
→ substitution record created
→ execution remains started until actual sets are logged
```

### In-progress execution

Substitution should be allowed during an in-progress workout.

This supports real execution scenarios such as occupied equipment, joint discomfort, preference changes, or equipment mismatch discovered mid-session. Applying a substitution during execution should affect subsequent actual-set logging for that planned exercise, but it should not rewrite already logged actual sets automatically.

Allowed v1 behavior:

```text
in_progress plan instance
→ apply substitution
→ substitution record created/updated
→ future actual-set logging can default to replacement exercise
→ existing actual-set rows remain unchanged unless separately edited
```

If actual sets already exist for the original planned exercise, the system should not silently rewrite them. A future UI can warn the user that previous logged sets will remain as originally logged unless corrected.

### Completed workouts

Applying a new substitution to a completed workout should not be part of v1.

Completed-plan substitution changes are correction/audit behavior and need stricter rules. They can affect historical displays and dynamic planned-vs-actual summaries, so they should wait until a correction/audit strategy exists.

Recommended v1 behavior:

```text
completed plan instance
→ reject apply-substitution
```

Future correction behavior may allow completed substitution edits if:

- completed status is preserved,
- completed timestamps are preserved,
- original planned exercise remains immutable,
- a correction/audit field is recorded,
- dynamic summaries recompute safely,
- history shows the correction clearly.

### Abandoned or cancelled workouts

Substitutions should be rejected for abandoned or cancelled plans in v1.

These states are not active execution contexts, and allowing substitutions would create ambiguous history.

## Immutability rules

### ApprovedWorkoutPlan JSON

`approved_workout_plan_json` must remain immutable.

It represents what the backend approved at selection time. Substitutions are user execution adaptations, not a rewrite of the originally approved plan.

Do not:

- rewrite the approved plan JSON,
- replace exercise names inside the approved plan JSON,
- remove original exercises from the approved plan snapshot,
- re-run workout generation during apply-substitution.

### planned_workout_exercises

Original `planned_workout_exercises` rows should remain immutable for v1.

They should continue to represent the originally selected plan. A substitution layer should describe the active replacement.

Do not:

- overwrite `planned_workout_exercises.exercise_name`,
- overwrite planned reps or RIR,
- delete the original planned exercise,
- mark the original row as replaced by mutation alone.

## Recommended persistence model

Add a separate future table:

```text
workout_plan_exercise_substitutions
```

Recommended fields:

```text
id
workout_plan_instance_id
workout_execution_session_id
planned_workout_exercise_id
original_exercise_name
replacement_exercise_name
replacement_catalog_exercise_id
original_movement_pattern
replacement_movement_pattern
substitution_reason
status
created_at
updated_at
```

Optional later fields:

```text
created_by
source
equipment_profile_snapshot_json
replacement_required_equipment_json
notes
voided_at
void_reason
previous_substitution_id
```

### Status values

Recommended v1 statuses:

```text
active
replaced
cancelled
```

For v1, the simplest implementation may enforce one active substitution per planned exercise:

```text
unique active substitution per plan_instance_id + planned_workout_exercise_id
```

If a user changes a substitution before completing the workout, the old substitution can be marked `replaced` and the new one marked `active`, or v1 can update the existing row while preserving `updated_at`.

A full audit trail can come later.

## Apply-substitution endpoint design

Recommended future endpoint:

```text
POST /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitute
```

Suggested request body:

```json
{
  "replacement_catalog_exercise_id": 123,
  "substitution_reason": "equipment_unavailable"
}
```

Possible substitution reasons:

```text
equipment_unavailable
preference
movement_comfort
fatigue_management
exercise_too_difficult
exercise_too_easy
time_constraint
other
```

Suggested response:

```json
{
  "success": true,
  "workout_plan_instance": {},
  "execution_session": {},
  "planned_exercise": {},
  "substitution": {},
  "effective_exercise": {},
  "substitution_candidates": []
}
```

The response may optionally include refreshed candidates for the same planned exercise, but it should not expose raw actual-set rows unless this endpoint explicitly needs execution context later.

## Apply-substitution validation

The apply operation should validate all of the following.

### Plan validation

- `workout_plan_instance` exists.
- Plan status is one of:
  - `selected`
  - `started`
  - `in_progress`
- Plan status is not one of:
  - `completed`
  - `abandoned`
  - `cancelled`
- Execution session exists when the plan has been selected through the normal flow.

### Planned exercise validation

- `planned_workout_exercise_id` exists.
- Planned exercise belongs to the given plan instance.
- Planned exercise has not been removed.
- Planned exercise can be matched to a catalog entry or has enough metadata to determine movement pattern.

### Replacement validation

- Replacement exercise exists in the exercise catalog.
- Replacement exercise is active/seeded/valid.
- Replacement required equipment is compatible with the current equipment profile.
- Replacement does not require unavailable equipment.
- Replacement does not require `machine` when machine is unavailable.
- Replacement does not require `adjustable_bench` when adjustable bench is unavailable.
- Replacement does not require barbell/rack/plates/cable/pull-up bar/bike/treadmill when unavailable.
- Replacement is the same movement pattern or an explicitly approved compatible movement family.
- Replacement is not the same exercise as the original unless v1 chooses to treat that as a no-op.

### Movement-pattern compatibility

Default v1 rule:

```text
replacement_movement_pattern == original_movement_pattern
```

Approved compatible movement families may be allowed when explicitly defined, such as:

```text
squat ↔ lunge
horizontal_pull ↔ vertical_pull only if intentionally allowed for back/pull substitution
core_anti_extension ↔ core_anti_rotation only for core/accessory slots
conditioning ↔ conditioning
arms_biceps ↔ arms_biceps
arms_triceps ↔ arms_triceps
```

The default should be strict. Broader movement swaps should not happen accidentally.

### Equipment compatibility source of truth

The backend should load the current equipment profile at apply time.

Do not trust client-submitted equipment metadata.

Do not trust the frontend to determine compatibility.

Do not assume catalog metadata from the request body.

### Equipment profile changes after substitution

If the equipment profile changes after a substitution is applied, the existing substitution should remain as historical context for that plan instance.

Recommended v1 behavior:

- Validate equipment compatibility at apply time.
- Do not automatically invalidate old substitutions when profile changes.
- Future execution views may show a warning if a currently active substitution no longer matches the latest equipment profile.
- Future apply/reapply operations should use the latest equipment profile.

This preserves history and avoids silently rewriting completed or in-progress workouts.

## Relationship to actual-set logging

The existing actual-set layer already supports substitution-like behavior through `substitution_for_planned_exercise_id`.

The planned substitution layer should make actual-set logging easier but not replace actual-set truth.

Recommended behavior:

- If an active planned substitution exists for a planned exercise, actual-set logging UI/API may default `exercise_name` to the replacement exercise.
- Actual-set rows should still reference the original `planned_workout_exercise_id`.
- Actual-set rows may also use existing substitution fields to indicate the original planned exercise was substituted.
- Existing actual-set substitution behavior should remain valid for ad hoc substitutions that happen during set logging.

Future actual-set payload behavior may include:

```json
{
  "planned_workout_exercise_id": 456,
  "exercise_name": "Cable Row",
  "substitution_for_planned_exercise_id": 456,
  "actual_reps": 10,
  "actual_weight": 80,
  "actual_rir": 2,
  "completed": true
}
```

The planned substitution record explains the intended replacement; actual-set rows record what was actually performed.

## Planned-vs-actual summary behavior

Planned-vs-actual summaries should preserve both original and substituted exercise context.

Recommended behavior:

- Planned exercise count remains based on original `planned_workout_exercises`.
- Substitution count includes active planned substitutions and/or actual-set substitutions, depending on the final implementation.
- Summary should show original planned exercise and replacement exercise.
- Completion percentage should still be based on actual completion/skips against planned exercise slots.
- Substitutions should not reduce completion percentage by themselves.
- Substitutions should not be treated as skipped exercises.
- Substitutions should not be treated as failed workouts.
- Repeated substitutions can become a future plan-fit review signal.

Example display concept:

```text
Planned: Barbell Row
Substituted: Cable Row
Completed: 3 sets
```

For v1, if a substitution is applied but no actual sets are logged, the summary may count it as a substitution but not as completed work.

## Workout history display

Workout history should make substitutions clear without implying failure.

Allowed display language:

```text
Substituted Cable Row for Barbell Row.
Used Cable Row in place of Barbell Row.
Replacement exercise: Cable Row.
```

Avoid language like:

```text
Failed Barbell Row.
Did not adhere to plan.
Plan was ineffective.
User skipped Barbell Row because of poor discipline.
```

History should preserve:

- original planned exercise,
- replacement exercise,
- completion/skipped status,
- actual reps/weight/RIR,
- substitution reason if available.

## TrainingExecutionSummary behavior

`TrainingExecutionSummary` should eventually count applied substitutions in a conservative way.

Allowed future interpretation:

```text
Repeated substitutions may suggest reviewing plan fit, equipment fit, or exercise preferences.
```

Forbidden interpretation:

```text
Substitutions prove poor adherence.
Substitutions prove the plan failed.
Substitutions prove the user lacks discipline.
One substitution means programming is bad.
```

Recommended future fields or reason codes:

```text
substituted_exercise_count
substitutions_present
repeated_substitutions_present
plan_fit_review_signal
equipment_fit_review_signal
```

Substitution counts should not automatically change:

- `execution_quality`,
- `CoachingDecision.scenario`,
- progression readiness,
- deload logic,
- recovery diagnosis.

## Recommendation behavior

Do not change recommendation behavior in the apply-substitution v1 implementation.

Future recommendation behavior may mention repeated substitutions only after:

- substitution persistence exists,
- planned-vs-actual summary behavior is stable,
- `TrainingExecutionSummary` includes substitution counts,
- execution-aware recommendation validation supports the wording,
- QA confirms wording is not judgmental.

Allowed future wording:

```text
Recent substitutions may be worth reviewing for plan fit or equipment fit.
```

Forbidden future wording:

```text
You failed to follow the plan.
Your adherence is poor.
The workout plan is bad.
Substitutions caused stalled progress.
```

## Revert/change substitution behavior

V1 should support either:

1. one active substitution that can be replaced by another active substitution, or
2. a simple delete/cancel behavior before completion.

Recommended safer direction:

- Do not hard-delete substitution rows.
- Mark old rows as `replaced` or `cancelled`.
- Preserve `updated_at`.
- Avoid audit-heavy complexity until correction flows are designed.

For v1, if full audit is too much, updating the active row is acceptable only before completion, but the design should not require mutating the original planned exercise.

## Non-goals

Do not implement in this design milestone:

- apply-substitution endpoint,
- substitution persistence table,
- Streamlit apply button,
- custom exercise creation,
- automatic AI substitutions,
- CrewAI workout generation,
- automatic progression,
- weekly periodization,
- nutrition changes,
- report changes,
- recommendation behavior changes,
- completed-workout correction/audit flow,
- exercise media,
- autocomplete.

## Recommended staged implementation

### 1. Exercise Substitution Apply Design v1

This document.

### 2. Exercise Substitution Persistence Schema v1

Add `workout_plan_exercise_substitutions` table/model and read helpers.

No apply endpoint yet if risk is high.

### 3. Apply Substitution Endpoint v1

Add:

```text
POST /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitute
```

Support `selected`, `started`, and `in_progress`.

Reject `completed`, `abandoned`, and `cancelled`.

### 4. Execution State Integration v1

Show effective exercise in execution state while preserving original planned exercise.

Actual-set logging can default to replacement exercise.

### 5. Planned-vs-Actual Summary Integration v1

Count applied substitutions and display original/replacement exercise pairs.

### 6. Streamlit Apply Substitution UI v1

Add user-facing apply button once backend behavior is stable.

### 7. TrainingExecutionSummary Integration v1

Count applied substitutions conservatively as plan-fit/equipment-fit signals.

### 8. Recommendation Policy Expansion v1

Only after repeated-substitution behavior is stable, consider limited recommendation wording.

## Test strategy for future implementation

Required tests before apply-substitution behavior is accepted:

- selected plan can apply compatible substitution,
- started plan can apply compatible substitution,
- in_progress plan can apply compatible substitution,
- completed plan rejects apply-substitution,
- abandoned/cancelled plan rejects apply-substitution,
- planned exercise from another plan is rejected,
- replacement exercise missing from catalog is rejected,
- replacement exercise requiring unavailable equipment is rejected,
- machine replacement is rejected when machine unavailable,
- adjustable-bench replacement is rejected when adjustable bench unavailable,
- same movement-pattern replacement is allowed,
- incompatible movement-pattern replacement is rejected unless explicitly compatible,
- `ApprovedWorkoutPlan` JSON remains unchanged,
- original `planned_workout_exercises` row remains unchanged,
- substitution row records original and replacement exercise,
- actual-set logging can still work after substitution,
- planned-vs-actual summary preserves original and replacement context,
- substitution does not imply skipped exercise by itself,
- substitution does not reduce completion percentage by itself,
- workout history displays substitution without failure/adherence wording,
- `TrainingExecutionSummary` remains stable until explicitly integrated,
- `/recommendations/daily/{user_id}` remains stable,
- full report behavior remains stable,
- Streamlit behavior remains stable until UI implementation begins.
