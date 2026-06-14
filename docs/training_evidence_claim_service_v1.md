# Training Evidence Claim Service v1

## Status

Implemented as a reusable backend evidence layer before full training report integration.

## Purpose

`Training Evidence Claim Service v1` extracts bounded training claim derivation out of the direct-Ollama training report provider path.

The service gives report providers and deterministic fallback code a shared source of approved training evidence without letting AI infer freely.

Core pattern:

```text
completed workout / logged training data
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ model-facing context
→ strict validator
→ approved training report section or deterministic fallback
```

A future milestone can connect `TrainingExecutionSummary` as the long-term source of training execution truth. For v1, the service can be built from the existing approved training quote context used by the direct-Ollama provider.

## Product principle

Backend owns truth.
AI explains approved truth.
Validator enforces reality.

The coach should sound more human because it has more approved evidence to talk about, not because the model is allowed to make unsupported claims.

## Added models

`models/training_evidence_claim_models.py`

### TrainingEvidenceContext

Reusable context for backend-approved training evidence.

Fields include:

- `workout_names`
- `exercise_names`
- `set_rep_load_rir_values`
- `training_summary_facts`
- `required_quote_name`
- `required_fact_anchors`
- `source`

### ApprovedTrainingClaim

Represents one backend-approved bounded training claim.

Fields include:

- `claim_id`
- `claim_type`
- `approved_meaning`
- `required_names`
- `required_terms`
- `allowed_terms`
- `forbidden_scope`
- `source_fact_refs`
- `scope`
- `confidence`
- `public_safe`

### TrainingClaimValidationResult

Reusable result for validating whether a short phrase stays inside approved training claim scope.

Fields:

- `claim_valid`
- `validation_errors`

## Added service

`services/training_evidence_claim_service.py`

Primary functions:

- `build_training_evidence_context_from_quote_context(...)`
- `derive_approved_training_claims(...)`
- `derive_approved_training_claim_dicts(...)`
- `validate_training_claim_language(...)`

The direct-Ollama training report section still receives the same `approved_bounded_training_claims` payload shape, but derivation now flows through this reusable service boundary.

## Claim types for v1

### single_session_rep_pattern

Generated only when all logged sets for one exercise share the same rep count.

Example approved meaning:

```text
Romanian Deadlift used the same rep count across all logged sets in this session.
```

Allowed language:

- same rep count across the logged sets
- steady reps in this session
- consistent rep counts within this workout

Rejected language:

- you are consistent
- consistent performance
- consistency over time
- progression trend
- improving consistency

### single_session_effort

Generated only when the final logged RIR for an exercise is `0` or `1`.

Example approved meaning:

```text
Dumbbell Floor Press finished with a final set at 0 RIR, so effort was high within this logged session.
```

Allowed language:

- close to failure based on the logged RIR
- high effort within this session
- effort context from the logged RIR

Rejected language:

- great effort overall
- consistently strong effort
- recovery handled it well
- fatigue is managed
- strong execution
- good form

### complete_reference_lift

Generated only when logged load, reps, sets, and RIR are available.

Example approved meaning:

```text
Romanian Deadlift and Dumbbell Floor Press are the strongest reference lifts in this session because they have complete logged training details.
```

Allowed language:

- reference lifts from this workout
- clearest signal from the session
- use these as anchors for the next training decision

Rejected language:

- proves progress
- proves the plan worked
- shows recovery is good
- shows form is strong

### scope_limit

Generated when the section is based on one workout/session.

Example approved meaning:

```text
Gradual Progression Strength Session is a single-session observation and should not be treated as a trend.
```

Allowed language:

- single-session reference point
- useful but not enough to call it a trend
- one workout can guide the next choice, not prove the bigger pattern

Rejected language:

- progression confirmed
- recovery pattern
- fatigue pattern
- consistent improvement

## Validator direction

The service-level validator does not replace the direct-Ollama section validator. It provides reusable claim-scope validation that future integrations can use.

Continue rejecting:

- broad consistency claims
- broad effort claims
- unsupported recovery/fatigue claims
- unsupported form/control claims
- unsupported progression claims
- unsupported plan-alignment claims
- unsupported adherence/completion claims
- invented workout names
- invented exercise names
- unapproved numbers
- debug/meta/internal copy

Allow bounded language only when backed by `ApprovedTrainingClaim` entries.

## Integration status

This milestone does not fully integrate the direct-Ollama training section into full report generation.

Current integration remains conservative:

- deterministic remains default
- direct-Ollama remains opt-in
- qwen2.5:3b remains the supported model for this section
- qwen3 remains experimental/product-voice probe only
- strict fallback remains mandatory
- raw model output is not persisted
- raw provider output is not public

## Future integration path

Recommended follow-up sequence:

1. Keep provider baseline stable.
2. Reuse `ApprovedTrainingClaim[]` in deterministic fallback and direct-Ollama contexts.
3. Connect `TrainingExecutionSummary` as the long-term source of training execution truth.
4. Only then consider full report training-section integration.
5. Revisit product voice after the evidence layer is stable.


## Anchor-preservation rule

`ApprovedTrainingClaim[]` enriches the model-facing context, but it must not replace the exact required fact anchors.

Provider prompt/payload construction must keep this order of authority:

1. exact required training details
2. `key_observations` exact-copy rules
3. approved bounded training claims
4. interpretation claims and semantic coaching moves
5. forbidden claim boundaries
6. JSON output contract

`key_observations[0]` and `key_observations[1]` must copy exact required training details character-for-character when anchors are available.

The provider should continue rejecting:

- paraphrased anchors
- planned-only details used as required observations when not listed as required anchors
- unsupported progression claims such as “progression in load and reps”
- broad consistency, recovery, fatigue, form, control, plan-success, or adherence claims

The claim service exists to make approved evidence reusable, not to make the model less accountable to exact anchors.
