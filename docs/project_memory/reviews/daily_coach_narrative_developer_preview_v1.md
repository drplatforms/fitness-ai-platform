# Daily Coach Narrative Developer Preview v1 Review

Status: IMPLEMENTED / PENDING QA

Review status: `DAILY_COACH_NARRATIVE_DEVELOPER_PREVIEW_V1_IMPLEMENTED_PENDING_QA`

## Summary

Daily Coach Narrative Developer Preview v1 adds a backend developer-only debug endpoint for inspecting the narrative path safely before any normal product integration.

The implementation exposes either:

1. validated provider narrative, or
2. deterministic fallback narrative.

It never returns rejected provider text or raw provider/debug internals.

## Files changed

- `api/routes/daily_coach.py`
- `models/daily_coach_narrative_models.py`
- `services/daily_coach_narrative_preview_service.py`
- `tests/test_daily_coach_narrative_preview_route.py`
- `tests/test_daily_coach_narrative_preview_service.py`
- `docs/project_memory/milestones/daily_coach_narrative_developer_preview_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_developer_preview_v1.md`
- `docs/project_memory/runtime_qa/daily_coach_narrative_developer_preview_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Accepted implementation intent

- Developer-only backend debug endpoint first.
- Streamlit Developer Mode preview intentionally deferred.
- Provider disabled by default.
- direct_ollama provider attempted only through explicit preview query parameter.
- Deterministic fallback returned by default.
- Approved provider output returned only after existing parser and validator pass.
- Rejected provider text is never returned.
- Raw prompts, payloads, validation errors, validation internals, and stack traces are not returned.

## Endpoint

```text
GET /daily-coach/{user_id}/narrative-preview/debug
```

Examples:

```powershell
Invoke-RestMethod "http://localhost:8000/daily-coach/102/narrative-preview/debug"

Invoke-RestMethod "http://localhost:8000/daily-coach/102/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180"
```

## QA expectation

The route should pass deterministic fallback QA before live model QA.

Live model QA should confirm:

- qwen3:8b approved output appears only when validation passes
- qwen2.5:3b approved output appears only when validation passes
- qwen3:32b timeout/failure falls back safely if run
- rejected text is not exposed
- fallback reasons remain public-safe

## Final review position

Implementation is ready for local API/runtime QA.

Recommended status before runtime QA:

`DAILY_COACH_NARRATIVE_DEVELOPER_PREVIEW_V1_IMPLEMENTED_PENDING_QA`
