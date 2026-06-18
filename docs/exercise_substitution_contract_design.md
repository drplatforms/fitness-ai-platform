# Exercise Substitution Contract Design

## Purpose

This document defines how a user should eventually substitute a planned workout exercise with a compatible catalog exercise without corrupting the immutable workout plan snapshot, planned-vs-actual summaries, workout history, TrainingExecutionSummary, or future recommendation logic.

The current system can preview a deterministic catalog-backed workout plan, select/start it, log actual performed sets, edit actual sets, complete a workout, display planned-vs-actual review data, and browse the exercise catalog in Streamlit. Actual performed substitutions can already be represented at the actual-set layer with `substitution_for_planned_exercise_id`, but there is not yet a formal contract for substituting a planned exercise before or during execution.

This is a design document only. It does not implement substitution APIs, Streamlit substitution UI, custom exercise creation, AI-driven substitutions, CrewAI workout generation, automatic progression, weekly periodization, nutrition changes, full-report changes, or recommendation behavior changes.

## Current stable flow

The current workout flow is:

```text
Exercise Catalog Seed
→ catalog-backed equipment metadata
→ deterministic workout preview exercise selection
→ equipment-profile filtering
→ movement-pattern variety tuning
→ optional accessory/core/conditioning slot
→ Streamlit Workout Plan Preview
→ POST /workout-plans/{user_id}/select
→ immutable ApprovedWorkoutPlan snapshot
→ planned_workout_exercises rows
→ POST /workout-plans/{plan_instance_id}/start
→ workout_execution_session
→ actual set logging/editing
→ planned-vs-actual summary
→ workout execution history
```

The current actual-set substitution representation is:

```text
workout_execution_set_actuals.substitution_for_planned_exercise_id
```

That field means the user performed `exercise_name` instead of the planned exercise referenced by `substitution_for_planned_exercise_id`.

## Design goals

1. Keep the original `ApprovedWorkoutPlan` snapshot immutable.
2. Preserve the original `planned_workout_exercises` rows.
3. Let users choose safe, equipment-compatible substitutions from the exercise catalog.
4. Prefer substitutions with the same movement pattern in v1.
5. Preserve both the originally planned exercise and the substituted exercise.
6. Keep planned-vs-actual summaries honest about substitutions without framing them as failure.
7. Keep manual workout logging independent.
8. Avoid automatic progression or coaching conclusions from substitutions until policy and validation are explicit.
9. Keep substitution behavior deterministic and backend-owned.
10. Avoid exposing raw actual-set notes or unbounded execution history to recommendation/LLM contexts.

## When substitutions should be allowed

### Before selecting a plan

Substitution before selection should not be a durable mutation in v1.

The preview endpoint is intentionally stateless. If a user wants different exercises before selecting a plan, the safer first step is to regenerate or adjust inputs such as equipment profile, restrictions, or preferences.

Future option:

```text
POST /workout-plans/preview/{user_id}/substitute
```

This could return a preview-only modified plan, but it should not persist anything unless the user selects the plan.

V1 recommendation:

- do not implement pre-selection durable substitutions
- keep `GET /workout-plans/preview/{user_id}` stateless
- use equipment/profile constraints to improve generated previews instead

### After selecting but before starting

This is the safest durable substitution window.

A selected plan has persisted `planned_workout_exercises`, but no actual execution has started. The user may know a planned exercise is unavailable, uncomfortable, or not preferred before beginning the session.

V1 recommendation:

- allow planned-exercise substitutions while plan status is `selected`
- record the substitution in a separate substitution layer
- do not mutate the original `ApprovedWorkoutPlan` JSON
- do not overwrite the original planned exercise row
- use the active substitution when rendering the execution view

Allowed example:

```text
Planned: Barbell Row
Substitute: Cable Row
Reason: equipment/fit preference
```

### During in_progress execution

Substitutions should be allowed during execution.

This supports real workout behavior: equipment is taken, fatigue changes, movement does not feel right, or the user intentionally swaps a movement while training.

V1 recommendation:

- allow substitutions during `started` or `in_progress`, with the first actual substitution moving the session to `in_progress` if needed
- record the planned-exercise substitution if it is selected before logging sets
- allow actual-set substitution rows to continue working for set-level/performed substitutions
- keep both layers compatible

For a during-execution substitution, the UI should ideally ask:

```text
Are you replacing this planned exercise for the rest of this workout?
```

If yes, create a planned-exercise substitution record. If no, log it as an actual-set substitution only.

### After completion as a correction

Completed-workout substitutions should be correction-only.

