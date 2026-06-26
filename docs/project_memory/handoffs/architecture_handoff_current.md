# Architecture Handoff Current

Milestone: Exercise Eligibility Matrix v1

Status: implementation checkpoint committed and Linux-validated; final closeout validation/smoke pending.

Source baseline: `main` at `37d210f`.

Branch: `feature/exercise-eligibility-matrix-v1`.

Current checkpoint commit: `05d319e` (`Add exercise eligibility matrix quality gate`).

Current checkpoint snapshot: `fitness_ai_snapshot_2026-06-26_05d319e_add-exercise-eligibility-matrix-quality-gate.zip`.

## Review focus

Architecture should verify that v1 stayed narrow:

- diagnostic-first process was followed;
- quality-gate test failed before implementation;
- explicit generator-facing eligibility matrix service exists;
- known primary, accessory, core, carry/conditioning, and equipment-excluded examples are classified;
- diagnostic output records reachability and exclusion reasons;
- generator behavior was not broadly rewritten;
- no provider/AI workout generation was introduced;
- the failed optional diagnostic-service refactor was correctly stopped/deferred instead of stacked blindly.

## V1 acceptance intent

Exercise Eligibility Matrix v1 should be accepted if it makes eligibility explicit and test-covered while preserving existing workout behavior.

It should not be blocked merely because many exercises remain not selected in the deterministic sweep; that is a documented Catalog Reachability Audit v2 / future workout-roadmap issue.

## Known diagnostic baseline

- active catalog exercises: 240
- equipment-compatible exercises: 237
- generator-eligible exercises: 232
- selected in 10-variation deterministic sweep: 54
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families: arms_biceps, arms_triceps, mobility

## Final acceptance is still blocked until

- full validation suite is green;
- Linux validation remains green;
- browser/manual workout smoke is green;
- final feature snapshot is created;
- final handoff records validation/smoke results.

Proposed final status after successful closeout: `EXERCISE_ELIGIBILITY_MATRIX_V1_ACCEPTED`.
