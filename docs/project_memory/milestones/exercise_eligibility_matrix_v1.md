# Exercise Eligibility Matrix v1

Status: implementation checkpoint committed and Linux-validated; final closeout validation/smoke pending.

Branch: `feature/exercise-eligibility-matrix-v1`.

Source baseline: `main` at `37d210f`.

Current checkpoint commit: `05d319e` (`Add exercise eligibility matrix quality gate`).

Current checkpoint snapshot: `fitness_ai_snapshot_2026-06-26_05d319e_add-exercise-eligibility-matrix-quality-gate.zip`.

## Purpose

Exercise Eligibility Matrix v1 makes the relationship between catalog exercises and deterministic workout generation explicit.

The goal is not to force every exercise into workouts immediately.

The goal is that every active, equipment-compatible catalog exercise can be classified as generator-eligible or excluded with a clear reason.

## Process followed

This milestone followed the Test-First Quality Gate Development Plan v1:

1. Diagnostic-first patch added `tools/exercise_eligibility_matrix_diagnostic.py`.
2. Diagnostic showed current reachability and exclusion gaps.
3. Quality-gate tests were added before the service existed.
4. The test failed as expected with `ModuleNotFoundError` for `services.exercise_eligibility_matrix_service`.
5. Narrow implementation added `services/exercise_eligibility_matrix_service.py`.
6. Focused quality gate passed.
7. Linux checkpoint validation passed.
8. Optional diagnostic-service refactor failed to apply and was stopped/deferred.

## Diagnostic baseline

- total active catalog exercises: 240
- total equipment-compatible exercises: 237
- total exercises with usable metadata: 240
- total specialized/accessory movements: 135
- total generator-eligible exercises: 232
- total selected in deterministic 10-variation sweep: 54
- total not reachable in deterministic sweep: 186
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families: arms_biceps, arms_triceps, mobility

## Files added

- `services/exercise_eligibility_matrix_service.py`
- `tools/exercise_eligibility_matrix_diagnostic.py`
- `tests/test_exercise_eligibility_matrix_v1.py`

## V1 acceptance target

V1 acceptance should focus on explicit eligibility classification, not complete reachability.

Expected v1 capabilities:

- primary strength movements classify to generator-facing slot families;
- specialized/accessory movements classify clearly;
- core movements classify clearly;
- carry and conditioning movements classify clearly;
- unavailable equipment is excluded;
- metadata/exclusion reasons are visible;
- existing workout generation sizing/persistence/refresh behavior remains stable;
- no provider/AI workout generation is introduced.

## Deferred

- Catalog Reachability Audit v2;
- complete catalog reachability;
- rolling multi-refresh novelty;
- persistent exercise exposure tracking;
- deeper movement-family de-duplication;
- arms/mobility slot expansion decisions;
- optional diagnostic-service refactor.

## Next recommended product direction after acceptance

This should be the final workout-foundation pass before nutrition unless Architecture decides otherwise.

Recommended next:

1. Nutrition Deterministic Food Suggestions v1.
2. Nutrition AI Meal/Snack Candidate Contract v1.
3. Recovery engine improvements later.
4. Return to workouts later for reachability/rotation/periodization.