A user may complete a workout and later realize the wrong substitution was recorded. That should be correctable, but it should not silently rewrite history.

V1 recommendation:

- allow correction after completion only through the actual-set editing/correction flow or a future audited substitution correction endpoint
- preserve completed status and completed_at timestamps
- dynamically recompute planned-vs-actual summary after correction
- do not mutate the original plan snapshot
- eventually create audit rows for completed-workout substitution changes before recommendations consume them

## Immutable plan snapshot rule

The original `ApprovedWorkoutPlan` JSON on `workout_plan_instances` must remain immutable.

Reason:

- it records what the system originally approved
- it supports accountability for planned-vs-actual comparison
- it protects workout history from silent rewrites
- it lets future recommendation logic distinguish plan quality, equipment fit, and user choices

Do not update the original `approved_workout_plan_json` when a substitution is selected.

## Planned exercise immutability

Original `planned_workout_exercises` rows should remain immutable after selection.

Do not overwrite:

- name
- sets
- reps_min/reps_max
- rir_min/rir_max
- notes
- equipment_required_json

Instead, add a substitution layer that records the replacement.

This keeps the comparison clear:

```text
Originally planned: Dumbbell Split Squat
Substituted with: Goblet Squat
Performed sets: actual rows for Goblet Squat
```

## Proposed substitution table

Recommended future table:

```text
workout_plan_exercise_substitutions
```

Suggested fields:

- id
- workout_plan_instance_id
- workout_execution_session_id nullable
- planned_workout_exercise_id
- original_exercise_name
- substitute_exercise_catalog_id nullable
- substitute_exercise_name
- substitute_movement_pattern
- substitute_equipment_required_json
- substitution_reason
- source
- status
- created_at
- updated_at
- replaced_at nullable

Suggested `source` values:

- pre_start_selection
- in_progress_execution
- completed_correction
- api
- streamlit_ui

Suggested `status` values:

- active
- replaced
- voided

### Why a separate table

A separate table allows the system to:

- preserve original planned exercises
- preserve the approved plan snapshot
- record multiple substitution events over time
- support auditability later
- distinguish planned-exercise substitutions from actual-set substitutions
- keep planned-vs-actual summaries transparent

## Relationship to existing actual-set substitutions

The current actual-set field should remain supported:

```text
workout_execution_set_actuals.substitution_for_planned_exercise_id
```

That field is still useful when a substitution is only known at actual logging time.

Recommended interpretation:

- `workout_plan_exercise_substitutions` records a chosen replacement for a planned exercise.
- `workout_execution_set_actuals.substitution_for_planned_exercise_id` records what was actually performed instead of a planned exercise.

If a planned-exercise substitution exists and the user logs sets against it, the actual rows should still preserve the original planned exercise reference, either through:

- `substitution_for_planned_exercise_id`, or
- a future `workout_plan_exercise_substitution_id` field

Do not remove the current actual-set substitution mechanism.

## Planned-vs-actual comparison rule

Planned-vs-actual should preserve both the original plan and the substitution.

The summary should be able to answer:

1. What was originally planned?
2. What substitute was selected?
3. What was actually performed?
4. Was the substitution compatible by movement pattern and equipment?
5. Did the user complete the substituted work?

Recommended v1 summary behavior:

- count substitutions in `substituted_exercise_count`
- include a `substitutions_present` deviation flag
- do not count substitutions as skipped work if performed sets exist
- do not frame substitutions as poor adherence
- preserve the original planned exercise in developer/debug detail
- show user-facing language such as “Substituted Cable Row for Barbell Row”

Example summary detail:

```json
{
  "planned_exercise": "Barbell Row",
  "substituted_exercise": "Cable Row",
  "movement_pattern_match": true,
  "equipment_compatible": true,
  "completed_sets": 3
}
```

This detail should be bounded and structured. Do not pass raw notes or full actual-set rows into recommendation contexts.

## Movement-pattern compatibility

V1 substitutions should prefer the same movement pattern.

Examples:

- `horizontal_pull` → `horizontal_pull`
- `vertical_pull` → `vertical_pull`
- `horizontal_push` → `horizontal_push`
- `vertical_push` → `vertical_push`
- `hinge` → `hinge`
- `squat` → `squat`
- `lunge` → `lunge`
- `core_anti_extension` → `core_anti_extension`
- `core_anti_rotation` → `core_anti_rotation`
- `arms_biceps` → `arms_biceps`
- `arms_triceps` → `arms_triceps`
- `conditioning` → `conditioning`

