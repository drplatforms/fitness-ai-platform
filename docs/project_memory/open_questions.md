# Open Questions

## Current milestone review questions

### Nutrition Actuals Provenance & Confidence Model v1

Status: backend implementation complete / ready for Architecture and focused QA review.

Primary review question:

Is the v1 backend interpretation contract sufficient as the first safe layer for nutrition actuals provenance/confidence?

Questions for Architecture / QA review:

1. Are the v1 source types sufficient?
   - `raw_grams`
   - `canonical_grams`
   - `canonical_serving_unit`
   - `unknown`

2. Are the v1 precision labels sufficient?
   - `exact`
   - `estimated`
   - `ranged`
   - `low_confidence`
   - `unknown`

3. Should raw/canonical grams remain moderate-confidence user-entered exact values until stronger source metadata exists?

4. Is the wide serving-unit range threshold acceptable for v1, or should Architecture tune it in a follow-up?

5. Should Target-vs-Actual consume these interpretation objects in a future milestone, or should v1 remain service/model-focused only?

6. Which public-safe interpretation fields should eventually be allowed in AI/provider context?

7. Should a future API endpoint expose these interpretations, or should they stay internal service output until there is a concrete UI/product need?

## Closed serving-unit questions

The following are no longer open for the accepted serving-unit user flow:

- Whether `food_entries` remains the actuals bridge: yes.
- Whether a companion provenance table is preferred: yes.
- Whether a dedicated serving-unit logging endpoint is preferred: yes.
- Whether grams override is allowed in serving-unit v1: no.
- Whether Streamlit may invent mappings/conversions: no.
- Whether AI/provider may invent serving conversions: no.
- Whether backend serving-unit logging should persist provenance: yes.
- Whether Target-vs-Actual sees serving-unit logs through resolved grams: yes.
- Whether serving-unit IDs are public-safe discoverable: yes, through `GET /foods/canonical/{canonical_food_id}/serving-units`.
- Whether Streamlit serving-unit logging is accepted: yes.
- Whether the current serving-unit UI needs a separate QA handoff: no, unless Architecture explicitly requests independent QA review.
- Whether feature snapshots and canonical accepted snapshots differ: yes.
- Whether canonical accepted snapshots should be created from main after Architecture acceptance/merge: yes.

## Deferred questions

### Target-vs-Actual confidence display

Deferred until after Nutrition Actuals Provenance & Confidence Model v1 is accepted:

- Should Target-vs-Actual show estimated-vs-weighed context in the macro table or a separate note?
- Should ranged serving estimates appear as bands or labels?
- Should low-confidence actuals be excluded, down-weighted, or merely annotated?

### AI/provider context

Deferred:

- When should provider context include serving-unit-derived actuals confidence summaries?
- What approved summary fields should be allowed?
- How do we prevent provider explanations from overstating serving-size certainty?

### Food suggestions

Deferred:

- How should future food suggestions account for actuals confidence?
- Should low-confidence actuals affect suggestion ranking differently than exact grams?
- Should missing nutrient values block certain suggestions or appear as data-quality notes?
