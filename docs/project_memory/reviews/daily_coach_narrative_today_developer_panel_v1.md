# Daily Coach Narrative Today Developer Panel v1 Review Notes

Status: `IMPLEMENTED_PENDING_QA`

## Summary

Daily Coach Narrative Today Developer Panel v1 implements the first Streamlit-side developer-only preview surface for Daily Coach Narrative provider lanes.

The panel is gated behind Developer Mode and uses the existing backend debug endpoint. It does not alter the normal Today user experience.

## Implementation review focus

Architecture/QA should verify:

- panel appears only when Developer Mode is enabled
- normal Today user view remains unchanged
- deterministic fallback appears immediately in the panel
- provider lanes require manual trigger
- the model-lane selector includes all four accepted lanes
- premium qwen3:32b lane includes clear long-runtime warning
- approved provider narrative appears only when backend validation passes
- fallback remains visible when provider output fails or is rejected
- no rejected/raw/provider/debug internals are displayed

## Lane mapping

| Label | Provider | Model | Timeout seconds |
|---|---|---|---:|
| Deterministic fallback | deterministic | none | 0 |
| Fast preview: qwen3:8b | direct_ollama | qwen3:8b | 180 |
| Premium preview: qwen3:32b | direct_ollama | qwen3:32b | 420 |
| Baseline/regression: qwen2.5:3b | direct_ollama | qwen2.5:3b | 180 |

## Validation performed before QA handoff

Expected local validation:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
.\.venv\Scripts\python.exe -m pytest tests\test_streamlit_daily_coach_narrative_developer_panel.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_preview_route.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_preview_service.py -q
.\.venv\Scripts\python.exe -m py_compile ui\streamlit_app.py
```

## Acceptance recommendation

Accept if manual Streamlit QA confirms that the panel is Developer Mode-only, fallback-first, manually triggered, multi-lane, and leakage-safe.

Do not accept if provider generation happens on normal Today page load or raw/rejected provider output is displayed.
