# CrewAI Workout Candidate Design v1

## Purpose

This document defines the v1 design for allowing CrewAI to generate structured `CandidateWorkoutPlan` JSON from approved backend context while the backend remains responsible for parsing, schema validation, workout validation, approval, fallback, and deterministic rendering.

This is a design document only. It does not implement CrewAI workout generation, provider toggles, subprocess workers, Streamlit UI, persistence changes, automatic progression, weekly periodization, nutrition changes, meal planning, or production deployment work.

The goal is to preserve the current deterministic workout loop as the stable default while defining a safe future boundary where CrewAI can propose workout candidates without becoming the source of truth.

## Current decision

Additional workout-loop hardening should pause except for critical bugs. The current workout foundation is usable enough to move from deterministic workout execution polish toward future AI-assisted workout candidate design.

Accepted current foundation:

- expanded exercise catalog
- equipment-aware deterministic workout previews
- workout selection/start
- actual set logging/editing
- workout completion
- workout history
- planned-vs-actual summaries
- `TrainingExecutionSummary`
- execution-aware recommendation copy
- substitution candidate/apply backend
- substitution overlay UI behavior
- Today-first UX direction documented

CrewAI workout generation should not replace this foundation. It should eventually sit behind the same trusted pattern already used elsewhere in the app: untrusted candidate generation, backend validation, approved contract, deterministic rendering, and safe fallback.

## Target future flow

```text
UserHealthState
→ CoachingDecision
→ TrainingConstraints
→ WorkoutConstraints
→ EquipmentProfile
→ ExerciseCatalog
→ TrainingExecutionSummary
→ WorkoutContext
→ CrewAI CandidateWorkoutPlan JSON
→ backend parse/schema validation
→ workout validator
→ ApprovedWorkoutPlan
→ deterministic rendering
```

The backend remains the source of truth throughout the flow. CrewAI may propose a candidate plan only. It must not approve, persist, render, or directly display workout recommendations.

## CandidateWorkoutPlan JSON shape

CrewAI should return exactly one JSON object matching the candidate workout contract.

Required top-level fields:

```json
{
  "title": "...",
  "session_focus": "...",
  "duration_minutes": 45,
  "exercises": [],
  "warmup": "...",
  "cooldown": "...",
  "progression_guidance": "...",
  "rationale": "...",
  "confidence": "Moderate"
}
```

### Field rules

- `title`: short user-facing workout title
- `session_focus`: short explanation of the session's intent
- `duration_minutes`: integer session estimate; should remain realistic for the scenario
- `exercises`: non-empty list of candidate exercises
- `warmup`: concise user-facing warmup guidance
- `cooldown`: concise user-facing cooldown guidance
- `progression_guidance`: user-facing guidance constrained by `TrainingConstraints`
- `rationale`: short explanation grounded in approved backend context
- `confidence`: one of the backend-approved confidence labels, such as `Limited`, `Low`, `Moderate`, or `High`

The model should not return markdown, code fences, commentary, extra root objects, or final-report sections.

## Candidate exercise JSON shape

Each exercise in `exercises` should be a JSON object with bounded structured fields.

Required fields:

```json
{
  "exercise_name": "Dumbbell Bench Press",
  "catalog_exercise_id": 12,
  "movement_pattern": "horizontal_push",
  "target_zone": "upper_body_push",
  "sets": 3,
  "reps_min": 8,
  "reps_max": 12,
  "target_rir_min": 2,
  "target_rir_max": 4,
  "required_equipment": ["dumbbell", "adjustable_bench"],
  "notes": "Use controlled reps and stop with reps in reserve."
}
```

### Candidate exercise field rules

- `exercise_name`: must match an exercise in the approved catalog list sent to the model
- `catalog_exercise_id`: should be included when available from the approved catalog list
- `movement_pattern`: must match the catalog entry or an approved backend alias
- `target_zone`: bounded grouping for UI and validation, not a free-form medical claim
- `sets`: positive integer within scenario-safe bounds
- `reps_min`: positive integer
- `reps_max`: positive integer greater than or equal to `reps_min`
- `target_rir_min`: integer within approved `TrainingConstraints`
- `target_rir_max`: integer within approved `TrainingConstraints`
- `required_equipment`: must be a subset of the catalog entry requirements and available equipment
- `notes`: short coaching cue; no forbidden claims or internal/debug language

The backend may translate `exercise_name` into the existing `CandidateWorkoutExercise.name` field after validation. The backend may also keep `catalog_exercise_id`, `movement_pattern`, and `target_zone` as validation-only metadata until the model layer is expanded.

## Approved backend context CrewAI may receive

CrewAI should receive only a bounded, LLM-safe workout-generation context prepared by the backend.

Allowed context:

- user scenario
- top-level confidence
- approved training constraints
- approved workout constraints
- training environment
- available equipment
- unavailable equipment
- bounded allowed catalog exercises
- recent `TrainingExecutionSummary`
- movement-pattern targets
- scenario safety constraints
- session length target or range
- allowed RIR range
- allowed exercise count range
- relevant plan-fit signals, if already summarized

