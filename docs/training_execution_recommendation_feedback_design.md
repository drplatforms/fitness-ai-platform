# TrainingExecutionSummary → Recommendation Feedback Design v1

## Status

Design milestone for Architecture review. No implementation is included in this milestone.

## Purpose

Define how completed workout execution data should influence future daily recommendations conservatively, without automatic progression, automatic deloading, workout-generation changes, or judgmental adherence language.

This design follows the accepted post-workout review direction:

- `ApprovedWorkoutPlan` remains the workout source of truth.
- Completed `WorkoutExecutionSession` and planned-vs-actual data remain the factual execution source.
- AI/copy layers may summarize, explain, and contextualize.
- AI/copy layers must not prescribe future programming.
- Public-safe endpoints must not expose raw AI output, runtime metadata, provider internals, validation errors, or debug context.

## Proposed Future Flow

```text
Completed WorkoutExecutionSession
→ planned-vs-actual summary
→ ApprovedPostWorkoutReviewSummary
→ TrainingExecutionSummary
→ RecommendationContext
→ CoachingDecision / ApprovedActionPlan copy
→ daily recommendation rendering
```

The first implementation should use this flow only for conservative recommendation copy. It should not change scenario classification, workout generation, progression, deloading, nutrition, reports, or Streamlit behavior.

## Core Principle

Completed training data can support recommendation wording, but it must not become an automatic programming engine.

The recommendation system may say:

> Recent completed sessions were generally close to the plan.

It must not say:

> Increase load next session.

The recommendation system may say:

> Recent effort has been a bit harder than planned, so keep today controlled.

It must not say:

> You are overtraining and need a deload.

## Data Sources

### Primary source

Use completed planned workout executions only.

A workout should count when:

- It has a `WorkoutExecutionSession`.
- The execution session status is `completed`.
- It is linked to an approved planned workout.
- It can produce a planned-vs-actual summary.

### Excluded source types

Do not use these for execution-aware recommendation claims in v1:

- In-progress workouts.
- Selected but not started plans.
- Abandoned/cancelled executions.
- Unplanned/ad-hoc workouts, unless later explicitly modeled.
- Raw actual-set rows in recommendation prompt payloads.
- Raw notes or user free text.
- Unbounded workout history.

## Recommended Lookback Window

Use a small recent-history window.

Suggested v1 defaults:

- Count up to the most recent 5 completed planned workout executions.
- Use only summarized signals.
- Prefer aggregate/trend language only when at least 2 completed planned workouts exist.
- Degrade confidence when set-level logging is incomplete.

Rationale:

- One completed workout is context, not a trend.
- Two or more completed workouts can support cautious pattern language.
- A bounded window prevents stale execution history from dominating daily guidance.

## Safe Summary Signals

The following signals are safe to use after aggregation and confidence gating:

- completed planned workout count
- completion percentage
- planned set count
- completed set count
- skipped set count
- skipped exercise count
- substitution count
- average planned RIR
- average actual RIR
- RIR deviation
- sets inside planned rep range
- sets below planned rep range
- sets above planned rep range
- incomplete logging flags
- logging completeness
- recent trend across multiple completed planned workouts

## Signals Requiring Caution

### Harder-than-planned effort

Allowed:

> Recent effort has been a bit harder than planned, so keep today controlled.

Forbidden:

> You are overtraining.

Forbidden:

> You need a deload.

### Easier-than-planned effort

Allowed:

> Recent effort has been easier than planned, so the current plan may be giving useful room to practice clean execution.

Forbidden:

> Increase load automatically.

Forbidden:

> Progress faster next workout.

### Skipped work

Allowed:

> Some planned work has been skipped recently, which is useful context for reviewing recovery, schedule, or plan fit.

Forbidden:

> Poor adherence.

Forbidden:

> Lack of discipline.

Forbidden:

> You failed the workout.

### Substitutions

Allowed:

> Substitutions have shown up recently, so plan fit or equipment fit may be worth reviewing.

