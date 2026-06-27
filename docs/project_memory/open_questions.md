# Open Questions

## Current milestone questions

### Canonical Serving Unit Discovery API v1

Status: authorized backend implementation.

QA found one non-blocking follow-up after Nutrition Serving Unit Logging Backend v1:

Serving-unit IDs are not yet discoverable through a public-safe API response. Manual QA had to look up `serving_unit_id` directly in `canonical_food_serving_units`.

Current implementation questions to resolve in the branch:

1. Should the endpoint live under `/foods/canonical/{canonical_food_id}/serving-units`?
   - Current Architecture recommendation: yes.

2. Should inactive canonical foods return 404 or a safe empty result?
   - Preferred v1 behavior: safe 404 / hidden inactive food.

3. Should inactive serving units be omitted silently?
   - Preferred v1 behavior: yes, return active serving units only.

4. Should response include source/source note?
   - Preferred v1 behavior: include bounded public-safe `source` and `source_notes` only, not raw payloads.

5. Should response include `unit_name` and `unit_quantity`?
   - Preferred v1 behavior: yes, these are backend-approved serving-unit fields useful for UI display/readiness.

6. Should `amount_source` be explicit in the response?
   - Preferred v1 behavior: yes, use `serving_unit_estimate` so Streamlit can display estimate provenance without inventing it.

7. Should this route change logging behavior?
   - No. This milestone is discovery-only.

## Deferred questions

### Nutrition Serving Unit Logging Streamlit UI v1

Deferred until Backend discovery API is accepted:

- How should the UI display active serving units for the selected canonical food?
- Should users see gram ranges immediately, or only confidence/source language?
- Should custom serving overrides remain hidden until a later user-saved-serving milestone?

### Nutrition Actuals Confidence Model v1

Still open for a future milestone:

- How should actuals confidence combine weighed grams, grams-entered, package labels, serving-unit estimates, copied entries, and unknown amounts?
- Which confidence vocabulary should be displayed to users for logged actuals?
- Should Target-vs-Actual show estimated-vs-weighed context in the macro table or a separate note?
- How should estimated actuals affect DailyCoachSynthesis, nutrition explanations, and reports?

### AI/provider context

Deferred:

- When should provider context include serving-unit-derived actuals confidence summaries?
- What approved summary fields should be allowed?
- How do we prevent provider explanations from overstating serving-size certainty?

## Closed by accepted policy/backend milestones

The following are no longer open for v1:

- Whether `food_entries` remains the actuals bridge: yes.
- Whether a companion provenance table is preferred: yes.
- Whether a dedicated serving-unit logging endpoint is preferred: yes.
- Whether grams override is allowed in serving-unit v1: no.
- Whether Streamlit may invent mappings/conversions: no.
- Whether AI/provider may invent serving conversions: no.
- Whether backend serving-unit logging should persist provenance: yes.
- Whether Target-vs-Actual sees serving-unit logs through resolved grams: yes.
- Whether feature snapshots and canonical accepted snapshots differ: yes.
- Whether canonical accepted snapshots should be created from main after Architecture acceptance/merge: yes.
