# Daily Coach Narrative Provider Contract Tightening v1.1 Review

Status: `DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_IMPLEMENTED_PENDING_QA`

## Review summary

Daily Coach Narrative Provider Contract Tightening v1.1 is implemented pending local QA/runtime QA.

The change adds a narrow product-copy quality gate that rejects model-generated meta/process/internal architecture language before any Daily Coach Narrative provider output can be considered approved.

No product integration occurs in this milestone.

## Implementation summary

Updated:

- `services/daily_coach_narrative_validation_service.py`
- `services/daily_coach_narrative_provider_service.py`
- `tests/test_daily_coach_narrative_validation_service.py`
- `tests/test_daily_coach_narrative_provider_service.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

Added:

- `docs/project_memory/milestones/daily_coach_narrative_provider_contract_tightening_v1_1.md`
- `docs/project_memory/reviews/daily_coach_narrative_provider_contract_tightening_v1_1.md`
- `docs/project_memory/runtime_qa/daily_coach_narrative_provider_contract_tightening_v1_1.md`

## Validator behavior

The validator now checks model-generated user-facing text fields for meta/process/internal language:

- `coach_note`
- `key_takeaway`
- `confidence_language`
- `avoided_claims`

It intentionally does not reject canonical parser/contract field names such as `used_approved_facts`; those are internal structured output fields, not user-facing coach copy.

Rejection reason:

`Meta/internal process language is not allowed in coach narrative output`

## Tests added or extended

Focused tests prove:

- qwen2.5-style meta language is rejected
- internal architecture language is rejected
- normal qwen3-style coach copy still passes
- exact recommended focus validation remains strict
- exact approved fact validation remains strict
- invented food/target/number rejection remains strict
- raw/debug/provider metadata rejection remains strict
- changed workflow target references remain rejected

## Prompt cleanup

The offline QA prompt example was updated to avoid demonstrating the rejected pattern.

The old example used process language similar to the observed qwen2.5 issue. The new example uses coach-like output while preserving the same six-key JSON contract.

## Boundary review

Confirmed unchanged:

- no normal Today UI integration
- no Streamlit normal surface integration
- no report integration
- no persistence of model-generated narrative
- no model promotion
- qwen3 remains not approved
- direct_ollama remains opt-in only
- no Daily Next Action decision changes
- no DailyCoachNarrativeContext truth-field changes
- no provider gate changes
- no validator loosening
- no deterministic fallback weakening

## Runtime QA required

Run the required matrix after implementation:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Optional:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

## Pending acceptance

Architecture/QA should accept this milestone only after confirming:

- meta/process/internal language is rejected
- qwen3:8b remains stable or failures are safely contained
- qwen2.5:3b is either improved or safely rejected for copy quality
- no normal product integration occurred
- no model was promoted

## Runtime Fix Review Addendum

Status: `DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_RUNTIME_FIX_IMPLEMENTED_PENDING_QA`

Runtime QA after the first v1.1 implementation produced a partial pass, not a product-quality pass.

Findings addressed:

- qwen3:8b emitted meta/internal wording for users 102 and 105.
- qwen3:8b user 101 cited `Nutritional confidence: Limited`, which is not an exact approved fact string.
- qwen2.5:3b remained baseline-only and changed the Daily Next Action in one case.

Fix summary:

- field-specific meta/internal diagnostics make failures easier to interpret
- product-copy checks now focus on the fields that could become user-facing narrative
- `avoided_claims` remains useful for offline QA but no longer blocks product-copy validation by itself
- provider prompt and context language now avoid teaching the model to say backend/internal phrases
- strict exact fact matching remains unchanged, so paraphrased facts remain rejected

Runtime QA must be rerun before acceptance.