Forbidden:

> The plan is bad.

Forbidden:

> You are not following the program.

### Incomplete logging

Allowed:

> Incomplete set-level logging limits how much the system should infer from recent workouts.

Forbidden:

> Your data is unreliable.

Forbidden:

> You failed to log properly.

## Confidence Gates

### 0 completed planned workouts

Recommendation copy should not mention execution history.

Allowed:

> No execution-aware copy.

Forbidden:

> Recent workouts suggest...

### 1 completed planned workout

Only limited context is allowed. No trend claims.

Allowed:

> The most recent completed workout gives a small amount of context, but it is too early to call it a trend.

Allowed:

> Logging is still developing, so today’s recommendation should stay conservative.

Forbidden:

> Your recent workouts show a pattern.

Forbidden:

> You have been underperforming.

### 2–3 completed planned workouts

Cautious pattern language is allowed if logging quality supports it.

Allowed:

> Recent completed sessions have generally stayed close to the plan.

Allowed:

> Recent effort has been a little harder than planned, so keep today controlled.

Forbidden:

> You need a deload.

Forbidden:

> Progress has stalled.

### 4–5 completed planned workouts

Moderate confidence trend language may be allowed when logging quality is adequate.

Allowed:

> Across recent completed workouts, effort has generally stayed close to the planned RIR range.

Allowed:

> Recent substitutions may be worth reviewing for plan fit or equipment fit.

Forbidden:

> Automatic progression is warranted.

Forbidden:

> The program is failing.

### Incomplete logging

When logging is incomplete, add uncertainty language.

Allowed:

> Incomplete RIR logging limits effort interpretation.

Allowed:

> The completed sets give some useful context, but missing set-level details keep confidence limited.

Forbidden:

> Strong execution trend claims.

## Recommended Copy-Only v1 Behavior

The first implementation after this design should affect recommendation copy only.

It may influence:

- short recommendation rationale text
- approved action plan explanation text
- daily coach-facing copy, if already public-safe
- debug-only explanation of execution-aware context

It should not influence:

- `CoachingDecision` scenario classification
- `ApprovedActionPlan` structure
- workout generation
- exercise selection
- progression decisions
- deload decisions
- nutrition targets
- report generation
- Streamlit UI layout

## Allowed Recommendation Language

Examples that should be allowed after confidence gates pass:

- “Recent workouts suggest logging consistency is still developing.”
- “Recent completed sessions were generally close to the plan.”
- “Recent effort has been a bit harder than planned, so keep today controlled.”
- “Substitutions have shown up recently, so plan fit or equipment fit may be worth reviewing.”
- “Incomplete set-level logging limits how much should be inferred from recent workouts.”
- “The recent completed workout gives some context, but it is too early to call it a trend.”
- “Recent sessions suggest the current plan is producing useful review data.”

## Forbidden Recommendation Language

Always reject or avoid:

- overtraining
- stalled progress
- stalled fat loss
- poor adherence
- lack of discipline
- failed programming
- failed workout
- user failed
- automatic deload
- required deload
- automatic load increase
- automatic progression
- increase load automatically
- add weight next workout
- next workout should increase
- medical claims
- injury diagnosis
- strong conclusions from one workout
- discipline or morality framing
- plan is bad
- program is ineffective

## Scenario Interaction

### data_quality_limited

Execution-history claims should remain very limited.

Allowed:

> Recent logging is still developing, so execution history should be treated as context rather than a firm trend.

Forbidden:

> Your training pattern proves...

### recovery_limited

Harder-than-planned effort may be used only as support for controlled-session language.

Allowed:

> Recent effort has been a bit harder than planned, so today should stay controlled.

Forbidden:

> You are overtraining.

Forbidden:

> A deload is required.

### aligned_managed

Consistency or controlled progression language may be allowed only with adequate history.

Allowed:

> Recent completed sessions have generally stayed close to the plan.

Forbidden:

> Increase load automatically.

### nutrition_training_mismatch

