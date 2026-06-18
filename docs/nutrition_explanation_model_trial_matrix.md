# Nutrition Explanation Provider Model Trial Matrix v1

## Purpose

The optional nutrition explanation provider is allowed to draft only `CandidateNutritionExplanation` JSON. Backend parser and validator behavior remains strict. Provider output is never rendered directly, extra fields are rejected, malformed JSON falls back, and deterministic output remains the default.

This matrix is for runtime QA only. It helps compare local model schema adherence and latency after provider-facing context compression.

## Current provider policy

- Default provider: `deterministic`
- Optional runtime provider: `crewai`
- Provider input: compressed approved nutrition explanation context only
- Provider output: raw `CandidateNutritionExplanation` JSON only
- Normal preview response: public-safe approved explanation only
- Debug route: runtime metadata only, no normal UI exposure

## Exact accepted provider output schema

```json
{
  "explanation_summary": "string",
  "macro_context": "string or null",
  "food_suggestion_context": "string or null",
  "trend_context": "string or null",
  "calibration_context": "string or null",
  "limitations_context": "string or null",
  "confidence": "Limited | Low | Moderate | High",
  "reason_codes": ["string"]
}
```

Any extra top-level key must fail parsing and fall back deterministically.

## Known invalid fields to track

Track whether the model still emits any of these unapproved fields:

- `displayFlags`
- `display_flags`
- `explanationDate`
- `explanation_date`
- `allow_calorie_targets`
- `allow_carbohydrate_targets`
- `allow_fat_targets`
- `allow_protein_targets`
- markdown/code fence wrapper
- any target/display/formula/provider/runtime/debug metadata

## Runtime QA setup

Use the debug endpoint so provider metadata remains developer-only:

```powershell
$env:NUTRITION_EXPLANATION_PROVIDER="crewai"
$env:OLLAMA_BASE_URL="http://192.168.1.104:11434"
```

For each model trial:

```powershell
$env:NUTRITION_EXPLANATION_MODEL="ollama/qwen2.5:3b"
```

Then test representative seeded users:

```powershell
Measure-Command { Invoke-RestMethod "http://localhost:8000/nutrition/102/explanation/debug?date=2026-06-06" }
Measure-Command { Invoke-RestMethod "http://localhost:8000/nutrition/103/explanation/debug?date=2026-06-06" }
Measure-Command { Invoke-RestMethod "http://localhost:8000/nutrition/104/explanation/debug?date=2026-06-06" }
Measure-Command { Invoke-RestMethod "http://localhost:8000/nutrition/105/explanation/debug?date=2026-06-06" }
```

Reset to deterministic when finished:

```powershell
$env:NUTRITION_EXPLANATION_PROVIDER="deterministic"
```

## Trial matrix

| Model | User | Duration | provider_attempted | candidate_parse_status | candidate_valid | validation_status | final_explanation_source | fallback_reason | Invalid fields/wrappers observed | Notes |
|---|---:|---:|---|---|---|---|---|---|---|---|
| `ollama/qwen2.5:3b` | 102 |  |  |  |  |  |  |  |  | Current fast baseline |
| `ollama/qwen2.5:3b` | 103 |  |  |  |  |  |  |  |  | Current fast baseline |
| `ollama/qwen2.5:3b` | 104 |  |  |  |  |  |  |  |  | Current fast baseline |
| `ollama/qwen2.5:3b` | 105 |  |  |  |  |  |  |  |  | Current fast baseline |
| `ollama/llama3.2:3b` | 102 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/llama3.2:3b` | 103 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/llama3.2:3b` | 104 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/llama3.2:3b` | 105 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/gemma3:4b` | 102 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/gemma3:4b` | 103 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/gemma3:4b` | 104 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/gemma3:4b` | 105 |  |  |  |  |  |  |  |  | Trial if available |
| `ollama/qwen2.5:7b` | 102 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen2.5:7b` | 103 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen2.5:7b` | 104 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen2.5:7b` | 105 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen3:8b` | 102 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen3:8b` | 103 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen3:8b` | 104 |  |  |  |  |  |  |  |  | Slower capability trial |
| `ollama/qwen3:8b` | 105 |  |  |  |  |  |  |  |  | Slower capability trial |

## PASS criteria

A model passes runtime QA when the debug endpoint shows:

- `provider_attempted: true`
- `candidate_parse_status: success`
- `candidate_valid: true`
- `validation_status: approved`
- `final_explanation_source: provider_approved`
- `fallback_used: false`
- no invalid fields or markdown/code-fence wrapper observed

A safe fallback is still acceptable for architecture safety, but it does not count as provider schema-adherence success.

## Failure mapping

| Observation | Expected backend behavior |
|---|---|
| Malformed JSON | `candidate_parse_status: failed`, deterministic fallback |
| Markdown/code fence wrapper | `candidate_parse_status: failed`, deterministic fallback |
| Extra top-level keys | `candidate_parse_status: failed`, deterministic fallback |
| Unsafe wording in valid schema JSON | `candidate_parse_status: success`, `validation_status: rejected`, deterministic fallback |
| Provider exception | deterministic fallback with provider exception metadata |

## Notes for future work

Do not relax parsing to rescue messy model output. Improving provider results should come from smaller context, clearer prompt instructions, or trying a more capable local model. If local CPU runtime remains too slow, keep deterministic as default and consider isolated worker/runtime strategy later.
