# Direct Ollama Health Report Section Spike v1

## Summary

This spike evaluates whether the successful direct Ollama structured-output pattern used by nutrition explanations can improve Full AI Health Report generation through bounded section-level candidates.

This is a spike only. It does not replace the production health report pipeline.

Accepted architecture pattern:

```text
approved backend context
→ direct structured AI candidate
→ strict parser
→ validator
→ approved output or deterministic fallback
```

## Why section-level generation

The spike intentionally does not ask a model to write the entire health report as one free-form blob.

Instead, it starts with a single nutrition report section because the nutrition explanation path already has:

- deterministic backend source of truth
- direct Ollama structured output
- strict parser behavior
- strict validator behavior
- deterministic fallback
- value-aware nutrition copy
- approved food suggestion candidate grounding
- debug-only runtime visibility
- clean public preview behavior

## Scope

Added isolated script:

```text
scripts/spike_direct_ollama_health_report_sections.py
```

Added mocked tests:

```text
tests/test_direct_ollama_health_report_section_spike.py
```

The script currently supports the nutrition section only.

## Candidate section contract

The spike requires this exact JSON object:

```json
{
  "section_summary": "string",
  "key_observations": ["string"],
  "coaching_interpretation": "string",
  "suggested_focus": "string",
  "limitations_context": "string",
  "confidence": "Limited | Low | Moderate | High",
  "reason_codes": ["string"]
}
```

No extra keys are accepted.

No wrapper objects are accepted.

Markdown/code-fenced JSON is rejected.

## Approved context

The nutrition section spike builds bounded backend-approved context from:

- UserHealthState
- CoachingDecision
- NutritionExplanationContext
- compressed/value-aware nutrition context
- approved target/logging/gap/food suggestion context already prepared for nutrition explanation providers

The model receives approved context only.

## Backend source-of-truth boundary

Backend remains source of truth for:

- nutrition targets
- logged actuals
- macro gaps
- food suggestions
- recovery status
- training load
- workout execution summaries
- trend interpretation
- confidence
- data completeness
- safety limits
- report assembly
- validation
- fallback

AI may generate:

- clearer section explanations
- coaching tone
- user-friendly interpretation
- concise action framing

AI may not:

- invent targets
- invent logged values
- invent workouts
- invent nutrition values
- invent health metrics
- make medical claims
- mutate backend recommendations
- output markdown
- output wrapper objects
- output extra keys

## Diagnostics recorded

The spike records:

- configured_model
- selected_model
- elapsed_seconds
- candidate_parse_status
- candidate_validation_status
- validation_status
- fallback_used
- fallback_reason
- raw_output_length
- raw_output_preview_truncated
- markdown_wrapper_detected
- extra_keys_detected
- wrapper_object_detected

## Manual runtime command

Example first runtime test:

```bash
export OLLAMA_BASE_URL=http://192.168.1.104:11434

python scripts/spike_direct_ollama_health_report_sections.py \
  --model ollama/qwen2.5:3b \
  --user-id 102 \
  --date 2026-06-06 \
  --section nutrition \
  --ollama-base-url "$OLLAMA_BASE_URL" \
  --timeout-seconds 120 | jq
```

Suggested model matrix:

- ollama/qwen2.5:3b
- ollama/gemma3n:e4b
- ollama/hermes3:3b
- ollama/qwen3:8b

## Automated test policy

Automated tests mock the direct Ollama call.

Tests must not call live Ollama or CrewAI.

## Decision fork

If the spike succeeds, a future milestone may be:

```text
Direct Ollama Health Report Section Provider v1
```

If the spike fails, keep full health report generation deterministic for now and continue using direct_ollama only for nutrition explanation.

## Non-goals

- no production health report provider switch
- no full report replacement
- no async job implementation
- no report UI changes
- no parser relaxation
- no messy JSON extraction
- no medical advice expansion
- no nutrition target changes
- no workout changes
- no Streamlit provider controls
