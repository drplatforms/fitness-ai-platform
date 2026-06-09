# Direct Ollama Training Report Section Grounding Context v1

## Status

Implemented as a spike-only grounding improvement for the direct Ollama training report section.

This milestone does not add a production training report provider, does not wire the training section into full report assembly, does not change Streamlit, and does not change report persistence.

## Background

`Direct Ollama Training Report Section Spike v1` proved that direct Ollama can return strict JSON for the training section contract, and that strict parsing, validation, diagnostics, and deterministic fallback all work.

Manual runtime QA also showed that tested live models produced generic training copy or invented unsupported numbers instead of quoting approved workout/exercise details. That result was accepted as a partial pass and routed to a grounding-context improvement rather than validator relaxation.

## Goal

Provide explicit backend-approved, quoteable training context so the provider can produce specific training-section copy without inventing workouts, exercises, sets, reps, loads, RIR values, progression, fatigue, or recovery claims.

Accepted pattern remains:

```text
approved backend context
â†’ direct structured AI candidate
â†’ strict parser
â†’ validator
â†’ approved output or deterministic fallback
```

## ApprovedTrainingQuoteContext

The spike now builds and exposes a bounded quote context:

```json
{
  "approved_workout_names": ["Upper Body Strength"],
  "approved_exercise_names": ["Dumbbell Bench Press"],
  "approved_training_numbers": [1, 2, 3, 8, 10, 50],
  "approved_set_rep_load_rir_values": [
    {
      "workout_name": "Upper Body Strength",
      "exercise_name": "Dumbbell Bench Press",
      "planned_sets": 3,
      "planned_reps": "8-10",
      "planned_rir": "2-3",
      "actual_sets": 1,
      "actual_reps": [10],
      "actual_load_lb": 50,
      "actual_rir": [1]
    }
  ],
  "approved_training_summary_facts": [
    "Upper Body Strength was completed.",
    "Dumbbell Bench Press was logged at 50 lb for 10 reps.",
    "The final Dumbbell Bench Press set was logged at 1 RIR."
  ]
}
```

The quote context is built only from backend-approved training execution data.

It intentionally excludes:

- raw actual-set database rows
- raw notes
- unbounded workout history
- provider/internal metadata
- raw model output
- values not explicitly approved for quotation

## Prompt behavior

The prompt now directs the model to use `approved_training_quote_context` for exact training details.

Provider rules:

- mention at least one exact approved workout or exercise name when names are available
- quote only workout names from `approved_workout_names`
- quote only exercise names from `approved_exercise_names`
- quote only numbers from `approved_training_numbers` or approved summary facts
- restate facts only from `approved_training_summary_facts`
- do not calculate volume load
- do not calculate average RIR
- do not invent percentages or week-over-week changes
- do not infer progression, fatigue, or recovery status unless the exact fact is approved
- return only the required JSON object
- no markdown, code fences, wrapper objects, or extra keys

## Candidate schema

The strict candidate schema remains unchanged:

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

## Validation behavior

Validation now uses the explicit quote context as the approved grounding source.

Rules:

- if approved workout or exercise names exist, candidate output must mention at least one exact approved name
- candidate output must not rely on generic training copy when quoteable details exist
- numbers in candidate output must exist in the approved quote context
- known unapproved workout/exercise names are rejected where feasible
- invented volume-load claims are rejected
- invented average-RIR claims are rejected
- invented percentage/progression claims are rejected
- invented fatigue/recovery conclusions are rejected unless backed by approved summary facts
- deterministic fallback remains the response on any parse or validation failure

## Diagnostics/debug output

The spike result now includes sanitized quote context as:

```text
approved_training_quote_context
```

This allows runtime QA to confirm exactly which names, numbers, and facts were approved for model quotation.

## Scope boundaries

Preserved:

- no production training section provider
- no full report assembly wiring
- no report persistence changes
- no Streamlit changes
- no workout generation changes
- no CrewAI behavior changes
- no live Ollama calls in pytest
- deterministic fallback remains safe

