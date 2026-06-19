# Daily Coach Narrative Offline Provider QA v1 Review

Status: `DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_IMPLEMENTED_PENDING_RUNTIME_QA`

## Review summary

Daily Coach Narrative Offline Provider QA v1 is implemented as an offline/debug-only harness for testing provider output against real `DailyCoachNarrativeContext` packets.

The implementation creates a model-facing prompt from approved context fields only and validates provider output against the tightened six-key coach voice JSON contract.

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

## Validation behavior

Provider output is rejected for:

- markdown/prose around JSON
- missing keys
- extra keys
- changed `recommended_focus`
- unapproved facts in `used_approved_facts`
- invented numbers
- invented foods
- invented exercises
- invented calorie/macro targets
- changed Daily Next Action phrases
- changed workflow target references
- medical/clinical claims
- generic filler
- raw/debug/provider/model metadata

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

## Validation completed

Focused tests passed:

- `tests/test_daily_coach_narrative_validation_service.py`
- `tests/test_daily_coach_narrative_provider_service.py`
- `tests/test_daily_coach_narrative_context_service.py`
- `tests/test_daily_next_action_service.py`
- `tests/test_coach_voice_bakeoff_service.py`
- `tests/test_report_persistence_boundary.py`
- `tests/test_full_report_section_registry.py`

Runtime QA remains pending because automated tests do not call live Ollama.

## Recommended next action

Run manual offline provider QA with:

```bash
python tools/daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Then run `qwen3:32b` separately if practical.
