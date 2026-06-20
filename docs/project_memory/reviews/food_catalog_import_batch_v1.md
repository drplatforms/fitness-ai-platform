# Food Catalog Import Batch v1 Review

Status: `FOOD_CATALOG_IMPORT_BATCH_V1_IMPLEMENTED_PENDING_REVIEW`

## Summary

Food Catalog Import Batch v1 adds a tiny reviewed USDA/FDC-sourced generic food batch to the canonical food catalog.

The batch is intentionally small: 20 canonical rows.

This is not a bulk import, not a branded-food dump, not scraping, and not an API integration.

## Source and review method

Source family:

```text
USDA FoodData Central Foundation Foods
```

Source access reference:

```text
https://fdc.nal.usda.gov/download-datasets/
```

Review approach:

1. Use the accepted Catalog Import Pipeline v1 as the staging gate.
2. Use a tiny local USDA/FDC-style source sample under qa_artifacts.
3. Run the deterministic food importer locally.
4. Review staged output, report, and findings locally.
5. Promote only clean, non-duplicate, useful, per-100g rows into canonical seed data.
6. Commit only curated canonical rows, tests, and docs.

Local-only artifacts are not committed.

## Canonical rows added

| Row | Canonical display name | USDA/FDC source note | Calories | Protein | Carbs | Fat |
|---:|---|---|---:|---:|---:|---:|
| 1 | Alaska Pollock, Raw | fdc_id 2768188, Alaska Pollock, raw | 78.5 | 17.3 | 0.1 | 1.0 |
| 2 | Apricot, Raw | fdc_id 2710815, Apricot, with skin, raw | 48.4 | 1.0 | 10.2 | 0.4 |
| 3 | Arugula, Raw | fdc_id 2710822, Arugula, baby, raw | 31.0 | 1.6 | 5.4 | 0.3 |
| 4 | Beets, Raw | fdc_id 2685576, Beets, raw | 44.6 | 1.7 | 8.8 | 0.3 |
| 5 | Beet Greens, Raw | fdc_id 2747653, Beet greens, raw | 26.4 | 1.6 | 4.7 | 0.1 |
| 6 | Bok Choy, Raw | fdc_id 2685572, Cabbage, bok choy, raw | 20.3 | 1.0 | 3.5 | 0.2 |
| 7 | Red Cabbage, Raw | fdc_id 2346408, Cabbage, red, raw | 34.1 | 1.2 | 6.8 | 0.2 |
| 8 | Collard Greens, Raw | fdc_id 2685574, Collards, raw | 46.9 | 3.0 | 7.0 | 0.8 |
| 9 | Fennel Bulb, Raw | fdc_id 2747655, Fennel, bulb, raw | 26.9 | 0.9 | 5.5 | 0.1 |
| 10 | Figs, Dried | fdc_id 326905, Figs, dried, uncooked | 249.0 | 3.3 | 63.9 | 0.9 |
| 11 | Haddock, Raw | fdc_id 333374, Fish, haddock, raw | 74.0 | 16.3 | 0.0 | 0.5 |
| 12 | Catfish, Raw | fdc_id 2684445, Fish, catfish, farm raised, raw | 129.1 | 16.5 | 0.0 | 7.3 |
| 13 | Plantain, Raw | fdc_id 2710817, Plantains, ripe, raw | 136.5 | 1.2 | 31.0 | 0.9 |
| 14 | Mandarin, Raw | fdc_id 2710832, Mandarin, seedless, peeled, raw | 62.0 | 1.0 | 13.4 | 0.5 |
| 15 | Black Rice, Dry | fdc_id 2710825, Rice, black, unenriched, raw | 370.0 | 7.6 | 77.2 | 3.4 |
| 16 | Red Rice, Dry | fdc_id 2710838, Rice, red, unenriched, dry, raw | 369.8 | 8.6 | 76.2 | 3.4 |
| 17 | Fonio Grain, Dry | fdc_id 2710829, Fonio, grain, dry, raw | 369.1 | 7.2 | 81.3 | 1.7 |
| 18 | Khorasan Grain, Dry | fdc_id 2710830, Khorasan, grain, dry, raw | 371.4 | 14.8 | 71.8 | 2.8 |
| 19 | Parsnips, Raw | fdc_id 2747659, Parsnips, raw | 87.1 | 1.3 | 19.3 | 0.5 |
| 20 | Radishes, Raw | fdc_id 2747665, Radishes, red, raw | 19.6 | 0.7 | 4.1 | 0.1 |

## Skipped / rejected candidates

Skipped in v1:

- rows already well-covered in the canonical starter catalog
- rows with incomplete macro fields in the reviewed local source sample
- branded or restaurant-style rows
- mixed prepared dishes
- rows with ambiguous serving basis
- rows that would create confusing duplicate search results

## Manual QA result

Manual QA confirmed the intended workflow:

- tiny local food source sample can be staged through the food importer
- staged CSV/report/findings are local-only under qa_artifacts
- only reviewed rows are manually promoted to canonical seed data
- canonical food search can find newly added rows
- newly added rows preserve per-100g calories/protein/carbohydrate/fat
- no raw USDA/FDC dataset is committed

## Boundary confirmation

Confirmed:

- exactly 20 canonical food rows added
- canonical food catalog source changed: `services/food_normalization_service.py`
- no exercise catalog rows changed
- no raw USDA/FDC datasets committed
- no staged qa_artifacts committed
- no scraping added
- no API clients added
- no AI-generated nutrition data used
- no nutrition calculation changes
- no food logging logic changes
- no Streamlit UI behavior changes
- no FastAPI runtime behavior changes
- no provider behavior changes
- no validator/fallback behavior changes
- no persistence/database changes
- no report changes
- no paid tools required
- no Aider required
- no Codex required
- no Headroom reintroduced
- no Claude workflow
- no CLAUDE.md

## Validation

Expected validation:

```powershell
git diff --check
scripts/dev_commit_check.ps1 -Mode code
python -m py_compile tools/import_food_catalog.py
python -m py_compile tools/catalog_import_common.py
pytest tests/test_food_catalog_import_batch_v1.py -q
pytest tests/test_food_catalog_import.py -q
pytest tests/test_exercise_catalog_import.py -q
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
pytest tests/test_daily_coach_narrative_preview_route.py -q
pytest tests/test_daily_coach_narrative_preview_service.py -q
pytest tests/test_daily_next_action_service.py -q
pytest tests/test_report_persistence_boundary.py -q
pytest tests/test_full_report_section_registry.py -q
```

## Final recommendation

Proposed final status:

`FOOD_CATALOG_IMPORT_BATCH_V1_ACCEPTED`

Recommended next milestone after acceptance:

`Exercise Catalog Import Batch v1`