The context should be intentionally smaller than the full backend state. CrewAI does not need raw database rows to propose a plan.

## Bounded catalog context

The backend should not send the full exercise catalog unbounded if it becomes large.

Recommended v1 catalog context:

1. Filter catalog by equipment compatibility first.
2. Exclude machine exercises when machine is unavailable.
3. Prefer movement patterns needed for the session.
4. Include a bounded number of candidate exercises per movement pattern.
5. Include only metadata needed for generation and validation.

Recommended allowed exercise item shape:

```json
{
  "catalog_exercise_id": 12,
  "name": "Dumbbell Bench Press",
  "movement_pattern": "horizontal_push",
  "exercise_type": "strength",
  "primary_muscle_groups": ["chest", "triceps", "shoulders"],
  "required_equipment": ["dumbbell", "adjustable_bench"],
  "difficulty": "intermediate"
}
```

CrewAI should be instructed to choose only from this allowed list. The backend still validates every selected exercise against the live catalog and equipment profile.

## Context CrewAI must not receive

CrewAI workout generation must not receive sensitive, unbounded, or backend-only data.

Do not send:

- raw actual-set rows
- raw workout notes
- unbounded workout history
- raw manual workout logs
- raw report text
- raw CrewAI logs
- internal debug payloads
- validator internals
- database row dumps
- private/backend-only metadata
- user-entered free-text notes unless separately sanitized and explicitly approved
- hidden target values that are not approved for model use

Execution history should be summarized through `TrainingExecutionSummary`, not sent as raw row-level history.

## Workout-specific validation rules

Every CrewAI candidate must be treated as untrusted until it passes backend validation.

Required validation:

1. Candidate JSON parses successfully.
2. Candidate has exactly the required shape or only explicitly allowed fields.
3. Every exercise exists in the exercise catalog or approved allowed-catalog subset.
4. `catalog_exercise_id` and `exercise_name` agree when both are present.
5. Required equipment is available in the current `EquipmentProfile` / `WorkoutConstraints`.
6. Unavailable equipment does not appear in any exercise.
7. Machine exercises are rejected when machine is unavailable.
8. RIR values stay within `TrainingConstraints`.
9. Sets and reps are positive and within scenario-safe bounds.
10. Exercise count and duration are reasonable for the scenario.
11. Movement patterns match allowed movement-pattern targets or approved compatible families.
12. The candidate does not contradict `CoachingDecision.scenario`.
13. The candidate does not include internal/debug terms.
14. The candidate does not include forbidden claims.
15. The candidate passes the existing workout validator before conversion to `ApprovedWorkoutPlan`.

If any validation fails, the backend must use deterministic fallback.

## Scenario safety rules

### recovery_limited

Allowed:

- recovery-aware strength practice
- moderate effort
- RIR 2-3 or other approved `TrainingConstraints` range
- lower recovery-cost exercise choices
- shorter duration when appropriate

Forbidden:

- max-effort framing
- RIR 0-1 default work
- aggressive finishers
- automatic deload claims unless already approved elsewhere
- overtraining diagnosis

### aligned_managed

Allowed:

- normal gradual progression
- balanced strength session
- moderate accessory work
- progression only within backend-approved constraints

Forbidden:

- unnecessary deload framing
- unnecessary reduce-intensity framing
- automatic load increases
- strong claims that progress is stalled or guaranteed

### nutrition_training_mismatch

Allowed:

- controlled strength practice
- moderate volume
- nutrition-support-aware rationale
- avoid aggressive conditioning volume

Forbidden:

- zero-intake assumptions
- hard calorie claims
- punishment framing
- aggressive volume increases while nutrition support is uncertain

### improving_after_deload

Allowed:

- controlled progression
- gradual return to normal training stress
- moderate accessory work
- avoid rapid jumps

Forbidden:

- aggressive ramping language
- max-effort return-to-training framing
- automatic load increases

### data_quality_limited

Allowed:

- manageable baseline session
- simple exercises
- logging-quality caution
- confidence-limited rationale

Forbidden:

- overtraining claims
- stalled-progress claims
- failed-programming claims
- strong trend claims
- automatic progression or deload claims

## Forbidden claims and language

CrewAI workout candidates must not include:

- overtraining diagnosis
- stalled progress claims
- failed programming claims
- poor adherence claims
- lack-of-discipline claims
- automatic deload required
- automatic load increase
- guaranteed progress
- injury diagnosis
- medical claims
- pain-treatment claims
- unsupported progression claims
- claims based on one workout as a trend
- internal/debug language such as `guardrail`, `validator`, `fallback`, `deterministic`, `schema`, or backend model names

Substitutions, skipped work, incomplete actual-set logging, or incomplete workout history must be framed as uncertainty or plan-fit context, not failure.

## Runtime policy

