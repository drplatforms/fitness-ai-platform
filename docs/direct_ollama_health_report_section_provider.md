# Direct Ollama Health Report Section Provider v1

## Status

`Direct Ollama Health Report Section Provider v1` promotes the accepted health report section spike into a narrow production-capable provider path for the nutrition report section only.

This does **not** replace the full health report pipeline. Existing report generation, report persistence, Streamlit behavior, and CrewAI report flow remain unchanged by default.

## Architecture pattern

```text
approved backend report context
→ direct Ollama section candidate
→ strict JSON schema
→ exact parser
→ section validator
→ approved section or deterministic fallback
```

The backend remains the source of truth. Direct Ollama may generate only bounded user-facing wording from approved section context.

## Scope

Implemented scope:

- Nutrition health report section only.
- Deterministic provider remains default.
- `direct_ollama` provider is opt-in via environment variable.
- Strict `CandidateHealthReportSection` contract is reused from the spike.
- Provider output is parsed and validated before approval.
- Invalid output falls back deterministically.
- Runtime metadata is available only through a debug endpoint.
- Full health report output remains public-safe and unchanged by default.

Non-goals preserved:

- No full report replacement.
- No all-section implementation.
- No async job system.
- No report UI redesign.
- No report persistence change.
- No parser relaxation.
- No messy JSON extraction.
- No markdown/code-fence acceptance.
- No medical advice expansion.
- No nutrition target changes.
- No workout changes.
- No Streamlit provider controls.
- No CrewAI removal.

## Candidate schema

Provider output must be one raw JSON object with exactly these keys:

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

The parser rejects:

- markdown wrappers
- code fences
- wrapper objects
- extra keys
- missing required keys
- malformed JSON
- non-object output

## Validation rules

The section validator checks:

- required fields are non-empty
- `key_observations` has 1–5 strings
- confidence is one of `Limited`, `Low`, `Moderate`, `High`
- reason codes are non-empty strings
- no markdown code fences in fields
- no internal implementation terms such as `validator`, `fallback`, `debug`, `provider`, `Ollama`, or `CrewAI`
- no medical, disease, diagnosis, treatment, or cure claims
- no target mutation or calibration-change claims
- no unapproved numeric values
- vague copy is rejected when specific approved nutrition context exists

## Provider configuration

Default behavior:

```bash
HEALTH_REPORT_SECTION_PROVIDER=deterministic
```

Direct Ollama opt-in:

```bash
HEALTH_REPORT_SECTION_PROVIDER=direct_ollama
HEALTH_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
HEALTH_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_BASE_URL=http://192.168.1.104:11434
```

Recommended first model:

```text
ollama/qwen2.5:3b
```

The spike showed this model passed in 11.843 seconds and was fastest by a wide margin.

## Debug endpoint

Debug/developer inspection endpoint:

```text
GET /reports/sections/nutrition/{user_id}/debug?date=YYYY-MM-DD
```

Response includes:

- `success`
- `user_id`
- `section`
- `report_date`
- `approved_section`
- `runtime_metadata`

Runtime metadata includes:

- configured_provider
- selected_provider
- configured_model
- selected_model
- provider_attempted
- fallback_used
- fallback_reason
- candidate_valid
- validation_errors
- candidate_parse_status
- candidate_validation_status
- validation_status
- final_section_source
- raw_output_length
- raw_output_preview_truncated
- markdown_wrapper_detected
- extra_keys_detected
- wrapper_object_detected
- elapsed_seconds

This endpoint is for QA/developer inspection. Normal full report endpoints remain unchanged and do not expose provider metadata.

## Public safety boundary

Existing public report output must not expose:

- raw provider output
- runtime metadata
- configured_model
- selected_model
- validation internals
- raw context payloads

## Testing policy

Automated tests mock provider calls and do not call live Ollama or CrewAI.

Tests cover:

- deterministic provider remains default
- direct Ollama valid provider output approves
- malformed JSON falls back
- markdown-wrapped output falls back
- wrapper object output falls back
- extra-key output falls back
- missing field output falls back
- validation failure falls back
- invalid provider falls back deterministically
- debug endpoint exposes runtime metadata
- existing latest report endpoint does not expose section metadata

## Runtime QA recommendation

Run the debug endpoint with direct Ollama enabled:

```bash
HEALTH_REPORT_SECTION_PROVIDER=direct_ollama
HEALTH_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
HEALTH_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_BASE_URL=http://192.168.1.104:11434
```

Primary QA target:

```text
user_id=102
date=2026-06-06
section=nutrition
```

Confirm:

- provider reaches approved section or safely falls back
- runtime metadata records configured/selected provider/model
- section output is specific and grounded in backend-approved context
- no invented nutrition values
- no medical claims
- fallback remains deterministic and safe
- existing full report behavior remains stable