### Compatible movement-pattern families

Some patterns may be allowed as same-family substitutions when exact matches are limited:

```text
lower_body_knee_dominant:
- squat
- lunge

upper_body_pull:
- horizontal_pull
- vertical_pull, only when acceptable for the plan context

core:
- core_anti_extension
- core_anti_rotation

arms:
- arms_biceps
- arms_triceps should not substitute for each other unless the planned slot is explicitly accessory/general arms
```

V1 recommendation:

- require exact movement-pattern match by default
- allow a small explicit compatibility map only where safe
- expose compatibility decisions in developer/debug context
- do not let arbitrary catalog exercises replace primary lifts

## Equipment compatibility

A substitute must be compatible with the user’s current equipment profile.

Validation should check the substitute exercise’s catalog equipment requirements against:

- `available_equipment`
- `unavailable_equipment`
- training environment
- movement restrictions when they exist later

Examples:

- A user without `adjustable_bench` should not substitute to Chest-Supported Dumbbell Row.
- A user without `ez_bar` and `plates` should not substitute to EZ-Bar Curl.
- A user without `pull_up_bar` should not substitute to Pull-Up or Band-Assisted Pull-Up.
- A user with `machine` unavailable should not substitute to machine-based exercises.

Do not trust client-submitted equipment metadata. The backend should load the substitute from the catalog and validate compatibility server-side.

## Catalog requirements

The replacement exercise should exist in the exercise catalog.

V1 substitution candidates should use catalog entries because the catalog owns:

- normalized exercise names
- equipment requirements
- movement pattern
- primary muscle groups
- exercise type/category
- difficulty

Do not allow custom exercise creation in the substitution contract v1.

Future custom exercises should have their own review/normalization flow before they are allowed as planned substitutions.

## API design, future only

### List substitution candidates

Recommended endpoint:

```text
GET /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitution-candidates
```

Response:

```json
{
  "success": true,
  "plan_instance_id": 123,
  "planned_exercise": {},
  "movement_pattern": "horizontal_pull",
  "equipment_profile": {},
  "candidates": [
    {
      "catalog_exercise_id": 17,
      "name": "Cable Row",
      "movement_pattern": "horizontal_pull",
      "equipment_required": ["cable"],
      "primary_muscle_groups": ["back"],
      "difficulty": "intermediate",
      "compatibility_reason_codes": ["same_movement_pattern", "equipment_available"]
    }
  ]
}
```

### Apply planned-exercise substitution

Recommended endpoint:

```text
POST /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitute
```

Request:

```json
{
  "substitute_exercise_catalog_id": 17,
  "substitution_reason": "Cable row is a better fit for today's setup."
}
```

Response:

```json
{
  "success": true,
  "substitution": {},
  "workout_plan_instance": {},
  "execution_session": {},
  "planned_exercises": [],
  "planned_vs_actual_summary": {}
}
```

### Void planned-exercise substitution

Recommended later endpoint:

```text
POST /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitution/void
```

This should preserve the substitution row with `status = voided` rather than deleting it.

## Status-specific rules

### selected

Allowed.

- create substitution row
- keep plan status selected
- do not create actual rows
- do not mutate original planned exercise
- update execution view to show substitute as active

### started

Allowed.

- create substitution row
- keep or transition session status depending on whether actual work is logged
- do not create actual rows unless user logs performed sets
- do not complete anything automatically

### in_progress

Allowed.

- create substitution row if replacing the planned exercise for remaining work
- actual rows may reference the original planned exercise as substituted
- planned-vs-actual summary should reflect substitutions dynamically

### completed

Correction-only.

- preserve completed status
- preserve completed_at timestamps
- require correction/audit metadata in a future audit milestone
- recompute planned-vs-actual summary dynamically

### abandoned/cancelled

Reject by default.

- do not allow normal substitutions
- future admin correction tools may support audited changes if needed

## User-facing display rules

Workout execution review should show substitutions clearly without blame.

Good wording:

```text
Substituted Cable Row for Barbell Row.
```

```text
Substitution used: Dumbbell RDL instead of Conventional Deadlift.
```

```text
This substitution keeps the same movement pattern and matches your available equipment.
```

Avoid wording:

```text
You failed to complete Barbell Row.
```

```text
Poor adherence: substituted exercise.
```

```text
The plan was ineffective because you substituted exercises.
```

## Recommendation and TrainingExecutionSummary behavior

Substitutions should eventually inform TrainingExecutionSummary as plan-fit signals, not failure signals.

Allowed future interpretation:

- repeated substitutions may suggest reviewing plan fit
- repeated substitutions may suggest reviewing equipment fit
- repeated substitutions may suggest the generated plan should better match preferences

Forbidden interpretation:

- substitutions prove poor adherence
- substitutions prove lack of discipline
- substitutions prove failed programming
- one substitution proves the plan is bad
- substitutions require automatic deload
- substitutions require automatic progression

Before substitutions influence recommendations, validators must enforce the execution-aware policy already established in `docs/execution_aware_recommendation_policy.md`.

## How substitutions should appear in history

Workout history should preserve substitutions in a readable way.

Recommended fields for history/detail responses:

- original_planned_exercise_name
- substituted_exercise_name
- substitution_source
- substitution_reason, bounded and sanitized if exposed
- movement_pattern_match
- equipment_compatible
- completed_set_count

Do not expose raw actual-set notes broadly.

## Validation rules

Future substitution APIs should validate:

1. plan exists
2. planned exercise belongs to the plan
3. plan status allows substitution
4. replacement exercise exists in the catalog
5. replacement exercise equipment is compatible with current equipment profile
6. replacement exercise is not machine-only when machine is unavailable
7. replacement movement pattern matches or is explicitly compatible
8. original planned exercise remains immutable
9. ApprovedWorkoutPlan JSON remains immutable
10. substitution reason is optional but length-bounded
11. completed workouts require correction/audit metadata when changed
12. abandoned/cancelled plans reject substitutions by default
13. substitution is recorded as plan-fit/equipment-fit context, not failure/adherence context

## Staged implementation plan

### Stage 1 — Design

Current milestone.

- document substitution contract
- do not implement APIs or UI

### Stage 2 — Candidate lookup service

Add a backend service that returns compatible catalog substitutions for a planned exercise.

Potential function:

```python
get_substitution_candidates(plan_instance_id: int, planned_exercise_id: int)
```

This service should:

- load the plan and planned exercise
- load current equipment profile
- filter catalog by movement pattern and compatible equipment
- return bounded candidate metadata
- include reason codes

### Stage 3 — Substitution persistence schema

Add `workout_plan_exercise_substitutions`.

Do not mutate existing planned exercises.

### Stage 4 — Apply substitution endpoint

Add `POST /workout-plans/{plan_instance_id}/planned-exercises/{planned_exercise_id}/substitute`.

Keep response bounded and include updated execution state.

### Stage 5 — Streamlit substitution UI

Add UI inside Workout Plan Preview / Execution View:

- “Find substitute” button
- candidate list
- select substitute
- show original and replacement

### Stage 6 — Planned-vs-actual and history display polish

Ensure summaries/history show original and substitute clearly.

### Stage 7 — TrainingExecutionSummary integration

Only after validation, aggregate substitution frequency as plan-fit/equipment-fit context.

### Stage 8 — Recommendation awareness

Only after the execution-aware policy and validation are extended, allow limited user-facing copy such as:

```text
Recent substitutions may suggest reviewing exercise fit or equipment fit before increasing training demand.
```

## Test strategy

Future implementation tests should cover:

- substitution candidates require same movement pattern by default
- compatible movement family mappings are explicit
- candidates require compatible available equipment
- machine substitutions are excluded when machine is unavailable
- selected plan can apply substitution
- started plan can apply substitution
- in_progress plan can apply substitution
- completed plan substitution correction preserves completed status and timestamps
- abandoned/cancelled plans reject substitutions
- original `ApprovedWorkoutPlan` JSON remains unchanged
- original `planned_workout_exercises` row remains unchanged
- planned-vs-actual summary counts substitutions without marking poor adherence
- actual-set substitution behavior remains compatible
- workout history displays original and substitute
- TrainingExecutionSummary treats substitutions as plan-fit context, not failure
- /recommendations/daily/{user_id} remains stable until explicitly changed
- Streamlit remains unchanged until UI milestone

## Non-goals

This design does not add:

- substitution endpoints
- substitution database table
- Streamlit substitution UI
- custom exercise creation
- automatic AI substitutions
- CrewAI workout generation
- automatic progression
- weekly periodization
- nutrition changes
- full report changes
- recommendation behavior changes
- workout execution flow redesign

## Recommended next milestone

After this design is accepted, the next implementation milestone should be:

```text
Exercise Substitution Candidate Service v1
```

Suggested scope:

- add read-only substitution candidate service
- use exercise catalog metadata
- filter by movement pattern and equipment profile
- do not persist substitutions yet
- add tests for compatible candidates and unavailable equipment filtering