Deterministic workout generation remains the default.

CrewAI workout generation should be opt-in/debug only at first.

Recommended future provider toggle:

```text
WORKOUT_CANDIDATE_PROVIDER=deterministic|crewai_subprocess
```

Recommended future timeout setting:

```text
WORKOUT_CANDIDATE_TIMEOUT_SECONDS=45
```

Runtime rules:

1. Do not add same-process hard timeout hacks around CrewAI.
2. Use deterministic generation by default.
3. Use CrewAI only through the accepted isolated/subprocess strategy when implementation resumes.
4. Tests must never call live CrewAI or Ollama.
5. Malformed JSON must fall back deterministically.
6. Schema mismatch must fall back deterministically.
7. Validation failure must fall back deterministically.
8. Provider timeout/failure must fall back deterministically.
9. Runtime metadata should remain internal/debug-only.

## Output behavior

CrewAI output is never user-facing by itself.

Only `ApprovedWorkoutPlan` may be rendered to the user.

The stable workout preview response shape should remain unchanged unless Architecture explicitly approves a contract change.

The future CrewAI path should produce the same public preview contract as deterministic generation:

```text
GET /workout-plans/preview/{user_id}
→ success
→ user_id
→ scenario
→ confidence
→ training_constraints
→ workout_constraints
→ approved_workout_plan
→ rendered_workout_plan
```

If debug metadata is added later, it should live under a separate developer/debug route or developer-only UI expander, not the normal user-facing preview contract.

## Prompt contract direction

The future CrewAI workout prompt should be short and strict.

Recommended instruction style:

- You are proposing a workout candidate from approved context.
- Return one JSON object only.
- Choose exercises only from the allowed catalog list.
- Respect available and unavailable equipment.
- Respect the provided RIR range.
- Respect the scenario safety instructions.
- Do not add markdown or commentary.
- Do not invent exercises, equipment, history, injuries, or progression rules.
- Do not include internal system terms.

Avoid exposing implementation names unless needed. Prefer user-safe language like `approved context`, `allowed exercises`, and `required JSON object`.

## Fallback behavior

Fallback should always return a safe deterministic `ApprovedWorkoutPlan`.

Fallback triggers:

- provider disabled
- provider unavailable
- provider timeout
- malformed JSON
- markdown-wrapped output if the parser does not explicitly support it
- schema mismatch
- missing required fields
- extra unapproved fields if strict parsing is enabled
- unknown exercise
- unavailable equipment
- RIR outside constraints
- scenario mismatch
- forbidden claims
- validation failure

Fallback should not be treated as an error for the user. It should be normal safe behavior.

## Testing strategy

Initial implementation tests should be mocked and deterministic.

Required future tests:

- valid CrewAI CandidateWorkoutPlan JSON parses
- malformed JSON falls back
- markdown-wrapped output falls back or is safely normalized
- missing required field falls back
- extra unapproved field falls back if strict parsing is enabled
- unknown catalog exercise falls back
- exercise requiring unavailable equipment falls back
- machine exercise falls back when machine is unavailable
- RIR outside TrainingConstraints falls back
- recovery_limited max-effort candidate falls back
- aligned_managed deload/reduce-intensity candidate falls back
- data_quality_limited overtraining/stalled-progress candidate falls back
- unsafe progression language falls back
- deterministic fallback renders safely
- normal preview response shape remains stable
- seeded users 101-105 remain valid
- pytest does not call live CrewAI/Ollama

## Staged implementation plan

Recommended future sequence:

1. Design CrewAI Workout Candidate contract. This document.
2. Add CandidateWorkoutPlan parse/schema helpers for JSON-only output.
3. Add workout-candidate provider boundary with deterministic default.
4. Add mocked provider tests for valid and invalid CrewAI output.
5. Add optional debug route or internal metadata for provider status.
6. Add subprocess worker only if Architecture resumes isolated CrewAI runtime work.
7. Keep Streamlit rendering only `ApprovedWorkoutPlan`.
8. Only after validation is proven, consider opt-in runtime QA with local CrewAI.

## Non-goals

This milestone does not include:

- CrewAI workout generation implementation
- Streamlit implementation
- nutrition changes
- automatic progression
- weekly periodization
- CrewAI final report generation
- meal planning
- production deployment work
- workout-plan persistence changes
- actual-set logging changes
- substitution behavior changes
- recommendation response-shape changes
- external exercise imports
- exercise media

## Architecture request

Before implementation begins, Architecture should confirm:

1. Whether the proposed CandidateWorkoutPlan JSON shape is sufficient for v1.
2. Whether `catalog_exercise_id`, `movement_pattern`, and `target_zone` should become durable model fields or remain validation-only at first.
3. Whether CrewAI workout candidates should use the same isolated subprocess strategy as recommendation candidates.
4. Whether debug metadata should be added through a separate route before runtime implementation.
5. Whether the normal workout preview response shape must remain unchanged for the first CrewAI workout milestone.
