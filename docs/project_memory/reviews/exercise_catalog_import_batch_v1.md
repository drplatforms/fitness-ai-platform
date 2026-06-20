# Exercise Catalog Import Batch v1 Review

Status: `EXERCISE_CATALOG_IMPORT_BATCH_V1_IMPLEMENTED_PENDING_REVIEW`

## Summary

Exercise Catalog Import Batch v1 adds a tiny manually curated home-gym exercise batch to the canonical exercise catalog.

The batch is intentionally small: 18 canonical rows.

This is not a bulk import, not scraping, not an API integration, and not AI-generated exercise truth.

## Source and review method

Source approach:

```text
Manual curation with existing project taxonomy alignment.
```

Review approach:

1. Review existing canonical exercise coverage.
2. Identify useful missing home-gym entries by movement pattern, equipment, and practical logging/training coverage.
3. Avoid duplicates and near-duplicates already covered by the canonical catalog.
4. Use only neutral taxonomy fields: name, type, movement pattern, primary muscles, equipment, and difficulty.
5. Add no copied descriptions, cues, medical claims, rehab claims, or contraindication language.
6. Commit only canonical catalog changes, tests, and docs.

No raw third-party dataset or staged qa_artifacts output is committed.

## Canonical rows added

| Row | Canonical exercise | Type | Movement pattern | Equipment | Primary muscles | Difficulty | Inclusion reason |
|---:|---|---|---|---|---|---|---|
| 1 | Bodyweight Step-Up | strength | lunge | bodyweight, adjustable_bench | quadriceps, glutes | beginner | Adds simple bench/box unilateral lower-body option without load. |
| 2 | Front-Foot Elevated Split Squat | strength | lunge | bodyweight, plates | quadriceps, glutes | intermediate | Adds reviewed split-squat variation using existing plate/bodyweight tags. |
| 3 | Deficit Reverse Lunge | strength | lunge | bodyweight, plates | quadriceps, glutes | intermediate | Adds unilateral lunge variation without new equipment taxonomy. |
| 4 | Cossack Squat | strength | lunge | bodyweight | quadriceps, glutes, adductors | intermediate | Adds lateral lower-body pattern coverage. |
| 5 | Single-Leg Calf Raise | strength | conditioning | bodyweight | calves | beginner | Adds no-equipment calf option using existing taxonomy. |
| 6 | Single-Leg Hip Thrust | strength | hinge | bodyweight, adjustable_bench | glutes, hamstrings | intermediate | Adds bench-supported hinge/glute option without new behavior. |
| 7 | Reverse Plank | core | core_anti_extension | bodyweight | core, glutes, hamstrings | beginner | Adds bodyweight posterior-chain core option. |
| 8 | V-Up | core | core_anti_extension | bodyweight | core, hip_flexors | intermediate | Adds common bodyweight core option. |
| 9 | Lying Leg Raise | core | core_anti_extension | bodyweight | core, hip_flexors | beginner | Adds accessible bodyweight core option. |
| 10 | Copenhagen Side Plank | core | core_anti_rotation | bodyweight, adjustable_bench | core, obliques, adductors | advanced | Adds advanced side-plank variation with neutral taxonomy only. |
| 11 | Dumbbell Alternating Bench Press | strength | horizontal_push | dumbbell, adjustable_bench | chest, triceps, shoulders | intermediate | Adds dumbbell horizontal-push variation. |
| 12 | Single-Arm Dumbbell Floor Press | strength | horizontal_push | dumbbell | chest, triceps, shoulders | beginner | Adds dumbbell press option without bench requirement. |
| 13 | Dumbbell Cossack Squat | strength | lunge | dumbbell | quadriceps, glutes, adductors | intermediate | Adds loaded lateral lower-body option. |
| 14 | Dumbbell Seated Calf Raise | strength | conditioning | dumbbell, adjustable_bench | calves | beginner | Adds dumbbell calf option aligned with available bench/dumbbells. |
| 15 | Barbell Step-Up | strength | lunge | barbell, rack, plates, adjustable_bench | quadriceps, glutes, core | advanced | Adds loaded step-up option for rack/barbell setup. |
| 16 | Zercher Squat | strength | squat | barbell, plates | quadriceps, glutes, core | advanced | Adds barbell squat-pattern variation without new equipment tags. |
| 17 | Single-Arm Cable Lat Pulldown | strength | vertical_pull | cable | lats, biceps | beginner | Adds cable vertical-pull variation. |
| 18 | Cable Hip Abduction | strength | lunge | cable | glutes, hips | beginner | Adds cable lower-body accessory option using neutral taxonomy. |

## Duplicate findings

Reviewed and skipped close duplicates already present in the catalog, including:

- existing Dumbbell Step-Up
- existing Dumbbell Reverse Lunge
- existing Dumbbell Split Squat
- existing Cable Lat Pulldown / Lat Pulldown
- existing Cable Row and single-arm cable row variants
- existing dumbbell, barbell, band, cable, and pull-up bar accessory coverage

The accepted rows fill gaps that are distinct enough to avoid confusing duplicate search results.

## Safety / language review

Confirmed:

- no exercise descriptions were copied
- no cue prose was copied
- no medical claims were added
- no rehab claims were added
- no injury-treatment or pain-relief claims were added
- no unsafe coaching claims were added
- no contraindication language was added
- only neutral taxonomy fields were added

## Manual QA result

Manual QA expectation:

- new exercises load through the canonical catalog mechanism
- new exercises are available to equipment filtering
- names are unique
- schema fields are present
- no food catalog behavior changed
- no report/provider/runtime behavior changed

Backend tests cover canonical loading, home-gym compatibility, uniqueness, required fields, taxonomy validity, and unsafe-language absence.

## Boundary confirmation

Confirmed:

- exactly 18 canonical exercise rows added
- canonical exercise catalog source changed: `services/exercise_catalog_service.py`
- no food catalog rows changed
- no raw exercise datasets committed
- no staged qa_artifacts committed
- no copied copyrighted descriptions
- no medical/rehab claims added
- no unsafe coaching claims added
- no scraping added
- no API clients added
- no AI-generated exercise metadata used
- no workout generation behavior changes
- no exercise recommendation behavior changes
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

Recommended next milestone after acceptance:

`Daily Coach Narrative Limited Today UI Readiness v1`
