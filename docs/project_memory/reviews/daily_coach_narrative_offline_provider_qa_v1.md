# Daily Coach Narrative Offline Provider QA v1 Review

Status: `DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_ACCEPTED_WITH_MODEL_FINDINGS`

## Review summary

Daily Coach Narrative Offline Provider QA v1 is accepted with model findings.

The implementation added an offline/debug-only harness for testing provider output against real `DailyCoachNarrativeContext` packets. Runtime QA confirmed the harness can safely evaluate local model output without integrating narrative output into normal Today, Streamlit, reports, or production provider paths.

No model is promoted. No model is production-approved.

## Implemented files

Added:

- `services/daily_coach_narrative_provider_service.py`
- `services/daily_coach_narrative_validation_service.py`
- `tools/daily_coach_narrative_offline_qa.py`
- `tests/test_daily_coach_narrative_provider_service.py`
- `tests/test_daily_coach_narrative_validation_service.py`
- `docs/project_memory/milestones/daily_coach_narrative_offline_provider_qa_v1.md`
- `docs/project_memory/runtime_qa/daily_coach_narrative_offline_provider_qa_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_offline_provider_qa_v1.md`

Updated:

- `models/daily_coach_narrative_models.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Runtime QA findings

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

Observed product-copy issue:

- "Use the exact approved focus because the backend-approved facts support it."

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

## Validator gap

The current validator catches safety and grounding failures, but runtime QA identified a product-copy validator gap.

The validator should reject meta/process language before any Developer Preview surface displays provider narrative.

Examples to reject in a follow-up milestone:

- "approved facts"
- "backend-approved"
- "exact approved focus"
- "use the exact"
- "as instructed"
- "provided context"

## Boundary review

Confirmed preserved:

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

## Final accepted status

`DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_ACCEPTED_WITH_MODEL_FINDINGS`

## Recommended next action

Proceed to merge after documenting runtime findings.

Recommended next milestone after merge:

`Daily Coach Narrative Provider Contract Tightening v1.1`
