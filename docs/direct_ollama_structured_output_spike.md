# Direct Ollama Structured Output Spike v1

## Purpose

This document records the Direct Ollama Structured Output Spike v1 investigation.

The spike tests whether a lower-level direct Ollama structured-output call can produce exact `CandidateNutritionExplanation` JSON more reliably than the CrewAI-wrapped nutrition explanation provider.

## Accepted architecture

```text
approved backend context
→ provider attempts bounded JSON
→ strict parser
→ validator
→ approved explanation or deterministic fallback
```

## Scope boundaries

This spike does **not** change production provider behavior.

Preserved boundaries:

- Deterministic nutrition explanation remains default.
- CrewAI nutrition explanation remains debug-only.
- Normal public endpoints are unchanged.
- Parser behavior is unchanged.
- Validator behavior is unchanged.
- Approval rules are unchanged.
- No markdown extraction is accepted.
- No code-fence stripping is accepted.
- No wrapper-object acceptance is added.
- No extra-key acceptance is added.
- No Streamlit provider controls are added.

## Implementation

Spike script:

```text
scripts/spike_direct_ollama_nutrition_explanation.py
```

The script:

1. Builds the existing approved nutrition explanation context.
2. Reuses the compressed nutrition explanation provider prompt.
3. Calls Ollama `/api/generate` directly.
4. Sends the exact `CandidateNutritionExplanation` JSON schema through Ollama's `format` field.
5. Evaluates the raw model response using the existing strict parser/validator/fallback boundary.
6. Emits debug-only spike metadata as JSON.

Ollama documentation states that `/api/generate` supports structured output via `format`, either as the string `"json"` or as a JSON schema object. The structured-output docs also recommend passing the schema in the prompt to ground the response.

## Manual usage

From the Linux runtime repo:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate
export OLLAMA_BASE_URL=http://192.168.1.104:11434

python scripts/spike_direct_ollama_nutrition_explanation.py \
  --model ollama/qwen2.5:3b \
  --user-id 102 \
  --date 2026-06-06 | jq
```

The script accepts CrewAI-style `ollama/<model>` names and normalizes them for direct Ollama REST calls.

Example:

```text
configured_model: ollama/qwen2.5:3b
selected_model: qwen2.5:3b
```

## Trial matrix

| Model | Runtime | Parse status | Validation status | Fallback reason | Notes |
|---|---:|---|---|---|---|
| `ollama/qwen2.5:3b` | TODO | TODO | TODO | TODO | TODO |
| `ollama/gemma3n:e4b` | TODO | TODO | TODO | TODO | TODO |
| `ollama/hermes3:3b` | TODO | TODO | TODO | TODO | TODO |
| `ollama/gemma3:4b` | TODO | TODO | TODO | TODO | Optional |
| `ollama/llama3.2:3b` | TODO | TODO | TODO | TODO | Optional |

Avoid for this spike unless intentionally testing ceiling behavior:

- `ollama/qwen3:8b`
- `ollama/qwen2.5:7b`
- `ollama/hermes3:8b`

The previous CPU-only `qwen3:8b` CrewAI-wrapped trial was manually stopped at 52m34s and is not useful for normal interactive UX.

## Result fields to record

For each model, record:

- configured_model
- selected_model
- elapsed_seconds
- candidate_parse_status
- candidate_validation_status
- validation_status
- candidate_valid
- fallback_used
- fallback_reason
- final_explanation_source
- raw_output_length
- markdown_wrapper_detected
- extra_keys_detected
- wrapper_object_detected
- validation_errors

## Success criteria

PASS if direct Ollama structured output:

- returns raw JSON only
- parses into exact `CandidateNutritionExplanation`
- validates successfully
- has no extra keys
- has no wrapper objects
- has no markdown/code fences
- has no display flags
- has no date fields
- has no formula metadata
- is materially faster or more schema-adherent than CrewAI-wrapped trials

## Failure criteria

FAIL if direct Ollama still emits:

- markdown/code fences
- wrapper objects
- extra keys
- date/display/formula metadata
- prose instead of JSON
- invalid schema output
- runtime too slow for practical use

## Recommendation placeholder

TODO after manual runtime trials.

If direct Ollama structured output succeeds, route a separate milestone:

```text
Direct Ollama Nutrition Explanation Provider v1
```

If direct Ollama structured output fails, pause live local provider work and continue deterministic nutrition explanation enrichment.
