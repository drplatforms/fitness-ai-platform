# Catalog Import Pipeline v1

Status: `CATALOG_IMPORT_PIPELINE_V1_IMPLEMENTED_PENDING_REVIEW`

## Purpose

Create deterministic tooling for importing, normalizing, validating, and staging food and exercise catalog candidate data.

The key boundary is staging. This milestone does not promote any imported row into a canonical catalog.

## Approved flow

```text
Raw local CSV/JSON source file
-> deterministic importer
-> normalized staged catalog rows
-> validation report
-> duplicate/suspicion report
-> human review
-> later approved merge into canonical catalog
```

## Implemented tools

Food catalog candidate import:

```powershell
python tools/import_food_catalog.py --input path\to\food.csv --out-dir qa_artifacts\catalog_import_v1\food
```

Exercise catalog candidate import:

```powershell
python tools/import_exercise_catalog.py --input path\to\exercises.csv --out-dir qa_artifacts\catalog_import_v1\exercise
```

Both tools support local `.csv` and `.json` inputs.

## Outputs

Food import writes:

```text
qa_artifacts/catalog_import_v1/food/staged_food_catalog.csv
qa_artifacts/catalog_import_v1/food/food_import_report.md
qa_artifacts/catalog_import_v1/food/food_import_findings.json
```

Exercise import writes:

```text
qa_artifacts/catalog_import_v1/exercise/staged_exercise_catalog.csv
qa_artifacts/catalog_import_v1/exercise/exercise_import_report.md
qa_artifacts/catalog_import_v1/exercise/exercise_import_findings.json
```

Generated artifacts remain local and uncommitted.

## Staged status contract

Each candidate row receives one of:

- `accepted_for_review`
- `review_required`
- `rejected`

No row is described as production-approved.

## Food validation

Food candidate validation checks:

- required fields exist
- name is non-empty
- calories/protein/carbs/fat per 100g are numeric
- calories/protein/carbs/fat are non-negative
- macro grams are plausible for a per-100g row
- calories are plausible relative to macro-derived estimate
- serving-size fields are flagged when present
- duplicate names and aliases are flagged
- missing source/confidence is flagged

## Exercise validation

Exercise candidate validation checks:

- required fields exist
- name is non-empty
- equipment is known or flagged for review
- movement pattern is known or flagged for review
- duplicate names and aliases are flagged
- unsafe, medical, rehab, or over-specific claims are flagged
- missing source/confidence is flagged

## Boundaries

This milestone does not change:

- canonical food catalog rows
- canonical exercise catalog rows
- nutrition calculations
- workout generation
- Streamlit product UI
- FastAPI runtime behavior
- provider behavior
- validators or fallback behavior outside the import tools
- persistence or database behavior

No external network calls are added.
No AI calls are added.
No paid tools are required.
No Aider, Headroom, or Claude workflow is introduced.
