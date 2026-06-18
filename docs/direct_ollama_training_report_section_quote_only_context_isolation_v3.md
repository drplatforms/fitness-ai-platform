# Direct Ollama Training Report Section Quote-Only Context Isolation v3

## Status

Implemented as a spike-only model-facing context isolation pass after Prompt Tightening v2.

Runtime QA showed that Prompt Tightening v2 improved rejection quality, but `qwen2.5:3b` still produced the same unapproved summary style when it could see broader training context. The next bottleneck was prompt input contamination, not missing quote facts or weak validator rules.

## Decision

Keep the richer backend/debug context available internally, but do not send it to the model.

The model-facing prompt now receives a smaller quote-only payload derived from `ApprovedTrainingQuoteContext`:

- `required_quote_name`
- `approved_workout_names`
- `approved_exercise_names`
- `approved_training_numbers`
- `approved_quote_facts`
- `coaching_intent`
- `tone_guidance`
- `section_contract_reminder`

The prompt no longer serializes the full backend `approved_context` block.

## What the model no longer sees

The quote-only payload excludes:

- `user_id`
- `report_date`
- runtime/provider metadata
- raw training state
- raw training execution summary
- raw recent execution rows
- raw actual-set rows
- raw notes
- broad adherence summaries
- broad trend summaries
- skipped-exercise summaries unless explicitly present as approved quote facts

## Coaching-language rule

The model is still expected to sound like a useful coach, not a static renderer.

The prompt tells the model not to merely repeat approved facts as a list. It may prioritize, phrase, and connect approved facts naturally, but every factual claim must be supported by approved quote facts, approved names, or approved numbers.

## Validation

Prompt Tightening v2 validation remains active:

- required approved name grounding
- per-field approved-name grounding
- user metadata rejection
- report-date rejection
- unapproved completion/adherence rejection
- unapproved skipped-exercise rejection
- unapproved trend/consistency rejection
- unapproved fatigue/recovery/progression rejection
- unapproved number rejection
- invented workout/exercise rejection
- deterministic fallback on any validation failure

V3 adds an explicit `model_facing_quote_context` field to spike output so runtime QA can verify what the model was actually allowed to see.

## Non-goals

This remains spike-only.

Do not:

- promote a production provider yet
- wire into full report assembly
- change Streamlit
- change report persistence
- change workout generation
- loosen parser behavior
- loosen validator behavior
- call live Ollama in pytest

## Runtime QA expectation

After v3, `qwen2.5:3b` should no longer have access to user/date/runtime or broad training summary metadata in the prompt. It should either:

1. pass by producing coach-like copy grounded in approved quote facts, or
2. fail validation and fall back deterministically.

Either outcome remains safe. Provider promotion still requires live provider-approved output or a clearly understood remaining failure mode.
