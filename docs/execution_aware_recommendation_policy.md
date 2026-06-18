# Execution-Aware Recommendation Policy

## Purpose

This document defines the policy boundary for allowing `TrainingExecutionSummary` to influence future `ApprovedActionPlan` text.

The current system already carries `TrainingExecutionSummary` inside `RecommendationContext` as internal/debug-only context. The normal `/recommendations/daily/{user_id}` response shape is stable, `recommendation_context_to_llm_json()` excludes execution summary data, and CrewAI does not receive execution history yet.

This policy exists so execution history does not accidentally become user-facing coaching before thresholds, wording, and validation rules are explicit.

This is a design document only. It does not implement recommendation behavior changes, full report changes, `UserHealthState` changes, `CoachingDecision` changes, `ApprovedActionPlan` changes, CrewAI prompt changes, Streamlit changes, automatic progression, or workout generation changes.

## Current accepted boundary

Current passive context flow:

```text
completed planned workout executions
→ dynamic WorkoutPlannedVsActualSummary
→ build_training_execution_summary(user_id)
→ TrainingExecutionSummary
→ RecommendationContext internal/debug context only
```

Current behavior guarantees:

- `RecommendationContext` carries `training_execution_summary`.
- `/recommendations/daily/{user_id}/debug` may expose `training_execution_summary` for QA/developer inspection.
- `/recommendations/daily/{user_id}` does not expose the summary.
- `recommendation_context_to_llm_json()` excludes the summary.
- CrewAI does not receive execution summary data.
- User-facing daily recommendation copy does not change.
- Full AI Health Report copy does not change.
- Streamlit behavior does not change.
- Automatic progression does not exist.

## Design principles

1. Execution history is context, not a verdict.
2. Descriptive execution signals must not become prescriptive until validation rules exist.
3. Missing or incomplete execution logging lowers confidence; it must not produce stronger coaching claims.
4. One completed planned workout is not a trend.
5. Skipped or substituted exercises may indicate plan-fit, equipment-fit, time, recovery, or logging context; they do not prove poor adherence.
6. Harder-than-planned effort may support existing recovery/intensity guidance, but it does not diagnose overtraining.
7. Easier-than-planned effort may support monitoring progression readiness, but it does not authorize automatic load or volume increases.
8. Execution-aware copy must never contradict `CoachingDecision`, `TrainingConstraints`, or `NutritionTargets`.
9. Execution-aware copy must remain scenario-safe.
10. CrewAI should not receive execution summary data until deterministic copy and validation have been proven.

## Minimum completed planned workout count

### 0 completed planned workouts

Policy:

- Do not mention execution history in user-facing recommendation text.
- Do not alter `CandidateActionPlan` or `ApprovedActionPlan` text.
- Do not add plan-fit, completion, effort-trend, adherence, progression, or deload language.
- Debug context may show `execution_quality = "no_planned_execution_data"`.

Allowed internal interpretation:

```text
No completed planned workout execution data is available yet.
```

Forbidden user-facing implication:

```text
You have not completed planned workouts, so adherence is poor.
```

### 1 completed planned workout

Policy:

- One completed workout is limited context only.
- User-facing execution-aware claims should usually be omitted.
- If explicitly allowed later, wording must say the history is limited.
- Do not claim a trend.
- Do not recommend progression, deload, plan changes, or adherence changes from one workout.

Allowed future wording, if approved:

```text
Planned workout execution history is still limited, so keep logging actual reps, weight, and RIR before drawing stronger conclusions.
```

Forbidden wording:

```text
Your recent workouts show a clear trend.
```

```text
Increase load next session because the last workout was easier than planned.
```

```text
Deload because the last workout was harder than planned.
```

### 2-3 completed planned workouts

Policy:

- Cautious trend language may be allowed if logging quality is adequate.
- Use words like `recent`, `appears`, `may`, `suggests`, and `monitor`.
- Avoid strong claims about performance, discipline, fatigue, adaptation, or programming quality.
- Do not override existing scenario logic.

Allowed future wording, if supported:

```text
Recent completed planned workouts appear mostly completed, so keep progression controlled while monitoring recovery and actual RIR.
```

```text
Recent actual RIR has been slightly harder than planned, so keep the next session within the approved RIR range rather than pushing closer to failure.
```

