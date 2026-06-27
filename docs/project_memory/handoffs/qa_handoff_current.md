# QA Handoff Current

Milestone closed: Nutrition Serving Unit Logging Streamlit UI v1

Final status: `NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED_AND_MERGED`.

QA status: PASS via completed manual Streamlit workflow smoke.

Current source of truth: `main` at `0ebb1b4`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_0ebb1b4_nutrition-serving-unit-logging-streamlit-ui-v1.zip`.

Separate QA handoff: not required unless Architecture explicitly requests independent QA review.

## QA closeout

QA classification: CLASS 4 — STREAMLIT / USER-FACING WORKFLOW.

Manual Streamlit smoke confirmed:

1. Streamlit starts.
2. Nutrition page loads.
3. Existing nutrition UI still appears.
4. Serving-unit logging section appears.
5. User can search canonical foods.
6. User can select canonical food.
7. Serving units load from backend.
8. Serving-unit selector shows backend-approved options.
9. `serving_unit_id` is not manually typed by user.
10. Quantity accepts valid positive values.
11. Submit logs serving successfully.
12. Success message displays backend-returned resolved grams.
13. No UI-side grams conversion is performed.
14. Existing grams logging path still works.
15. Existing raw/source fallback remains available.
16. Target-vs-Actual / Nutrition Today Summary updates according to existing UI behavior.
17. No traceback appears.
18. No AI/provider path is involved.
19. No raw DB/source/debug internals appear in normal UI.
20. Changing selected canonical food does not submit stale `serving_unit_id`.

## Next recommended QA class

If Architecture authorizes Nutrition Actuals Provenance & Confidence Model v1, suggested QA class:

CLASS 3 — PERSISTENCE / DATA INTEGRITY / ACTUALS SEMANTICS.

Expected QA focus:

- classification correctness for raw grams, canonical grams, serving-unit estimates, ranged serving estimates, missing nutrient values, and low/unknown confidence;
- persistence compatibility with `food_entries` and `nutrition_serving_unit_log_metadata`;
- no Target-vs-Actual redesign unless explicitly authorized;
- no Streamlit changes unless explicitly authorized;
- no AI/provider changes.

## Historical continuity anchors

These phrases are reference-only for project-memory continuity:

- Local Command Menu App Runtime Correction v1
- app` means Linux canonical app runtime
- wapp
- fports
