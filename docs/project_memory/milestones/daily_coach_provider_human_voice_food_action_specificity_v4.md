# Daily Coach Provider Human Voice & Food Action Specificity v4

Status: backend implementation in progress / patch candidate.

Baseline branch: `feature/daily-coach-provider-voice-context-freedom-rich-synthesis-v3`.
Baseline commit: `e23a435 Add daily coach provider voice context freedom rich synthesis v3`.
Recommended branch: `feature/daily-coach-provider-human-voice-food-action-specificity-v4`.

Requested Backend status:
`DAILY_COACH_PROVIDER_HUMAN_VOICE_FOOD_ACTION_SPECIFICITY_V4_IMPLEMENTATION_COMPLETE`

## Goal

Improve Daily Coach provider product copy after v3 technical pass / product voice failure.

v4 keeps the accepted provider doctrine:

- Backend computes facts.
- Backend validates facts.
- Backend approves facts.
- AI synthesizes approved facts.
- Backend parses, validates, approves, or falls back.

The provider does not get more factual authority. It gets better human-safe materials.

## Implemented backend scope

- Added provider-facing friendly food label context.
- Added claim-backed `friendly_name` values for approved food suggestions.
- Added conservative serving display handling.
- Added backend-derived `nutrition_action_context`.
- Updated `claim_backing_map` to separate `internal_meaning` from `user_facing_phrase_examples`.
- Cleaned `today_story` phrasing to avoid deterministic/framework language.
- Cleaned `approved_context_brief` phrasing and added meaning/user-safe context fields.
- Updated prompt examples/anti-examples for human coach voice and food action specificity.
- Strengthened validation for repeatedly rejected phrases, canonical food label leakage, friendly food quote backing, and invented serving language.
- Extended provider trial matrix diagnostics with v4 food/voice fields.

## Safety boundaries preserved

- Deterministic remains default.
- OpenAI remains opt-in/evaluation-only.
- direct_ollama remains opt-in where already supported.
- No provider default change.
- No parser relaxation.
- No quote/value validation relaxation.
- No deterministic fallback bypass.
- No provider output persistence.
- No Streamlit provider controls.
- No normal Today page provider calls.
- No meal planning changes.
- No workout generation changes.
- No nutrition target changes.
- No recovery score changes.
- No raw diagnostics committed.

## QA focus

Primary QA case:

- `user_id=102`
- date: `2026-06-05` or latest QA-selected v4 date
- provider: `openai`
- model: `gpt-5.5`

v4 should improve:

- human voice
- food action specificity
- recovery phrasing
- training phrasing
- priority action clarity

v4 should avoid:

- make nutrition support the work
- useful move
- rebuilding the whole plan
- support the work
- support the day
- nutrition support
- fatigue does not require backing off
- if it fits your meals
- raw canonical food labels such as `Tuna, Canned in Water` when a friendly label exists

## Validation target

Minimum validation:

- `pytest tests/test_daily_coach_value_narrative_service.py -q`
- `pytest tests/test_daily_coach_narrative_validation_service.py -q`
- `pytest tests/test_daily_coach_provider_trial_matrix.py -q`
- `pytest tests/test_daily_coach_value_narrative_api.py -q`
- `pytest tests/test_daily_coach_synthesis_service.py -q`
- `pytest tests/test_api_smoke.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/project_memory_check.py`
- targeted `py_compile`
- targeted Ruff/Black locally

## Patch lesson retained

Do not use broad variable-removal scripts for reused context variables such as `nutrition` or `recovery`. Scope fixes by function/block anchors.
