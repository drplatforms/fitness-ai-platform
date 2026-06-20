# Food Catalog Import Batch v1

Status: `FOOD_CATALOG_IMPORT_BATCH_V1_IMPLEMENTED_PENDING_REVIEW`

## Purpose

Add the first tiny reviewed USDA/FDC-sourced generic food batch to the canonical food catalog.

This milestone uses the accepted Catalog Import Pipeline v1 workflow as a staging/review gate, but commits only curated canonical rows.

## Scope

In scope:

- tiny reviewed generic food batch
- USDA FoodData Central Foundation Foods source notes
- per-100g calories/protein/carbohydrate/fat rows
- canonical food seed additions
- source-policy/confidence preservation for new batch rows
- tests proving the new rows seed, search, and preserve source metadata
- project-memory documentation

Out of scope:

- branded food dump
- bulk import
- raw USDA/FDC dataset commit
- staged qa_artifacts commit
- scraping
- API client
- AI-generated nutrition facts
- nutrition calculation changes
- food logging behavior changes
- Streamlit/FastAPI runtime changes
- provider changes
- exercise catalog changes

## Implemented batch

Canonical rows added: 20.

Source family: USDA FoodData Central Foundation Foods.

All values are staged as per-100g values and manually reviewed before canonical insertion.

Rows added:

1. Alaska Pollock, Raw
2. Apricot, Raw
3. Arugula, Raw
4. Beets, Raw
5. Beet Greens, Raw
6. Bok Choy, Raw
7. Red Cabbage, Raw
8. Collard Greens, Raw
9. Fennel Bulb, Raw
10. Figs, Dried
11. Haddock, Raw
12. Catfish, Raw
13. Plantain, Raw
14. Mandarin, Raw
15. Black Rice, Dry
16. Red Rice, Dry
17. Fonio Grain, Dry
18. Khorasan Grain, Dry
19. Parsnips, Raw
20. Radishes, Raw

## Source notes

Source page:

```text
https://fdc.nal.usda.gov/download-datasets/
```

Source type:

- USDA FoodData Central Foundation Foods / downloadable CSV-style data.
- Values selected from local reviewed USDA/FDC source rows.
- No raw source dataset is committed by this milestone.

Each new canonical row stores a source note with the USDA/FDC description and fdc_id.

New batch nutrients use:

```text
source_policy = direct_source
confidence = High
```

Existing older starter catalog rows keep existing default source metadata behavior unless separately reviewed later.

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