Forbidden wording:

```text
Your program is failing.
```

```text
You need a deload.
```

```text
You are not adhering to the plan.
```

### 4-5 completed planned workouts

Policy:

- Moderate-confidence execution-aware language may be allowed if completion and logging quality are adequate.
- User-facing copy may mention consistency, effort trend, plan fit, or logging quality.
- Still avoid automatic progression or automatic deload language.
- Still require scenario compatibility.

Allowed future wording, if supported:

```text
Across recent completed planned workouts, completion has been consistent and effort has stayed close to the approved range, so maintain controlled progression.
```

```text
Repeated substitutions may suggest the plan should be reviewed for equipment fit or exercise fit before training demand is increased.
```

Forbidden wording:

```text
Automatically increase all working weights next session.
```

```text
Your skipped exercises show lack of discipline.
```

## Minimum confidence required

### Limited confidence

Policy:

- No user-facing execution-aware coaching claims.
- Do not mention completion trends, effort trends, substitutions, skipped exercises, adherence, progression, or plan quality.
- Debug/internal context may show why confidence is limited.

Common reasons:

- no completed planned workouts
- one completed workout only
- incomplete actual-set logging
- missing actual reps
- missing actual RIR
- empty completion

Allowed user-facing wording only if a future UI explicitly asks for logging guidance:

```text
Planned-vs-actual workout data is still building, so keep logging actual sets before using it for stronger coaching decisions.
```

### Low confidence

Policy:

- Optional soft logging-quality language only.
- Do not use execution history to alter workout recommendations.
- Do not make trend claims.
- Do not mention plan fit unless repeated skips/substitutions are clearly present and wording remains tentative.

Allowed future wording:

```text
Execution logging is still developing, so use the current workout recommendation as the primary guide and keep tracking actual reps, weight, and RIR.
```

Forbidden wording:

```text
Your execution trend shows you need to change the plan.
```

### Moderate confidence

Policy:

- Limited execution-aware coaching may be allowed.
- Trend language must remain conservative.
- The summary can support, but not replace, existing `CoachingDecision` and `TrainingConstraints`.
- Strong recommendations still require matching recovery, nutrition, and training-state evidence.

Allowed future wording:

```text
Recent planned workouts have been mostly completed, which supports staying with controlled progression while monitoring recovery.
```

### High confidence

Policy:

- Execution-aware language may be more direct but still not automatic.
- Plan-fit and effort-management suggestions may be allowed when repeated patterns are present.
- Automatic progression still remains out of scope unless a dedicated progression engine is approved.

Allowed future wording:

```text
Recent planned workouts have been consistently completed with actual effort close to the plan, so the current program appears executable. Keep progression gradual and continue tracking actual RIR.
```

Forbidden wording:

```text
Automatically increase load because execution confidence is high.
```

## Allowed execution-aware claims

The following claim types may be allowed after deterministic copy and validation are implemented.

### Mostly completed recent planned workouts

Allowed when:

- completed planned workout count is at least 2-3
- confidence is Moderate or High
- completion percentage is high enough to support the claim
- incomplete logging is not the dominant signal

Allowed wording:

```text
Recent completed planned workouts were mostly completed.
```

```text
Recent planned workouts appear executable, so maintain controlled progression.
```

Do not say:

```text
You have perfect adherence.
```

### Actual effort harder than planned

Allowed when:

- repeated negative RIR deviation appears across completed planned workouts
- actual RIR values are present enough to support the trend
- scenario allows effort-management language

Allowed wording:

```text
Recent actual effort has been harder than planned, so keep working sets closer to the approved RIR range for now.
```

```text
Actual RIR has tended to land closer to failure than planned, which supports staying conservative with intensity until recovery stays stable.
```

Do not say:

```text
You are overtraining.
```

```text
A deload is automatically required.
```

### Actual effort easier than planned

Allowed when:

- repeated positive RIR deviation appears across completed planned workouts
- actual RIR values are present enough to support the trend
- recovery and nutrition context are compatible with progression discussion

Allowed wording:

```text
Recent actual effort appears easier than planned, so monitor whether load selection is still matching the intended effort target.
```

Do not say:

```text
Increase weight automatically next workout.
```

```text
Add volume immediately.
```

### Repeated substitutions

