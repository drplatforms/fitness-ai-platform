# QA Handoff Current

Milestone: Exercise Eligibility Matrix v1

QA status: implementation checkpoint committed and Linux-validated; final regression/manual smoke pending.

Branch: `feature/exercise-eligibility-matrix-v1`.

Current checkpoint commit: `05d319e`.

## QA focus

Confirm that Exercise Eligibility Matrix v1 preserved existing user-visible workout behavior while adding explicit generator-facing eligibility coverage.

Primary checks:

- Quick remains 3-4 exercises.
- Standard remains 4-5 exercises.
- Full remains 6-7 exercises.
- Immediate preview refresh anti-repeat remains meaningful.
- Selected workout persists exactly.
- Active Workout loads selected workout exactly.
- Today does not duplicate or regenerate selected/active workout.
- No invalid equipment appears for the current home-gym profile.
- No exact duplicate exercise names appear unless unavoidable.
- No provider/AI workout generation path exists.
- Normal UI does not leak provider/debug/runtime internals.

## Diagnostic / matrix checks

The diagnostic and service should make these visible:

- active catalog total;
- equipment compatibility;
- generator eligibility roles;
- slot families;
- reachability status;
- exclusion reasons;
- known specialized/accessory examples;
- known equipment-excluded examples.

## Known limitation for QA notes

The diagnostic reports that many generator-eligible exercises are not selected in a 10-variation deterministic sweep. This is not a v1 blocker if those exercises are classified with reasons and existing workout behavior remains stable.

## Deferred

- rolling multi-refresh novelty;
- persistent exposure tracking;
- complete catalog reachability;
- nutrition/recovery/provider changes;
- optional diagnostic-service refactor that failed to apply and was intentionally stopped.
