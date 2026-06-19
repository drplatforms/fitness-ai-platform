# Daily Coach Narrative Developer Preview v1

Status: IMPLEMENTED / PENDING QA

Implementation status: `DAILY_COACH_NARRATIVE_DEVELOPER_PREVIEW_V1_IMPLEMENTED_PENDING_QA`

## Goal

Expose approved Daily Coach Narrative output through a developer-only backend debug endpoint without integrating narrative output into normal Today UI, Streamlit normal surfaces, reports, persistence, or any production provider path.

## Implemented

- Added `DailyCoachNarrativePreviewResult` as the public-safe preview response model.
- Added `services/daily_coach_narrative_preview_service.py`.
- Added backend debug route: `GET /daily-coach/{user_id}/narrative-preview/debug`.
- Added focused route and preview service tests.

## Endpoint behavior

Route:

```text
GET /daily-coach/{user_id}/narrative-preview/debug
```

Supported query parameters:

- `provider=deterministic|direct_ollama`
- `model=qwen3:8b` or another explicitly requested preview/debug model
- `date=YYYY-MM-DD`
- `timeout_seconds=<seconds>`

Default behavior:

- `provider=deterministic`
- no model call
- deterministic fallback note returned
- `provider_attempted=false`
- `fallback_used=true`
- `fallback_reason=provider_disabled`

Provider behavior:

- provider is attempted only with `provider=direct_ollama`
- default preview model is `qwen3:8b`
- provider output is parsed and validated with existing Daily Coach Narrative validation rules
- approved provider output is returned only after validation succeeds
- rejected/unparsable/exception provider output falls back deterministically

## Public-safe fallback reasons

The preview payload exposes only public-safe fallback reasons:

- `provider_disabled`
- `provider_timeout`
- `provider_parse_failed`
- `provider_validation_failed`
- `provider_unavailable`

## Safety boundaries

The preview does not expose:

- rejected provider text
- raw model output
- raw prompts
- raw provider payloads
- raw validation errors
- validation internals
- stack traces
- model-facing schema text
- source metadata

## Non-goals preserved

- no normal Today UI integration
- no Streamlit normal surface integration
- no report integration
- no persistence of model-generated narrative
- no model promotion
- no qwen3 production approval
- no direct_ollama default change
- no Daily Next Action decision changes
- no DailyCoachNarrativeContext truth-field changes
- no validator loosening
- no deterministic fallback weakening
- no provider gate loosening
- no RAG, embeddings, scraping, agents, meal planning, food suggestions, or exercise suggestions

## Validation

Sandbox validation performed:

```text
python -m pytest tests/test_daily_coach_narrative_preview_service.py tests/test_daily_coach_narrative_preview_route.py -q
8 passed

python -m pytest tests/test_daily_coach_narrative_context_service.py tests/test_daily_coach_narrative_provider_service.py tests/test_daily_coach_narrative_validation_service.py tests/test_daily_next_action_service.py tests/test_coach_voice_bakeoff_service.py tests/test_report_persistence_boundary.py tests/test_full_report_section_registry.py tests/test_daily_coach_narrative_preview_service.py tests/test_daily_coach_narrative_preview_route.py -q
79 passed

python -m compileall api models services tests tools
passed

git diff --check
passed
```

Runtime QA remains required locally for live Ollama provider paths.
