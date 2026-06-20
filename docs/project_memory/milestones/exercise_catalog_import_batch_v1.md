# Exercise Catalog Import Batch v1

Status: `EXERCISE_CATALOG_IMPORT_BATCH_V1_IMPLEMENTED_PENDING_REVIEW`

## Purpose

Add a tiny manually curated exercise batch to the canonical exercise catalog after the accepted catalog import/source/food-batch milestones.

This milestone improves practical home-gym exercise coverage while preserving existing workout generation behavior.

## Scope

In scope:

- tiny manually curated exercise batch
- equipment-aligned home-gym entries
- existing exercise schema and taxonomy only
- no copied third-party descriptions
- no medical, rehab, contraindication, or unsafe coaching claims
- tests proving the new rows load, remain unique, use valid tags, and are home-gym compatible
- project-memory documentation

Out of scope:

- food catalog changes
- raw third-party exercise datasets
- staged qa_artifacts commit
- scraping
- API client
- AI-generated exercise facts
- exercise descriptions or cue prose copied from third parties
- workout generation behavior changes
- exercise recommendation behavior changes
- Streamlit/FastAPI runtime changes
- provider changes
- validator/fallback changes
- persistence or report changes

## Implemented batch

Canonical exercise rows added: 18.

Source/curation approach:

- manual curation
- existing project taxonomy alignment
- home-equipment fit review
- no copied descriptions
- no medical/rehab claims

Rows added:

1. Bodyweight Step-Up
2. Front-Foot Elevated Split Squat
3. Deficit Reverse Lunge
4. Cossack Squat
5. Single-Leg Calf Raise
6. Single-Leg Hip Thrust
7. Reverse Plank
8. V-Up
9. Lying Leg Raise
10. Copenhagen Side Plank
11. Dumbbell Alternating Bench Press
12. Single-Arm Dumbbell Floor Press
13. Dumbbell Cossack Squat
14. Dumbbell Seated Calf Raise
15. Barbell Step-Up
16. Zercher Squat
17. Single-Arm Cable Lat Pulldown
18. Cable Hip Abduction

## Coverage added

Movement-pattern coverage:

- lunge / unilateral lower body
- squat
- hinge
- horizontal push
- vertical pull
- core anti-extension
- core anti-rotation
- conditioning-tagged calf work using existing taxonomy

Equipment coverage:

- bodyweight
- adjustable bench
- plates
- dumbbells
- barbell
- rack
- cable

## Skipped / deferred candidates

Skipped or deferred in v1:

- exercises already covered by existing catalog names or close variants
- unclear-equipment rows requiring unsupported taxonomy
- landmine-specific rows because `landmine` is not an existing supported equipment tag
- medical/rehab/contraindication-oriented rows
- copied third-party exercise descriptions
- giant exercise dumps
- unclear-license datasets

## Validation

Expected validation:

```powershell
git diff --check
scripts/dev_commit_check.ps1 -Mode code
python -m py_compile tools/import_exercise_catalog.py
python -m py_compile tools/catalog_import_common.py
pytest tests/test_exercise_catalog_import_batch_v1.py -q
pytest tests/test_exercise_catalog_import.py -q
pytest tests/test_food_catalog_import.py -q
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

`EXERCISE_CATALOG_IMPORT_BATCH_V1_ACCEPTED`