## Manual runtime command

```bash
export OLLAMA_BASE_URL=http://192.168.1.104:11434

python scripts/spike_direct_ollama_training_report_section.py \
  --model ollama/qwen2.5:3b \
  --user-id 102 \
  --date 2026-06-06 \
  --ollama-base-url "$OLLAMA_BASE_URL" \
  --timeout-seconds 240 | jq
```

Runtime QA should inspect:

- `approved_training_quote_context`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_status`
- `fallback_used`
- `fallback_reason`
- `final_section_source`
- `validation_errors`

## Decision fork

If live runtime reaches `provider_approved` with grounded training copy:

- route `Direct Ollama Training Report Section Provider v1`

If live runtime still falls back:

- inspect `approved_training_quote_context`
- tighten context/prompt before provider promotion
- do not loosen validation just to approve generic training copy


## Follow-up runtime QA result

After Grounding Context v1, runtime QA with `ollama/qwen2.5:3b` confirmed that `approved_training_quote_context` was present and rich, but the model still wrote generic/user-metadata training summary copy instead of quote-first approved facts.

Rejected examples included:

- `Training Execution Summary for User 102 on June 6th`
- `4 out of 5 workouts were completed as planned`
- `trend towards lower effort`
- `One exercise was skipped`
- `adherence at High level`

This result routed the next milestone to `Direct Ollama Training Report Section Prompt Tightening v2`.

## Follow-up: Quote-Only Context Isolation v3

Prompt Tightening v2 improved rejection quality but did not change `qwen2.5:3b` output behavior. The model still summarized broader context when the full backend approved context was serialized into the prompt.

Quote-Only Context Isolation v3 keeps the richer backend/debug context available, but sends only a derived quote-only payload to the model. This payload contains approved names, approved numbers, approved quote facts, a required quote name, and coaching/tone guidance. It excludes user IDs, report dates, raw execution rows, raw summaries, runtime metadata, and other broad context that could invite unsupported summarization.

## Follow-up: Fact-Anchored Output v4

Quote-Only Context Isolation v3 removed contaminated model input and improved qwen2.5 behavior, but runtime QA still showed under-anchored copy and unsupported phrasing such as "completed as planned." Fact-Anchored Output v4 keeps quote-only isolation and adds prioritized `required_fact_anchors`, `required_anchor_count`, exact-anchor validation, and meta-copy rejection.

## Follow-up: Anchor-First Payload v4.1

Fact-Anchored Output v4 made the anchor mechanism active, but live qwen2.5 and hermes3 runs still failed provider approval. The models used the approved workout name and stayed in the training domain, but they either selected optional/planned facts instead of required logged-performance anchors or echoed meta-copy such as "approved facts."

Anchor-First Payload v4.1 keeps quote-only isolation and required fact anchors, but makes the required anchors the dominant prompt block. The actual prompt no longer dumps the full model-facing JSON payload and no longer exposes `forbidden_meta_terms` to the model. Forbidden/meta terms remain backend-side validation concerns only.

v4.1 also requires the first two key observations to be exact, different required training details when at least two anchors are available, and the spike output exposes matched-anchor diagnostics for runtime QA.

## Claim-Safe Interpretation v4.2 follow-up

Anchor-First Payload v4.1 solved required anchor placement in at least one live qwen2.5 run, but repeated qwen2.5 and qwen3:8b runs showed provider approval was not stable. Models could place the exact required anchors and then invent unsupported interpretation around them.

Claim-Safe Interpretation v4.2 keeps quote-only context and anchor-first observations, then adds backend-approved interpretation claims plus conservative validation for unsupported consistency, progression, form/control, fatigue/recovery, planned-alignment, adherence, and completion claims.

Exact anchors are now necessary but not sufficient. The interpretation fields must stay within backend-approved claim boundaries or fall back deterministically.
