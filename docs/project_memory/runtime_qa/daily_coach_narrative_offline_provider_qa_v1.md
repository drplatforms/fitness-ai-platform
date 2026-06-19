# Daily Coach Narrative Offline Provider Runtime QA v1

Status: `DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_ACCEPTED_WITH_MODEL_FINDINGS`

## Final runtime QA interpretation

Daily Coach Narrative Offline Provider Runtime QA v1 is accepted.

The offline/debug-only harness successfully tested local model output against real `DailyCoachNarrativeContext` packets.

No production integration occurred. No model is promoted. No model is production-approved.

## Runtime matrix summary

| Model | Users | Parse | Validation | Decision | Grounding | Voice | Latency | Decision |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `qwen3:8b` | 101, 102, 105 | 3/3 | 3/3 | 3/3 | 5 | 4 | ~39-52s | clean practical pass |
| `qwen2.5:3b` | 101, 102, 105 | 3/3 | 3/3 | 3/3 | 5 | 4 by harness score | ~25-40s | safe compliance pass with copy-quality warning |
| `qwen3:32b` | 101, 102, 105 | 2/3 | 2/3 | 2/3 | approved runs strong | approved runs strong | avg ~214s; one ~300s timeout | partial offline reference pass with timeout limitation |

## Model findings

### qwen3:8b

Result: `CLEAN_PRACTICAL_PASS`

- users 101, 102, and 105 passed
- parse success: 3/3
- validation approved: 3/3
- decision pass: 3/3
- grounding: 5
- voice: 4
- latency roughly 39-52 seconds

Architecture interpretation: `qwen3:8b` remains the best practical Daily Coach Narrative evaluation candidate. It is not production-approved.

Accepted safe excerpts included:

- "Prioritize low-risk training to support recovery."
- "Log your meal or snack to improve nutrition tracking accuracy."
- "Log your meal or snack to improve nutrition state tracking."

### qwen2.5:3b

Result: `SAFE_COMPLIANCE_PASS_COPY_QUALITY_WARNING`

- users 101, 102, and 105 passed
- parse success: 3/3
- validation approved: 3/3
- decision pass: 3/3
- grounding: 5
- voice: 4 by harness score
- latency roughly 25-40 seconds

Architecture interpretation: `qwen2.5:3b` is useful as a small compliant baseline, but representative excerpts showed process/meta-language leakage. It is not recommended for developer preview voice without additional validator protection.

Observed copy-quality issue:

- "Use the exact approved focus because the backend-approved facts support it."

This is safe but not acceptable coach copy.

### qwen3:32b

Result: `PARTIAL_OFFLINE_REFERENCE_PASS_TIMEOUT_LIMITATION`

- users 102 and 105 passed
- user 101 failed due to provider `TimeoutError`
- parse pass: 2/3
- validation pass: 2/3
- decision pass: 2/3
- average latency roughly 214 seconds
- timeout observed at roughly 300 seconds

Architecture interpretation: `qwen3:32b` remains a useful offline quality reference, but it is operationally too slow and not reliable enough for practical preview loops. The timeout was safely contained. It is not production-approved.

Accepted safe excerpt included:

- "Log a meal or snack to improve today's nutrition state."

## Validator gap identified

A copy-quality validator gap was identified.

Current validation allowed process/meta-language such as:

- "Use the exact approved focus"
- "backend-approved facts"
- "approved facts support it"

This is not a safety failure, but it is a product-quality issue. It must be tightened before any developer preview surface displays provider narrative.

## Boundaries preserved

Confirmed unchanged:

- no normal Today UI integration
- no Streamlit normal surface integration
- no report integration
- no persistence of model-generated narrative
- no model promotion
- qwen3 remains not approved
- direct_ollama remains opt-in only
- no Daily Next Action decision changes
- no `DailyCoachNarrativeContext` truth-field changes
- no provider gate changes
- no validator loosening
- no deterministic fallback weakening
- no food catalog changes
- no exercise catalog changes
- no workout generation changes
- no nutrition formula changes
- no Training Level 5 behavior changes
- no Nutrition Level 5 behavior changes
- no rejected model output exposed in normal UI
- no raw validation/debug/provider payloads exposed in normal UI

## Accepted status

`DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_ACCEPTED_WITH_MODEL_FINDINGS`

## Recommended next milestone

`Daily Coach Narrative Provider Contract Tightening v1.1`

Goal: add a small product-copy validator tightening pass before Developer Preview.

Required additions:

- reject meta/process language
- reject internal architecture language
- reject phrases like "approved facts", "backend-approved", "exact approved focus", "use the exact", "as instructed", and "provided context"
- keep `qwen3:8b` as practical reference
- keep `qwen2.5:3b` as baseline only
- keep `qwen3:32b` as optional offline reference
- no normal UI integration yet

After v1.1 passes, the next milestone may be `Daily Coach Narrative Developer Preview v1`.
