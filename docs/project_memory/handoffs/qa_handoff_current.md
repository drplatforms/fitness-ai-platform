# QA Handoff Current

Milestone: Nutrition Actuals Provenance & Confidence Model v1

Branch: `feature/nutrition-actuals-provenance-confidence-model-v1`

Status: backend implementation complete / ready for focused QA.

Requested final status: `NUTRITION_ACTUALS_PROVENANCE_CONFIDENCE_MODEL_V1_ACCEPTED`.

QA class:

CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

## QA focus

Validate classification correctness for persisted nutrition actuals/provenance.

Focused QA should confirm:

1. Raw/source grams entry classifies as `raw_grams`.
2. Canonical grams entry classifies as `canonical_grams`.
3. Serving-unit entry with metadata classifies as `canonical_serving_unit`.
4. Serving-unit interpretation exposes resolved grams from persisted backend value.
5. Serving-unit entry with `grams_min` / `grams_max` is marked `ranged`.
6. Wide gram range adds public-safe limitation/reason code.
7. Low serving-unit confidence adds public-safe limitation/reason code.
8. Missing serving-unit metadata does not crash classification.
9. Missing nutrient values are classified as missing/unknown, not zero.
10. Unknown source classifies safely as `unknown`.
11. Public-safe output excludes raw source payloads and SQL/debug internals.
12. Existing serving-unit logging remains stable.
13. Existing canonical grams logging remains stable.
14. Existing raw/source nutrition logging remains stable.
15. Existing Target-vs-Actual totals remain stable.
16. No Streamlit behavior changed.
17. No AI/provider behavior changed.

## Tests added

New focused test file:

- `tests/test_nutrition_actuals_confidence_service.py`

Sandbox focused result:

- 11 passed for the new confidence service test file.
- 117 passed across adjacent focused nutrition/API/project-memory regression set.

## Not required

This milestone does not require full Streamlit workflow QA.

This milestone does not require AI/provider QA.

This milestone does not require workout/recovery/report QA.

## Historical continuity anchors

These phrases are reference-only for project-memory continuity:

- Local Command Menu App Runtime Correction v1
- app` means Linux canonical app runtime
- wapp
- fports