Allowed when:

- substitutions are repeated across more than one completed planned workout
- confidence is at least Low for plan-fit language and Moderate for stronger plan-fit language

Allowed wording:

```text
Repeated substitutions may suggest reviewing exercise fit or equipment fit.
```

```text
If substitutions continue, adjust the plan to better match available equipment and preferred movements.
```

Do not say:

```text
You failed to follow the plan.
```

```text
The plan is bad.
```

### Repeated skipped exercises

Allowed when:

- skipped exercises repeat across completed planned workouts
- completion and logging data are adequate enough to distinguish skipped from missing

Allowed wording:

```text
Repeated skipped exercises may suggest reviewing plan fit, session length, recovery, or nutrition support.
```

Do not say:

```text
Skipped exercises show lack of discipline.
```

```text
Skipped exercises prove poor adherence.
```

### Incomplete actual-set logging

Allowed when:

- incomplete logging, missing RIR, missing reps, or empty completion flags appear

Allowed wording:

```text
Incomplete actual-set logging limits how much the system should infer from planned-vs-actual workout history.
```

```text
Keep logging actual reps, weight, and RIR so execution history can support future coaching more reliably.
```

Do not say:

```text
Incomplete logging means workout execution was poor.
```

## Forbidden claims

Execution-aware recommendation text must not say or imply any of the following from `TrainingExecutionSummary` alone:

- overtraining
- poor adherence
- failed programming
- failed plan
- stalled progress
- automatic deload required
- automatic load increase
- automatic volume increase
- user failed the workout
- plan is bad
- plan is ineffective
- skipped exercises mean lack of discipline
- substitutions mean noncompliance
- one workout proves a trend
- incomplete logging means poor execution
- nutrition caused missed reps unless approved nutrition logic already supports that claim
- recovery caused skipped exercises unless approved recovery logic already supports that claim
- weight-loss progress is stalled because of execution history
- muscle gain is blocked because of execution history

Forbidden phrase examples:

```text
You are overtraining.
```

```text
Your progress is stalled because completion was below 100%.
```

```text
Your skipped exercises show poor adherence.
```

```text
The plan is ineffective because you substituted exercises.
```

```text
Automatically increase the load next session.
```

```text
One difficult workout means you need a deload.
```

## Scenario interaction policy

### data_quality_limited

Policy:

- Keep execution-history claims extremely limited.
- Prefer logging-quality language only.
- Do not use execution data to produce stronger training or nutrition conclusions.
- Missing actual reps/RIR should reinforce uncertainty, not coaching intensity.

Allowed future wording:

```text
Execution logging is still limited, so keep tracking actual reps, weight, and RIR before using planned-vs-actual history for stronger coaching decisions.
```

Forbidden wording:

```text
Execution history shows overtraining.
```

```text
Skipped work proves poor adherence.
```

### recovery_limited

Policy:

- Harder-than-planned effort may support existing recovery-priority guidance.
- Execution history must not diagnose overtraining or require deload by itself.
- If RIR is missing, use logging-quality language rather than effort conclusions.

Allowed future wording:

```text
Recent actual effort appears harder than planned, which supports keeping working sets near the approved RIR range while recovery improves.
```

Forbidden wording:

```text
You are overtraining because actual RIR was harder than planned.
```

### aligned_managed

Policy:

- Consistently completed workouts may support calm consistency and controlled progression language.
- Easier-than-planned effort may support monitoring load selection only when history and recovery/nutrition context are adequate.
- Do not create intervention framing.

Allowed future wording:

```text
Recent completed planned workouts appear consistent, so maintain gradual progression and continue tracking actual RIR.
```

Forbidden wording:

```text
Increase load automatically because workouts were completed.
```

```text
You need intervention because completion was not perfect.
```

### nutrition_training_mismatch

Policy:

- Do not turn skipped, incomplete, or harder-than-planned execution into zero-intake or low-intake claims.
- Execution history may support reviewing training demand while nutrition support is clarified.
- Nutrition conclusions must still come from approved nutrition logic, not execution history alone.

Allowed future wording:

```text
If actual effort continues to run harder than planned while nutrition support is being clarified, keep training demand controlled.
```

Forbidden wording:

```text
Missed reps prove nutrition intake is inadequate.
```