Do not turn skipped or incomplete training into nutrition claims.

Allowed:

> Recent workout completion gives useful training context, but nutrition recommendations should still come from nutrition data.

Forbidden:

> Skipped work means your intake is too low.

### improving_after_deload

Avoid aggressive progression language.

Allowed:

> Recent completed sessions can support a controlled return to consistency.

Forbidden:

> Ramp back up quickly.

## RecommendationContext Design

`TrainingExecutionSummary` already exists as optional internal context. The next implementation can expose a derived public-safe feedback object inside `RecommendationContext`, such as:

```python
TrainingExecutionRecommendationFeedback(
    completed_execution_count=int,
    confidence="Limited | Low | Moderate | High",
    logging_quality="limited | developing | adequate",
    effort_signal="harder_than_planned | close_to_plan | easier_than_planned | unknown",
    completion_signal="mostly_completed | partially_completed | limited_data",
    substitution_signal="none | occasional | repeated",
    skip_signal="none | occasional | repeated",
    allowed_copy_points=list[str],
    uncertainty_notes=list[str],
)
```

This object should be derived from `TrainingExecutionSummary` and planned-vs-actual summaries. It should not contain raw actual-set rows or raw notes.

## Validation Expectations

Before execution-aware recommendation copy becomes user-facing, validators should ensure:

- no completed executions produce no execution-aware user-facing copy
- one completed execution cannot create trend claims
- incomplete logging lowers confidence
- harder-than-planned effort does not mention overtraining
- harder-than-planned effort does not require deload
- easier-than-planned effort does not recommend automatic progression
- skipped exercises produce context language, not adherence/failure language
- substitutions produce plan-fit/equipment-fit language, not failure language
- seeded users 101–105 remain scenario-stable
- normal `/recommendations/daily/{user_id}` response shape remains stable unless explicitly approved
- no live CrewAI/Ollama calls occur in tests

## Suggested Test Cases

### Unit tests

- feedback object returns no copy points for zero completed executions
- one completed execution produces context-only language
- two completed executions allow cautious pattern language
- incomplete logging produces uncertainty language
- repeated substitutions produce plan-fit/equipment-fit language
- skipped sets/exercises do not produce poor-adherence language
- harder-than-planned RIR produces controlled-session language
- easier-than-planned RIR does not produce load-increase language
- forbidden phrases are rejected

### Regression tests

- seeded users 101–105 daily recommendations remain scenario-stable
- current public recommendation response shape remains unchanged
- approved action plan structure remains unchanged unless explicitly approved
- workout preview/execution/history flows remain unchanged
- full pytest passes
- no live CrewAI/Ollama calls occur in pytest

## Implementation Sequence After Design Acceptance

1. **Execution-aware recommendation copy v2**
   - Add derived feedback object.
   - Add deterministic copy only.
   - Keep response shape stable unless explicitly approved.
   - Add validators.

2. **QA review of seeded and real-user wording**
   - Review users 101–105.
   - Review at least one real completed-workout flow.
   - Confirm no judgmental, prescriptive, or medical language.

3. **Daily Coach Synthesis v2**
   - Later, allow AI synthesis only after deterministic behavior is proven.
   - Continue strict parse/validate/fallback behavior.
   - Keep raw AI output out of public endpoints.

## Non-Goals

This design does not add:

- automatic progression
- weekly periodization
- next-workout prescription
- workout generator changes
- nutrition changes
- report changes
- Streamlit changes
- CrewAI workout structure generation
- live CrewAI/Ollama tests
- judgmental adherence language
- persistence changes
- public endpoint changes

## Acceptance Criteria

Architecture can accept this design when:

- the feedback path is copy-only first
- completed planned executions are the only source for execution-aware feedback
- confidence gates prevent strong claims from limited data
- incomplete logging lowers confidence
- substitutions/skips remain neutral context
- automatic progression and deloads remain explicitly out of scope
- existing recommendation, workout, nutrition, report, and Streamlit behavior remain unchanged until separately approved
