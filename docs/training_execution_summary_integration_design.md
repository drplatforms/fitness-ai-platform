# TrainingExecutionSummary Integration Design

## Purpose

This document defines how `TrainingExecutionSummary` should enter the coaching pipeline without prematurely changing daily recommendations, full AI Health Reports, automatic progression, workout programming, or CrewAI behavior.

`TrainingExecutionSummary` is already a conservative, read-only contract over completed planned workout executions. It summarizes recent completed `WorkoutPlannedVsActualSummary` records and intentionally does not read manual workout logs for planned-vs-actual conclusions.

This is a design document only. It does not implement code changes, model changes, route changes, recommendation changes, report changes, Streamlit changes, or CrewAI changes.

## Current boundary

The current execution-awareness flow is:

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
→ Workout Execution Awareness Design
→ TrainingExecutionSummary Contract
```

The current `TrainingExecutionSummary` source flow is:

```text
completed workout_plan_instances
→ dynamic WorkoutPlannedVsActualSummary
→ build_training_execution_summary(user_id)
→ TrainingExecutionSummary
```

The current summary is read-only and includes:

- completed execution count
- recent plan instance ids
- average completion percentage
- planned RIR
- actual RIR
- RIR deviation
- skipped exercise count
- substituted exercise count
- rep deviation buckets
- incomplete logging count
- missing actual RIR count
- missing actual reps count
- execution quality
- execution effort trend
- execution completion trend
- confidence
- reason codes

## Design principles

1. `TrainingExecutionSummary` should enter the pipeline as context before it changes decisions.
2. Summary data should remain descriptive before it becomes prescriptive.
3. The first integration should be passive propagation, not behavior change.
4. The summary should never override `CoachingDecision` by itself.
5. Incomplete execution data should lower confidence rather than produce stronger claims.
6. Manual workout logging should remain independent.
7. Raw actual-set rows should not be passed to CrewAI, reports, or recommendation copy in v1.
8. Completed planned workouts should inform plan-fit and execution-awareness language only after explicit validation rules exist.
9. Automatic progression should remain out of scope until the summary has been validated across real and seeded histories.
10. User-facing coaching should never imply poor adherence, failed programming, overtraining, stalled progress, or need for deload from sparse execution data alone.

## Recommended integration order

### Stage 1 — Passive service contract, already complete

Current milestone status:

```text
TrainingExecutionSummary Contract v1: complete
```

This stage added:

- `models/training_execution_summary_models.py`
- `services/training_execution_summary_service.py`
- `tests/test_training_execution_summary_service.py`

No coaching behavior changed.

### Stage 2 — Passive RecommendationContext attachment

Recommended next implementation milestone:

```text
TrainingExecutionSummary Passive Context Integration v1
```

Add an optional field to `RecommendationContext`:

```python
training_execution_summary: TrainingExecutionSummary | None = None
```

Build it inside the recommendation context construction path:

```text
build_user_health_state(user_id)
→ build_coaching_decision(health_state)
→ build_nutrition_targets(health_state)
→ build_training_constraints(health_state)
→ build_training_execution_summary(user_id)
→ RecommendationContext(..., training_execution_summary=summary)
```

Important behavior rule:

The daily recommendation output must remain unchanged in this stage unless tests explicitly assert the old output should change.

Purpose of Stage 2:

- prove the data can be carried through the context safely
- expose it under developer/debug details if needed
- make it available for tests
- avoid changing `CandidateActionPlan`, `ApprovedActionPlan`, or rendered recommendation copy

### Stage 3 — LLM-safe serialization, still no recommendation behavior change

Update `recommendation_context_to_llm_json()` only after Stage 2 is stable.

Expose only safe summary fields:

```json
{
  "completed_execution_count": 4,
  "average_completion_percentage": 92.5,
  "average_rir_deviation": -0.75,
  "execution_quality": "mostly_completed",
  "execution_effort_trend": "as_planned",
  "execution_completion_trend": "consistently_completed",
  "confidence": "Moderate",
  "reason_codes": [
    "completed_planned_executions_only",
    "multiple_completed_executions_available",
    "high_completion_rate"
  ]
}
```

Do not expose:

- raw actual-set rows
- raw notes
- raw correction history
- per-set weights
- per-set reps
- individual workout comments
- unbounded execution history
- internal database ids except `recent_plan_instance_ids` in developer/debug contexts

For CrewAI candidate generation, the serialized context should describe this as recent completed planned workout execution history, not as adherence, discipline, progression, or failure evidence.

### Stage 4 — Confidence and constraint support only

After passive propagation and serialization tests pass, `TrainingExecutionSummary` may support existing decisions conservatively.

Allowed uses:

- lower confidence when execution data is incomplete
- support controlled progression when completion is consistently high and recovery/nutrition are aligned
- support plan-fit review language when skips/substitutions repeat
- support load-selection review language when reps repeatedly fall below plan
- support effort-management language when actual RIR is repeatedly harder than planned

Disallowed uses:

- switching to `recovery_limited` from execution summary alone
- switching to `nutrition_training_mismatch` from execution summary alone
- claiming overtraining
- claiming stalled progress
- claiming poor adherence
- claiming failed programming
- recommending deload from one missed or difficult workout
- recommending automatic load increases from easier-than-planned execution alone

### Stage 5 — User-facing recommendation copy, explicitly gated

Only after Stage 4 tests pass should the approved recommendation renderer mention execution history.

Safe examples:

```text
Recent completed planned workouts were mostly completed, so maintain controlled progression while continuing to monitor recovery.
```

```text
Recent planned workouts show repeated substitutions, so review plan fit and equipment match before increasing training demand.
```

```text
Actual effort has been slightly harder than planned across recent completed sessions, so keep most working sets near the approved RIR range for now.
```

Unsafe examples:

```text
You are overtraining because recent workouts were harder than planned.
```

```text
Your plan is failing because you skipped exercises.
```

```text
Progress is stalled because completion was below 100%.
```

```text
Increase load next session because recent workouts were easier than planned.
```

### Stage 6 — Automatic progression, future only

Automatic progression is a separate future milestone.

Do not use `TrainingExecutionSummary` to automatically change sets, reps, load, exercise selection, or weekly periodization until there is a dedicated progression engine contract and safety test suite.

## Relationship to UserHealthState

Do not immediately merge `TrainingExecutionSummary` into `UserTrainingState`.

Recommended near-term approach:

```text
UserHealthState remains factual broad health state.
TrainingExecutionSummary remains separate execution-awareness state.
RecommendationContext can reference both.
```

Reason:

`UserTrainingState` currently summarizes broad workout history and manual logging. `TrainingExecutionSummary` summarizes planned-vs-actual execution against selected workout plans. Combining them too early would blur two different evidence types.

Potential later approach:

```python
@dataclass
class UserHealthState:
    ...
    training_execution_summary: TrainingExecutionSummary | None = None