```text
Skipped sets mean calories are too low.
```

### improving_after_deload

Policy:

- Mostly completed workouts may support controlled progression.
- Harder-than-planned effort should reinforce avoiding aggressive ramp-up.
- Easier-than-planned effort must not trigger aggressive progression language.

Allowed future wording:

```text
Recent planned workouts appear manageable, so continue controlled progression rather than jumping straight back to high-effort work.
```

Forbidden wording:

```text
Return to aggressive progression because one workout felt easy.
```

## Validation expectations before behavior changes

Before any user-facing execution-aware copy is enabled, add deterministic validation rules for `CandidateActionPlan` and rendered `ApprovedActionPlan` text.

Required validation behavior:

- Reject forbidden claims listed in this policy.
- Reject trend claims when `completed_execution_count < 2`.
- Reject moderate-confidence execution claims when summary confidence is `Limited` or `Low`.
- Reject automatic progression language unless a future progression engine explicitly approves it.
- Reject deload-required language from execution history alone.
- Reject adherence/failure/discipline language from skips/substitutions.
- Reject causality between execution and nutrition unless nutrition mismatch is independently established by existing approved nutrition logic.
- Reject causality between execution and recovery unless recovery-limited status is independently established by existing recovery logic.

Suggested validator phrase families:

```text
overtraining
poor adherence
failed programming
failed plan
stalled progress
automatic deload
automatically deload
automatic load increase
automatically increase load
failed the workout
lack of discipline
plan is bad
plan is ineffective
one workout proves
```

## Future integration order

Use this order before any behavior change reaches users:

1. Policy document, this milestone.
2. Deterministic `ApprovedActionPlan` copy proposal.
3. Candidate and approved-plan validation rules.
4. Tests proving no behavior changes for no-data and low-confidence users.
5. Tests proving seeded users 101-105 remain scenario-stable.
6. Deterministic execution-aware recommendation copy behind explicit conditions.
7. Debug review of generated copy.
8. CrewAI prompt exposure later, only after deterministic behavior is proven.
9. Full AI Health Report exposure later, only after daily recommendation behavior is stable.

## Required tests before user-facing behavior changes

Add tests proving:

- no completed executions do not alter recommendation text
- one completed execution does not create strong trend claims
- incomplete logging lowers confidence and produces logging-quality language only
- harder-than-planned effort does not mention overtraining
- harder-than-planned effort does not force deload language
- easier-than-planned effort does not recommend automatic progression
- repeated skipped exercises produce plan-fit language, not adherence/failure language
- repeated substitutions produce plan-fit/equipment-fit language, not noncompliance language
- data_quality_limited keeps execution-history claims minimal
- recovery_limited uses harder-than-planned effort only as support, not diagnosis
- aligned_managed avoids intervention framing
- nutrition_training_mismatch does not convert skipped/incomplete work into zero-intake claims
- improving_after_deload avoids aggressive progression language
- seeded users 101-105 remain scenario-stable
- normal `/recommendations/daily/{user_id}` response shape remains stable unless explicitly approved
- `/recommendations/daily/{user_id}/debug` remains the only route exposing raw `TrainingExecutionSummary` context until further approval
- no raw actual-set rows are serialized
- no raw notes are serialized
- no CrewAI or live Ollama calls occur in tests

## Non-goals

This policy does not add:

- recommendation behavior changes
- full report changes
- `UserHealthState` schema changes
- `CoachingDecision` behavior changes
- `ApprovedActionPlan` changes
- CrewAI execution-summary exposure
- automatic progression
- workout generation changes
- weekly periodization
- Streamlit changes
- workout_sets mirroring
- summary persistence
- raw execution-history serialization

## Recommended next milestone

Recommended next milestone after this policy is accepted:

```text
Execution-Aware ApprovedActionPlan Validation v1
```

Suggested scope:

1. Add validator rules for forbidden execution-aware claims.
2. Keep deterministic recommendation copy unchanged initially.
3. Add tests using synthetic `TrainingExecutionSummary` examples.
4. Prove no-data and low-confidence summaries do not alter user-facing copy.
5. Prove harder/easier/skipped/substituted execution examples cannot produce forbidden language.
6. Keep CrewAI prompt exposure disabled.
7. Keep `/recommendations/daily/{user_id}` response shape stable.
