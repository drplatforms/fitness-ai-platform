# Daily Coach Narrative Provider Contract Tightening v1.1

Status: `DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_IMPLEMENTED_PENDING_QA`

## Purpose

Daily Coach Narrative Offline Provider QA v1 proved that local models can generate bounded narrative copy from real `DailyCoachNarrativeContext` packets, but it also exposed a product-copy validator gap.

`qwen2.5:3b` produced safe but unacceptable meta/process language such as:

- "Use the exact approved focus because the backend-approved facts support it."

This milestone adds a narrow validator tightening pass before any Developer Preview surface displays provider narrative.

## Scope

Implemented:

- centralized meta/process/internal language fragments in the Daily Coach Narrative validation service
- user-facing generated field checks for:
  - `coach_note`
  - `key_takeaway`
  - `confidence_language`
  - `avoided_claims`
- product-copy rejection reason for internal/process copy
- prompt example cleanup so the offline harness no longer demonstrates the rejected language pattern
- focused tests for rejected qwen2.5-style meta copy and accepted qwen3-style coach copy

## Rejected language categories

The validator now rejects user-facing generated copy that exposes prompt, schema, validator, backend, provider, context-packet, workflow-target, deterministic-fallback, exact-match, output-contract, JSON, or approved-fact process language.

Examples rejected:

- "Use the exact approved focus."
- "The backend-approved facts support this."
- "Based on the provided context..."
- "As instructed, log a meal or snack."
- "The validator requires this focus."
- "The JSON output should..."

## Allowed language remains

Normal coach copy remains valid when it stays grounded in the approved context:

- "Focus on logging a meal or snack."
- "Keep training conservative today."
- "Use a lower-risk workout today."
- "Logging one meal helps improve today's nutrition picture."

## Boundaries preserved

This milestone does not:

- integrate into normal Today UI
- integrate into Streamlit normal surfaces
- integrate into reports
- persist model-generated narrative as user-facing history
- promote any model
- approve qwen3
- make direct_ollama default
- change Daily Next Action decision logic
- change DailyCoachNarrativeContext truth fields
- loosen validators
- remove deterministic fallback
- change provider gates
- add RAG, embeddings, scraping, or agents
- add meal planning or AI-generated food/exercise suggestions
- change food catalog, exercise catalog, workout generation, nutrition formulas, Training Level 5 behavior, or Nutrition Level 5 behavior

## Runtime QA expectation

Required runtime QA after implementation:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Optional offline reference:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

## Expected result

Expected implementation status:

`DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_IMPLEMENTED_PENDING_QA`

Expected final status if runtime QA confirms the gate:

`DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_ACCEPTED`

## Runtime Fix Addendum

Status: `DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_RUNTIME_FIX_IMPLEMENTED_PENDING_QA`

The first v1.1 runtime QA showed the validator worked as a safety/product-copy gate, but provider output still produced internal/meta language too often and one qwen3:8b candidate cited a non-exact confidence fact.

Runtime fix changes:

- keep validator strict
- add field-specific meta/internal diagnostics
- validate product-copy meta language only in `coach_note`, `key_takeaway`, and `confidence_language`
- treat `avoided_claims` as an offline audit field, not coach-facing copy
- remove backend/internal wording from generated context confidence language
- rewrite prompt labels away from `APPROVED_CONTEXT`, `APPROVED_FACTS`, backend wording, validator/schema wording, and workflow-target route exposure
- keep exact `used_approved_facts` matching strict
- keep changed-action and changed-workflow-target validation strict

This addendum does not approve any model and does not add product integration.
