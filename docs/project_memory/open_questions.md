# Open Questions

## Current recommended milestone questions

### Nutrition Actuals Provenance & Confidence Model v1

Status: recommended next milestone / pending Architecture authorization.

Primary question:

How should the backend represent and expose confidence/provenance for nutrition actuals now that serving-unit logging is user-facing?

Questions for Architecture before implementation:

1. What is the v1 confidence vocabulary for nutrition actuals?
   - Candidate categories: exact grams, user-entered grams, canonical grams, serving-unit estimate, ranged serving estimate, low-confidence estimate, unknown.

2. Should confidence be represented as display-facing labels, backend enum values, or both?

3. Should the first v1 output be internal service classification only, or should a public-safe API/summary expose the classification?

4. Should Target-vs-Actual consume this interpretation immediately, or should v1 only prepare the interpretation layer without redesigning Target-vs-Actual?
   - Current recommendation: prepare the interpretation layer first; defer Target-vs-Actual redesign.

5. How should missing nutrient values be classified so downstream summaries do not treat missing as zero?

6. How should serving-unit range fields (`grams_min`, `grams_max`) influence confidence labels?

7. How should provenance distinguish raw/source grams entries from canonical grams entries and serving-unit entries?

8. Which fields are safe for future AI/provider context, and which must remain backend-only?

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

Deferred until after the backend actuals provenance/confidence interpretation layer exists:

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
