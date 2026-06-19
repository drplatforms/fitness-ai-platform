# Daily Coach Narrative Offline Provider QA v1

Status: `DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_IMPLEMENTED_PENDING_RUNTIME_QA`

## Purpose

Daily Coach Narrative Offline Provider QA v1 adds an offline/debug-only runtime QA harness for testing whether local model candidates can write bounded Daily Coach Narrative language from the deterministic `DailyCoachNarrativeContext` packet.

This milestone tests model-speaking behavior without integrating model output into the product.

## Scope

Implemented:

- strict candidate output model extensions for Daily Coach Narrative QA
- strict parser for the tightened six-key coach voice JSON object
- Daily Coach Narrative-specific validation service
- direct Ollama offline/debug-only provider call helper
- offline QA runner service
- CLI tool for local runtime QA
- focused parser/validator/provider tests
- local-only artifact output under `artifacts/daily_coach_narrative_offline_qa_v1/`

## Runtime QA command

```bash
python tools/daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Optional offline reference run:

```bash
python tools/daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

## Output artifacts

The tool writes local ignored artifacts:

- `artifacts/daily_coach_narrative_offline_qa_v1/contexts.json`
- `artifacts/daily_coach_narrative_offline_qa_v1/results.json`
- `artifacts/daily_coach_narrative_offline_qa_v1/report.md`

These artifacts are for QA inspection and should not be committed unless Architecture explicitly asks for a curated result doc.

## Boundaries

This milestone does not:

- integrate narrative output into Today
- integrate narrative output into Streamlit
- integrate narrative output into reports
- persist model-generated narrative history
- promote any model
- approve qwen3 for production
- make direct_ollama default
- change Daily Next Action selection logic
- change `DailyCoachNarrativeContext` truth fields
- loosen validators
- remove deterministic fallback
- change food, exercise, workout, nutrition, Training Level 5, or Nutrition Level 5 behavior

## Expected QA status

Expected final review status after manual runtime QA:

`DAILY_COACH_NARRATIVE_OFFLINE_PROVIDER_QA_V1_ACCEPTED_WITH_MODEL_FINDINGS`
