# Daily Coach Narrative Developer Preview v1 Runtime QA

Status: PENDING LOCAL RUNTIME QA

Implementation status: `DAILY_COACH_NARRATIVE_DEVELOPER_PREVIEW_V1_IMPLEMENTED_PENDING_QA`

## Required local checks

### Deterministic fallback path

Provider disabled/default:

```powershell
Invoke-RestMethod "http://localhost:8000/daily-coach/101/narrative-preview/debug"
Invoke-RestMethod "http://localhost:8000/daily-coach/102/narrative-preview/debug"
Invoke-RestMethod "http://localhost:8000/daily-coach/105/narrative-preview/debug"
```

Expected:

- `provider_enabled=false`
- `provider_attempted=false`
- `fallback_used=true`
- `fallback_reason=provider_disabled`
- `approved_narrative=null`
- deterministic fallback note present
- no raw model output
- no raw prompt
- no raw provider payload
- no raw validation errors
- no stack trace

### qwen3:8b provider path

```powershell
Invoke-RestMethod "http://localhost:8000/daily-coach/101/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180"
Invoke-RestMethod "http://localhost:8000/daily-coach/102/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180"
Invoke-RestMethod "http://localhost:8000/daily-coach/105/narrative-preview/debug?provider=direct_ollama&model=qwen3:8b&date=2026-06-19&timeout_seconds=180"
```

Expected:

- `provider_enabled=true`
- `provider_attempted=true`
- approved narrative shown only when parse and validation pass
- deterministic fallback shown if parse/validation/provider failure occurs
- rejected provider text is not exposed

### qwen2.5:3b baseline path

```powershell
Invoke-RestMethod "http://localhost:8000/daily-coach/101/narrative-preview/debug?provider=direct_ollama&model=qwen2.5:3b&date=2026-06-19&timeout_seconds=180"
Invoke-RestMethod "http://localhost:8000/daily-coach/102/narrative-preview/debug?provider=direct_ollama&model=qwen2.5:3b&date=2026-06-19&timeout_seconds=180"
Invoke-RestMethod "http://localhost:8000/daily-coach/105/narrative-preview/debug?provider=direct_ollama&model=qwen2.5:3b&date=2026-06-19&timeout_seconds=180"
```

Expected:

- approved output shown only if product-copy validation passes
- rejected output falls back deterministically
- meta/process/internal language is not exposed

### Optional qwen3:32b offline/debug reference

```powershell
Invoke-RestMethod "http://localhost:8000/daily-coach/101/narrative-preview/debug?provider=direct_ollama&model=qwen3:32b&date=2026-06-19&timeout_seconds=300"
```

Expected:

- approved output if it completes and validates
- timeout/failure safely falls back
- no raw exception exposed

## Focused validation commands

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code

.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_context_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_provider_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_validation_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_preview_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_preview_route.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_next_action_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_coach_voice_bakeoff_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_report_persistence_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
```

## Pass criteria

PASS if:

- developer-only backend debug preview exists
- default path is deterministic fallback only
- direct_ollama provider path is explicit opt-in
- approved narrative is shown only after parse and validation pass
- provider failure falls back deterministically
- rejected provider text is not exposed
- raw prompts/payloads/validation internals/stack traces are not exposed
- normal Today UI remains unchanged
- reports remain unchanged
- no model is promoted
- direct_ollama remains opt-in only
- existing focused tests pass

## Debug endpoint smoke QA

Status: DEBUG_ENDPOINT_SMOKE_CLEAR

Smoke result:
- FastAPI health endpoint reachable from Windows to Linux host.
- Developer preview endpoint reachable through backend debug route.
- Provider-disabled/default path confirmed as developer preview fallback path.
- No rejected provider text, raw prompt, raw provider payload, stack trace, or raw validation internals were intentionally exposed by the preview contract.

Boundary confirmation:
- developer/debug endpoint only
- no normal Today UI integration
- no Streamlit normal surface integration
- no report integration
- no persistence as user-facing history
- no model promotion
- direct_ollama remains opt-in only
- deterministic fallback remains available
