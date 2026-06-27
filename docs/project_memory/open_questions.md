# Open Questions

## Current milestone questions

### Nutrition Serving Unit Logging Backend v1

Status: implementation authorized.

Architecture has answered the core design questions:

- Keep `food_entries` as the grams-based actuals bridge.
- Add a companion serving-unit provenance table.
- Use a dedicated endpoint: `POST /nutrition/{user_id}/log-serving`.
- Backend owns serving-unit validation and grams resolution.
- Persist resolved grams, gram ranges, confidence, amount source, and original serving display.
- Keep Target-vs-Actual behavior unchanged for this milestone.
- Keep Streamlit and AI/provider out of serving-unit conversion.

Remaining implementation-level questions to verify through tests/QA:

1. Does the backend response include enough public-safe fields for a future Streamlit serving-unit picker?
2. Does provenance metadata preserve the exact resolved grams and gram range used at log time?
3. Does Target-vs-Actual continue to see serving-unit logs through existing grams actuals?
4. Do missing optional gram ranges remain missing instead of becoming zero?
5. Do existing raw/source and canonical grams logging routes remain unchanged?

## Deferred questions

### Nutrition Actuals Confidence Model v1

Still open for a future milestone:

- How should actuals confidence combine weighed grams, grams-entered, package labels, serving-unit estimates, copied entries, and unknown amounts?
- Which confidence vocabulary should be displayed to users for logged actuals?
- Should Target-vs-Actual show estimated-vs-weighed context in the macro table or a separate note?
- How should estimated actuals affect DailyCoachSynthesis, nutrition explanations, and reports?

### Streamlit Serving Unit Logging UI v1

Deferred until Backend v1 is accepted:

- How should the UI display active serving units for the selected canonical food?
- Should users see gram ranges immediately, or only confidence/source language?
- Should custom serving overrides remain hidden until a later user-saved-serving milestone?

### AI/provider context

Deferred:

- When should provider context include serving-unit-derived actuals confidence summaries?
- What approved summary fields should be allowed?
- How do we prevent provider explanations from overstating serving-size certainty?

## Closed by accepted contract design

The following are no longer open for v1:

- Whether `food_entries` remains the actuals bridge: yes.
- Whether a companion provenance table is preferred: yes.
- Whether a dedicated endpoint is preferred: yes.
- Whether grams override is allowed in serving-unit v1: no.
- Whether Streamlit may invent mappings/conversions: no.
- Whether AI/provider may invent serving conversions: no.
