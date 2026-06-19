# Daily Coach Narrative Today Developer Panel v1

Status: `DAILY_COACH_NARRATIVE_TODAY_DEVELOPER_PANEL_V1_IMPLEMENTED_PENDING_QA`

## Purpose

Add a Streamlit Developer Mode-only Daily Coach Narrative preview panel that uses the accepted backend debug endpoint:

```text
GET /daily-coach/{user_id}/narrative-preview/debug
```

This milestone exposes the accepted multi-tier narrative lanes in Developer Mode without integrating provider narrative into the normal Today user experience.

## Implemented scope

Implemented in `ui/streamlit_app.py`:

- Developer Mode-only panel: `Developer Preview: Daily Coach Narrative`
- deterministic fallback display fetched through the backend debug endpoint
- manual lane selector
- manual trigger button
- curated public-safe status display
- curated public-safe context summary display
- approved provider narrative display only when backend response includes approved narrative and `fallback_used=false`
- fallback display when provider is disabled, fails, times out, parse-fails, or validation-fails

Implemented test coverage:

- `tests/test_streamlit_daily_coach_narrative_developer_panel.py`

## Accepted lanes represented

The panel includes all accepted lanes from the multi-tier async Today preview design addendum:

1. Deterministic fallback
   - `provider=deterministic`
   - no model parameter
   - no provider generation

2. Fast preview: qwen3:8b
   - `provider=direct_ollama`
   - `model=qwen3:8b`
   - `timeout_seconds=180`

3. Premium preview: qwen3:32b
   - `provider=direct_ollama`
   - `model=qwen3:32b`
   - `timeout_seconds=420`
   - warning shown that generation may take several minutes

4. Baseline/regression: qwen2.5:3b
   - `provider=direct_ollama`
   - `model=qwen2.5:3b`
   - `timeout_seconds=180`

## Safety boundaries

The panel intentionally does not display:

- rejected provider text
- raw model output
- raw prompts
- raw provider payloads
- raw model-facing schema
- raw validation internals
- raw stack traces
- provider exception internals
- hidden/internal architecture language
- production-only debug secrets

The panel shows curated fields only.

## Non-goals preserved

No changes were made to:

- normal Today user card behavior
- report integration
- persistence/cache
- provider defaults
- model approval status
- Daily Next Action decision logic
- DailyCoachNarrativeContext truth fields
- validation services
- provider services
- nutrition/workout/report behavior

## Expected QA status

Expected implementation status after backend/Streamlit validation:

`DAILY_COACH_NARRATIVE_TODAY_DEVELOPER_PANEL_V1_IMPLEMENTED_PENDING_QA`

Expected final status if QA accepts:

`DAILY_COACH_NARRATIVE_TODAY_DEVELOPER_PANEL_V1_ACCEPTED`
