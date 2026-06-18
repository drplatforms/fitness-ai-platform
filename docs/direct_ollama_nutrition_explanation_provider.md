# Direct Ollama Nutrition Explanation Provider v1

## Status

Implemented as an optional nutrition explanation provider.

Default provider remains deterministic.

## Provider options

`NUTRITION_EXPLANATION_PROVIDER` accepts:

- `deterministic`
- `crewai`
- `direct_ollama`

Recommended experimental provider:

```text
NUTRITION_EXPLANATION_PROVIDER=direct_ollama
```

## Runtime configuration

```text
NUTRITION_EXPLANATION_PROVIDER=direct_ollama
NUTRITION_EXPLANATION_MODEL=ollama/qwen2.5:3b
OLLAMA_BASE_URL=http://192.168.1.104:11434
NUTRITION_EXPLANATION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
```

The provider accepts CrewAI-style Ollama model names such as `ollama/qwen2.5:3b`
and normalizes the selected direct Ollama model to `qwen2.5:3b` for the REST call.

## Behavior

The direct provider calls Ollama `/api/generate` with:

- `stream: false`
- `temperature: 0`
- JSON-schema structured output through the `format` field
- the existing compressed approved nutrition explanation context
- the existing `CandidateNutritionExplanation` contract

Provider output remains untrusted. It must pass the existing strict parser and
validator before it can become approved output.

## Safety boundaries preserved

The provider does not change:

- deterministic default behavior
- parser behavior
- validator behavior
- approval rules
- normal public preview response shape
- target calculations
- food suggestion calculations
- report generation
- workout behavior
- Streamlit provider controls

Normal preview responses do not expose runtime metadata, configured model, selected
model, raw output, or provider internals.

## Failure handling

The provider falls back deterministically for:

- timeout
- connection error
- non-200 HTTP response
- malformed Ollama response payload
- missing response text
- parse failure
- validation failure
- unexpected provider exception

Fallback responses remain public-safe. Failure details stay in debug-only runtime
metadata.

## Debug metadata

The debug endpoint may show:

- `configured_provider`
- `selected_provider`
- `configured_model`
- `selected_model`
- `provider_attempted`
- `fallback_used`
- `fallback_reason`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_status`
- `final_explanation_source`
- `raw_output_length`
- `markdown_wrapper_detected`
- `raw_output_preview_truncated`

## Manual validation

```bash
export OLLAMA_BASE_URL=http://192.168.1.104:11434
export NUTRITION_EXPLANATION_PROVIDER=direct_ollama
export NUTRITION_EXPLANATION_MODEL=ollama/qwen2.5:3b

curl -s "http://127.0.0.1:8000/nutrition/102/explanation/debug?date=2026-06-06" | jq '.runtime_metadata'

curl -s "http://127.0.0.1:8000/nutrition/102/explanation/preview?date=2026-06-06" | jq
```

The debug response should show `selected_provider: direct_ollama` and model
metadata. The normal preview response must not expose runtime metadata.
