# Provider Narrative QA Matrix v2 Results

Status: RUNTIME QA COMPLETE / ACCEPTANCE CANDIDATE

Date: 2026-06-20

Provider lane:
- Provider: direct_ollama
- User: 102
- Workflow target: nutrition_quick_log
- Manual Developer Preview only
- No provider promotion
- No same-session approval
- No normal Today provider call

## Summary Matrix

| Model | Classification | Parse | Validation | Approved narrative | Fallback | Strategy | Runtime seconds | Forbidden leaks |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| qwen2.5:3b | APPROVED_BASELINE | True | True | True | False | raw_json_object | 22.9 | none |
| qwen2.5:7b | APPROVED_PROBE | True | True | True | False | raw_json_object | 60.82 | none |
| qwen3:8b | APPROVED_PROBE | True | True | True | False | raw_json_object | 53.85 | none |
| qwen3:14b | APPROVED_PROBE | True | True | True | False | raw_json_object | 93.27 | none |
| qwen3:32b | SAFE_REJECTED_PARSE | False | False | False | True | None | 240.17 | none |
| qwen3:30b-a3b | SAFE_REJECTED_PARSE | False | False | False | True | no_json_object_found | 49.33 | none |

## Recommendation

Bridge retry baseline:
- qwen2.5:3b

Reason:
- fastest approved model in this matrix
- parse_success true
- validation_success true
- approved_narrative_returned true
- fallback_used false
- no forbidden/debug leaks
- lowest runtime among approved models

Do not use for bridge:
- qwen3:32b
- qwen3:30b-a3b

Reason:
- qwen3:32b timed out and was safely rejected
- qwen3:30b-a3b did not produce a safely extractable JSON object
- both failed safely with no forbidden/debug leaks

Probe-only models:
- qwen2.5:7b
- qwen3:8b
- qwen3:14b

Reason:
- all passed the contract in this run
- all require manual voice review before any use beyond Developer Mode
- none are promoted by this milestone

## Per-model Notes

### qwen2.5:3b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: APPROVED_BASELINE
- Runtime seconds: 22.9
- Parse success: True
- Validation success: True
- Approved narrative returned: True
- Fallback used: False
- Fallback reason: None
- Parse extraction strategy: raw_json_object
- Forbidden/debug leaks: none
- Qualitative voice note: Contract-approved baseline. Manual voice review should confirm whether the copy is useful enough for bridge retry.
- Over-inference risk: Low if diagnostics show no validation warnings and no forbidden leaks.
- Display-readiness recommendation: Bridge baseline candidate only; not a product default or model promotion.

### qwen2.5:7b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: APPROVED_PROBE
- Runtime seconds: 60.82
- Parse success: True
- Validation success: True
- Approved narrative returned: True
- Fallback used: False
- Fallback reason: None
- Parse extraction strategy: raw_json_object
- Forbidden/debug leaks: none
- Qualitative voice note: Contract-approved probe. Manual voice review required before any future use beyond Developer Mode.
- Over-inference risk: Unknown until manually reviewed for over-inference and unsupported certainty.
- Display-readiness recommendation: Probe only; do not use for bridge unless Architecture accepts additional evidence.

### qwen3:8b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: APPROVED_PROBE
- Runtime seconds: 53.85
- Parse success: True
- Validation success: True
- Approved narrative returned: True
- Fallback used: False
- Fallback reason: None
- Parse extraction strategy: raw_json_object
- Forbidden/debug leaks: none
- Qualitative voice note: Contract-approved probe. Manual voice review required before any future use beyond Developer Mode.
- Over-inference risk: Unknown until manually reviewed for over-inference and unsupported certainty.
- Display-readiness recommendation: Probe only; do not use for bridge unless Architecture accepts additional evidence.

### qwen3:14b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: APPROVED_PROBE
- Runtime seconds: 93.27
- Parse success: True
- Validation success: True
- Approved narrative returned: True
- Fallback used: False
- Fallback reason: None
- Parse extraction strategy: raw_json_object
- Forbidden/debug leaks: none
- Qualitative voice note: Contract-approved probe. Manual voice review required before any future use beyond Developer Mode.
- Over-inference risk: Unknown until manually reviewed for over-inference and unsupported certainty.
- Display-readiness recommendation: Probe only; do not use for bridge unless Architecture accepts additional evidence.

### qwen3:32b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: SAFE_REJECTED_PARSE
- Runtime seconds: 240.17
- Parse success: False
- Validation success: False
- Approved narrative returned: False
- Fallback used: True
- Fallback reason: provider_timeout
- Parse extraction strategy: None
- Forbidden/debug leaks: none
- Qualitative voice note: Did not produce safely extractable contract JSON.
- Over-inference risk: Contained output that the parser could not safely accept.
- Display-readiness recommendation: Do not use for bridge; safe rejection is acceptable characterization.

### qwen3:30b-a3b

- Provider: direct_ollama
- User/date: 102 / 2026-06-20
- Next action: log_food / Log a meal or snack
- Workflow target: nutrition_quick_log
- Classification: SAFE_REJECTED_PARSE
- Runtime seconds: 49.33
- Parse success: False
- Validation success: False
- Approved narrative returned: False
- Fallback used: True
- Fallback reason: provider_parse_failed
- Parse extraction strategy: no_json_object_found
- Forbidden/debug leaks: none
- Qualitative voice note: Did not produce safely extractable contract JSON.
- Over-inference risk: Contained output that the parser could not safely accept.
- Display-readiness recommendation: Do not use for bridge; safe rejection is acceptable characterization.
- Sanitized parse error: Output must be a single JSON object with no markdown or prose.

## Boundary Confirmation

- Provider preview remains manual/developer-gated.
- Normal Today UI does not call the provider.
- No same-session approval was added by this matrix.
- No "Approve for this session" button was added.
- No provider narrative is displayed in normal Today UI.
- No model is promoted by this report.
- qwen2.5:3b is a bridge baseline candidate only, not a product default.
- qwen2.5:7b is probe-only.
- qwen3:8b is probe-only.
- qwen3:14b is probe-only.
- qwen3:32b is future premium-voice research only and is not bridge-ready.
- qwen3:30b-a3b is not bridge-ready.
- Raw/rejected provider output is not included in this report.
- No provider persistence was added.
- No database schema changes were added.
- No report persistence changes were added.
- No Daily Next Action, nutrition, workout, catalog, or report behavior changed.
