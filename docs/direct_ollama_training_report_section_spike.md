# Direct Ollama Training Report Section Spike v1

## Status

Implemented as an isolated spike.

This does not change production health report behavior, report persistence, Streamlit, or full report assembly.

## Goal

Evaluate whether the accepted direct structured-output pattern can generate a bounded training health report section from backend-approved workout and training execution context.

Accepted pattern:

```text
approved backend context
→ direct structured AI candidate
→ strict parser
→ strict validator
→ approved output or deterministic fallback
```

## Scope

The spike starts with one section only:

- training

The spike script is:

```text
scripts/spike_direct_ollama_training_report_section.py
```

Automated tests are mocked and do not call live Ollama:

```text
tests/test_direct_ollama_training_report_section_spike.py
```

## Candidate schema

The provider must return exactly this JSON object shape:

```json
{
  "section_summary": "string",
  "key_observations": ["string"],
  "performance_interpretation": "string",
  "fatigue_recovery_interpretation": "string",
  "suggested_focus": "string",
  "limitations_context": "string",
  "confidence": "Limited | Low | Moderate | High",
  "reason_codes": ["string"]
}
```

Allowed confidence values:

- Limited
- Low
- Moderate
- High

## Backend-approved context

The spike builds bounded training context from existing backend-owned sources:

- `UserHealthState.training_state`
- `UserHealthState.recovery_state`
- `TrainingExecutionSummary`
- recent completed planned workout execution rows, when available

The context may include bounded public-safe fields such as:

- workout title
- planned exercise name
- planned sets
- planned rep range
- planned RIR range
- actual exercise name
- set number
- actual reps
- actual weight
- actual RIR
- completed/skipped flags
- execution quality
- effort trend
- completion trend
- confidence
- reason codes

The context intentionally does not include raw provider output, raw model metadata, unbounded source payloads, or production report internals.

## Prompt rules

The prompt instructs the model to:

- return JSON only
- include exactly the allowed keys
- mention workout names only when present in approved context
- mention exercise names only when present in approved context
- quote set, rep, load, weight, and RIR values only when exact values appear in approved context
- avoid inventing workouts, exercises, sets, reps, loads, weights, RIR, progression, fatigue, recovery status, or health metrics
- avoid medical claims
- avoid workout-plan creation or recommendation mutation
- keep the section concise and user-facing

## Parser behavior

The parser rejects:

- empty output
- malformed JSON
- markdown/code fences
- wrapper objects
- missing required fields
- extra keys
- non-string scalar fields
- non-array list fields

No messy JSON extraction is performed.

## Validator behavior

The validator enforces:

- required text fields are non-empty
- key observations are present and bounded
- confidence is allowed
- reason codes are non-empty strings
- no markdown code fences inside text fields
- no internal implementation terms
- no medical claims
- no unsupported progression or workout prescriptions
- no unapproved numbers
- candidate text mentions at least one approved workout/exercise name when detailed training context exists
- vague training copy is rejected when detailed training context exists
- known unapproved training names are rejected where feasible

Invalid candidates return deterministic fallback.

## Runtime diagnostics

The spike records:

- configured_model
- selected_model
- elapsed_seconds
- candidate_parse_status
- candidate_validation_status
- validation_status
- candidate_valid
- fallback_used
- fallback_reason
- final_section_source
- raw_output_length
- raw_output_preview_truncated
- markdown_wrapper_detected
- extra_keys_detected
- wrapper_object_detected

## Manual runtime command

Use Linux FastAPI/runtime environment with Windows Ollama host available.

```bash
export OLLAMA_BASE_URL=http://192.168.1.104:11434

python scripts/spike_direct_ollama_training_report_section.py \
  --model ollama/qwen2.5:3b \
  --user-id 102 \
  --date 2026-06-06 \
  --ollama-base-url "$OLLAMA_BASE_URL" \
  --timeout-seconds 120 | jq
```

Optional model matrix:

```bash
for model in \
  ollama/qwen2.5:3b \
  ollama/hermes3:3b \
  ollama/qwen3:8b
 do
  echo "=== $model ==="
  python scripts/spike_direct_ollama_training_report_section.py \
    --model "$model" \
    --user-id 102 \
    --date 2026-06-06 \
    --ollama-base-url "$OLLAMA_BASE_URL" \
    --timeout-seconds 180 | jq '{
      success,
      configured_model,
      selected_model,
      elapsed_seconds,
      candidate_parse_status,
      candidate_validation_status,
      validation_status,
      fallback_used,
      fallback_reason,
      final_section_source,
      raw_output_length,
      markdown_wrapper_detected,
      extra_keys_detected,
      wrapper_object_detected
    }'
done
```

## Acceptance criteria

The spike is successful if:

- at least one training section can be generated as strict JSON
- output parses into the exact candidate schema
- validator approves valid output
- invalid output falls back deterministically
- markdown/code fences are rejected
- wrapper objects are rejected
- extra keys are rejected
- invented workout/exercise/set/load/reps/RIR values are rejected where feasible
- output is specific when approved training data exists
- no medical claims are allowed
- diagnostics are recorded
- tests do not call live Ollama

## Non-goals

- no production training report provider
- no full report replacement
- no report UI changes
- no report persistence changes
- no async job system
- no parser relaxation
- no Streamlit provider controls
- no workout generation changes
- no CrewAI removal

## Decision fork

If runtime QA passes:

- route `Direct Ollama Training Report Section Provider v1`

If runtime QA fails:

- keep training report deterministic
- improve approved training context and validator design before production provider work
