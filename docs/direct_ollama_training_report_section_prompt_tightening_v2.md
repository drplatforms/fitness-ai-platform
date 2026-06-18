# Direct Ollama Training Report Section Prompt Tightening v2

## Status

Implemented as a spike-only prompt and validator tightening pass after `Direct Ollama Training Report Section Grounding Context v1`.

This milestone does not add a production training report provider, does not wire the training section into full report assembly, does not change Streamlit, and does not change report persistence.

## Background

Grounding Context v1 added rich `approved_training_quote_context` output with approved workout names, exercise names, numbers, set/rep/load/RIR values, and summary facts.

Runtime QA with `ollama/qwen2.5:3b` showed that the context existed, but the model still treated the task like a general training summary. It wrote phrases such as:

- `Training Execution Summary for User 102 on June 6th`
- `4 out of 5 workouts were completed as planned`
- `trend towards lower effort`
- `one exercise was skipped`
- `adherence at High level`

The validator correctly rejected that output and deterministic fallback activated.

The v2 goal is not more context and not looser validation. The goal is quote-first prompt behavior and stricter rejection of unapproved metadata, trends, adherence, skipped-exercise, and completion-count claims.

## Prompt changes

The prompt now places quote requirements before the broader context payload:

- approved workout names appear near the top
- approved exercise names appear near the top
- a required quote name is selected from the approved names
- the model is told to quote at least one exact approved workout or exercise name
- the model is told every narrative field should mention an approved workout or exercise name when names exist
- the model is told to use `approved_training_summary_facts` as source text

The prompt explicitly forbids:

- user_id
- user numbers
- user metadata
- report dates
- runtime/provider metadata
- adherence summaries
- trend summaries
- skipped-exercise summaries
- completion-count summaries
- progression, fatigue, or recovery summaries unless exact approved facts support them

The prompt also includes model-facing anti-pattern examples:

Bad:

- `Training Execution Summary for User 102`
- `4 out of 5 workouts were completed`
- `training is progressing well`
- `adherence is high`
- `one exercise was skipped`
- `there was a trend toward lower effort`

Good when approved facts exist:

- `Romanian Deadlift was logged at 135 lb for 7, 7, 7 reps.`
- `The final Dumbbell Floor Press set was logged at 0 RIR.`
- `Gradual Progression Strength Session was completed.`
- `One-Arm Dumbbell Row was logged at 78 lb for 7, 7 reps.`

## Validator changes

Validation now rejects additional unapproved output patterns:

- user metadata leakage, including `User 102`, `user_id`, `for user`, `this user`, and report-date phrasing
- narrative fields that omit approved workout/exercise names when quote context exists
- completion-count and adherence claims such as `4 out of 5`, `completed as planned`, and `adherence`
- skipped-exercise claims such as `skipped`, `missed`, `not completed`, and `omitted`
- trend/consistency claims such as `trend`, `trending`, `lower effort`, `improving`, `stable`, and `consistent`
- generic training-quality claims such as `training is progressing well` and `performance is stable`

Existing validation remains in place:

- strict JSON schema
- no markdown/code fences
- no wrapper objects
- no extra keys
- no internal/provider/debug terms
- no medical claims
- no unsupported workout prescriptions
- no unapproved numbers
- no invented workout or exercise names
- no invented volume load
- no invented average RIR
- no invented percentage/progression claims
- no invented fatigue/recovery conclusions

## Tests

The focused training spike test suite now covers:

- prompt places approved names before broader context
- prompt forbids user metadata
- prompt includes a required quote-name rule
- candidate mentioning `User 102` fails validation
- candidate mentioning report date fails validation
- candidate saying `4 out of 5 workouts` fails validation
- candidate saying `adherence is high` fails validation
- candidate saying `one exercise was skipped` fails validation
- candidate saying `trend toward lower effort` fails validation
- each narrative field must mention approved names when quote context exists
- approved workout/exercise fact copy can still pass
- generic training copy still fails
- deterministic fallback remains safe

## Scope boundaries

Preserved:

- no production training section provider
- no full report assembly wiring
- no report persistence changes
- no Streamlit changes
- no workout generation changes
- no CrewAI behavior changes
- no live Ollama calls in pytest

## Runtime QA recommendation

Run qwen2.5 first after this patch:

```bash
export OLLAMA_BASE_URL=http://192.168.1.104:11434

python scripts/spike_direct_ollama_training_report_section.py \
  --model ollama/qwen2.5:3b \
  --user-id 102 \
  --date 2026-06-06 \
  --ollama-base-url "$OLLAMA_BASE_URL" \
  --timeout-seconds 240 | jq
```

Do not run qwen3 again until qwen2.5 has been tested after the v2 tightening pass.

## Decision fork

If runtime reaches `provider_approved` with quote-first grounded copy:

- consider `Direct Ollama Training Report Section Provider v1` design

If runtime still falls back:

- inspect whether the model ignored required quote-name rules
- consider a smaller prompt iteration or a different local model
- do not loosen validation