```

This should happen only after passive `RecommendationContext` integration proves stable.

Initial no-data behavior:

- no completed planned workouts should not be treated as a problem
- no completed planned workouts should not reduce overall health-state quality
- no completed planned workouts should not change `CoachingDecision`
- no completed planned workouts should simply mean `training_execution_summary.confidence == "Limited"`

## Relationship to RecommendationContext

`RecommendationContext` is the best first pipeline entry point because it already aggregates approved decision inputs for the recommendation engine.

Recommended field:

```python
training_execution_summary: TrainingExecutionSummary | None = None
```

Recommended behavior for Stage 2:

- build the summary every time the recommendation context is built
- include it in raw developer/debug context
- do not use it to change candidate generation yet
- do not use it to change deterministic rendered recommendation yet
- do not use it to change daily endpoint shape unless explicitly approved

If endpoint shape must remain stable, place the summary only in the debug endpoint first, not the normal `/recommendations/daily/{user_id}` response.

## Relationship to CoachingDecision

`CoachingDecision` should remain primarily driven by recovery, nutrition, training load, data quality, and existing scenario rules.

Recommended first integration:

```text
TrainingExecutionSummary can add reason codes and confidence modifiers later.
TrainingExecutionSummary should not create new scenarios in v1.
```

Potential future reason codes:

- `planned_execution_context_available`
- `planned_execution_limited_confidence`
- `recent_workouts_mostly_completed`
- `actual_effort_harder_than_planned`
- `actual_effort_easier_than_planned`
- `repeated_substitutions_plan_fit_review`
- `repeated_skips_plan_fit_review`
- `execution_logging_incomplete`

Do not add these to `CoachingDecision` until tests define expected behavior for each scenario.

## Relationship to ApprovedActionPlan

`ApprovedActionPlan` remains the only renderable recommendation contract.

`TrainingExecutionSummary` should never be rendered directly to the user. It should inform future candidate validation and approved plan rendering through explicit rules.

Potential future approved action influence:

- workout recommendation may mention controlled progression when execution history is consistently completed
- workout recommendation may mention plan-fit review when substitutions/skips repeat
- rationale may mention confidence limits when execution logging is incomplete

No direct `ApprovedActionPlan` field changes are recommended yet.

## Relationship to full AI Health Reports

Full report generation should not consume execution summary until the daily recommendation path proves safe.

Recommended order:

1. passive `RecommendationContext` integration
2. debug visibility
3. deterministic daily recommendation tests
4. candidate validation updates
5. approved recommendation copy updates
6. full report integration

Reason:

The full report contains more user-facing prose and has historically needed strict validation. Execution awareness should first be proven inside the smaller daily recommendation contract.

## Candidate validation implications

Before execution-aware recommendations are allowed, add validation rules that reject overconfident execution claims.

Forbidden claims from sparse or incomplete execution data:

- overtraining
- stalled progress
- poor adherence
- failed plan
- failed programming
- lack of discipline
- need to deload
- need to increase load
- guaranteed progression
- automatic progression
- exercise avoidance from one skipped exercise
- nutrition failure from workout completion data alone

If `TrainingExecutionSummary.confidence` is `Limited` or `Low`, candidate text should use uncertainty language such as:

- execution history is limited
- planned-vs-actual data is still building
- logging completeness limits confidence
- review plan fit if this pattern continues
- use this as a monitoring signal, not a conclusion

## Daily recommendation behavior by scenario

### aligned_managed

Potential later behavior:

- high completion and as-planned effort can support gradual progression language
- easier-than-planned effort can support monitoring load tolerance, not automatic load increases

Do not say:

- increase load automatically
- add volume automatically
- training is too easy based only on RIR deviation

### recovery_limited

Potential later behavior:

- harder-than-planned effort can reinforce existing recovery-priority guidance
- incomplete execution should reduce confidence, not intensify claims

Do not say:

- overtraining
- deload required from execution data alone
- user failed to follow plan

### nutrition_training_mismatch

Potential later behavior:

- repeated reps below plan or harder-than-planned effort may support reviewing training demand while nutrition support is clarified

Do not say:

- nutrition caused missed reps
- low intake caused incomplete workouts unless nutrition evidence already supports that through approved nutrition logic

### improving_after_deload

Potential later behavior:

- mostly completed execution can support controlled progression
- harder-than-planned effort can reinforce avoiding aggressive ramp-up

Do not say:

- progress aggressively because one workout was easy
- return to high-effort work from one positive completion

### data_quality_limited

Potential later behavior:

- incomplete execution logging should reinforce confidence limits
- missing RIR/reps should lead to better logging guidance

Do not say:

- overtraining
- stalled progress
- failed adherence
- program failure
- strong causality from incomplete execution logs

## Debug and API visibility

Recommended first visibility:

- debug route only, if available
- developer details only, if shown in Streamlit later

Avoid adding `training_execution_summary` to stable user-facing daily recommendation response until explicitly approved.

Potential debug response addition:

```json
{
  "runtime_metadata": {...},
  "training_execution_summary": {
    "completed_execution_count": 3,
    "execution_quality": "consistently_completed",
    "execution_effort_trend": "as_planned",
    "confidence": "Moderate",
    "reason_codes": ["multiple_completed_executions_available"]
  }
}
```

## Testing strategy

### Stage 2 tests — passive context

Add tests proving:

- `RecommendationContext` includes `TrainingExecutionSummary`
- no completed executions produce `no_planned_execution_data`
- context construction does not fail when execution tables are empty
- existing `/recommendations/daily/{user_id}` response shape remains unchanged
- existing deterministic daily recommendation text remains unchanged
- existing full report tests remain unchanged
- no CrewAI call is made in tests

### Stage 3 tests — safe serialization

Add tests proving:

- LLM-safe context includes only approved summary fields
- raw actual-set rows are not serialized
- raw notes are not serialized
- unbounded history is not serialized
- no internal database details leak to normal user-facing responses

### Stage 4 tests — decision support only

Add tests proving:

- low-confidence execution summary does not change scenario
- no-data execution summary does not change scenario
- harder-than-planned effort alone does not create recovery-limited scenario
- skipped/substituted work creates plan-fit reason codes only when explicitly supported
- aligned users remain aligned unless existing health-state evidence says otherwise

### Stage 5 tests — user-facing copy

Add tests proving:

- execution-aware copy is conservative
- incomplete logging produces uncertainty language
- repeated substitutions produce plan-fit language, not failure language
- repeated harder-than-planned effort produces effort-management language, not overtraining language
- easier-than-planned effort does not automatically recommend progression
- forbidden execution claims are rejected by validator

## Non-goals

This design does not add:

- UserHealthState integration
- RecommendationContext implementation changes
- CoachingDecision behavior changes
- ApprovedActionPlan behavior changes
- daily recommendation copy changes
- full report changes
- Streamlit changes
- API endpoint changes
- automatic progression
- weekly periodization
- CrewAI workout generation
- workout_sets mirroring
- raw actual-set serialization
- audit-trail behavior

## Recommended next milestone

Recommended next milestone:

```text
TrainingExecutionSummary Passive Context Integration v1
```

Suggested scope:

1. Add optional `training_execution_summary` to `RecommendationContext`.
2. Build it in `build_recommendation_context()` using `build_training_execution_summary(user_id)`.
3. Keep `/recommendations/daily/{user_id}` stable.
4. Optionally expose the summary only in `/recommendations/daily/{user_id}/debug` or developer details.
5. Do not change deterministic recommendation text.
6. Do not change `CoachingDecision` scenario logic.
7. Add tests proving the summary is carried passively and no existing recommendation behavior changes.
