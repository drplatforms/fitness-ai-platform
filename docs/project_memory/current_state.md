# Current State

Latest accepted milestone: Test-First Quality Gate Development Plan v1.

Latest accepted feature commit: `227990e`.

Latest main merge commit: `37d210f`.

Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_227990e_clarify-continuity-brief-metadata.zip`.

Current implementation milestone: Exercise Eligibility Matrix v1.

Current branch: `feature/exercise-eligibility-matrix-v1`.

Source baseline: `main` at `37d210f`.

Current feature checkpoint: `05d319e` (`Add exercise eligibility matrix quality gate`).

Current checkpoint snapshot: `fitness_ai_snapshot_2026-06-26_05d319e_add-exercise-eligibility-matrix-quality-gate.zip`.

## Current process doctrine

The current operating doctrine is:

> Bite by bite, just bigger bites.

Meaning:

- Larger objectives are allowed.
- Single patches stay narrow.
- Complexity determines process weight.
- Complex backend behavior requires diagnostic-first and test-first gates where practical.
- Real smoke failures become automated regression tests, diagnostic/coverage tests, documented limitations, or backlog items.
- Architecture defines v1/v2 scope before branches spiral.
- Backend must not blindly stack patches after repeated failures.
- QA validates the real user path, not only generic test-green status.

## Recent accepted milestones

### Workout Preview Full-Slot Rotation v1

Accepted and merged.

- Feature commit: `3b32f97`
- Main merge commit: `f39b403`
- Snapshot: `fitness_ai_snapshot_2026-06-25_3b32f97_fix-first-refresh-workout-slot-rotation.zip`
- Accepted scope: immediate previous-preview anti-repeat.
- Deferred v2 scope: rolling multi-refresh novelty.

This milestone proved that generic tests were not enough. The real path was `variation 0 -> variation 1`, where refreshed previews repeated exercises despite valid alternatives. A focused quality gate reproduced the behavior before the narrow fix landed.

### Exercise Catalog Utilization / Specialized Movement Coverage v1

Accepted and merged.

- Feature commit: `1d44b3d`
- Main merge commit: `b343a47`
- Snapshot: `fitness_ai_snapshot_2026-06-26_1d44b3d_preserve-primary-workout-rotation-after-catalog-expansion.zip`
- Accepted scope: improved deterministic catalog breadth and specialized movement reachability past quality gates.
- Preserved: Quick / Standard / Full sizing, immediate preview refresh anti-repeat, selected workout persistence, Active Workout persistence, Today workout de-dup, and no provider/AI workout generation path.
- Deferred future scope: Exercise Eligibility Matrix v1, Catalog Reachability Audit v2, rolling exposure tracking, deeper movement-family de-duplication, and complete catalog reachability.

This milestone proved the value of stop conditions. The first breadth implementation improved utilization but regressed preview rotation. Linux smoke later caught a home-gym hinge/vertical_pull regression. Patch drift also occurred. The final accepted branch succeeded only after each failure was treated as a diagnostic signal instead of continuing blind patch stacking.

### Test-First Quality Gate Development Plan v1

Accepted and merged.

- Feature commit: `227990e`
- Main merge commit: `37d210f`
- Snapshot: `fitness_ai_snapshot_2026-06-26_227990e_clarify-continuity-brief-metadata.zip`
- Accepted scope: canonized diagnostic-first / test-first quality gate process.
- Preserved: no app/runtime behavior changes, no service changes, no provider changes, no workout/nutrition/catalog behavior changes.

This milestone made the current quality doctrine repo-discoverable instead of chat-only.

## Current implementation milestone

Exercise Eligibility Matrix v1 is in progress on `feature/exercise-eligibility-matrix-v1`.

Current accepted implementation checkpoint:

- Feature checkpoint commit: `05d319e`
- Checkpoint snapshot: `fitness_ai_snapshot_2026-06-26_05d319e_add-exercise-eligibility-matrix-quality-gate.zip`
- Diagnostic-first process: completed.
- Failing/coverage quality gate: completed; the new test first failed because `services.exercise_eligibility_matrix_service` did not exist.
- Narrow implementation: completed; `services/exercise_eligibility_matrix_service.py` now provides explicit generator-facing eligibility profiles.
- Diagnostic tool: added as `tools/exercise_eligibility_matrix_diagnostic.py`.
- Focused test file: added as `tests/test_exercise_eligibility_matrix_v1.py`.
- Linux checkpoint validation: green.
- Optional diagnostic-service refactor: attempted, patch did not apply, and was deliberately stopped/deferred rather than stacked blindly.

Diagnostic baseline from current branch:

- total active catalog exercises: 240
- equipment-compatible exercises: 237
- generator-eligible exercises classified by matrix/diagnostic: 232
- exercises selected in 10-variation deterministic sweep: 54
- largest exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families called out by diagnostic: arms_biceps, arms_triceps, mobility

V1 acceptance intent:

- The matrix does not force all catalog exercises into workouts.
- The matrix makes generator-facing eligibility explicit.
- Active/equipment-compatible exercises can be classified as eligible or excluded with reason.
- Known primary, specialized/accessory, core, carry, conditioning, and equipment-excluded examples are covered.
- Existing workout generation behavior remains stable.

## Complex Backend Quality Gate

For any complex feature involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior:

1. Diagnose current behavior before patching.
2. Identify the exact failing, missing, or underperforming user path.
3. Add a failing regression test, diagnostic test, or coverage test that captures the real path where practical.
4. Confirm the test fails or exposes the gap before implementation.
5. Apply the smallest safe implementation change.
6. Prove the new test passes.
7. Re-run prior milestone regression tests.
8. Re-run the original manual/browser smoke path.
9. Update project memory.
10. Only then request Architecture acceptance.

Do not treat generic green tests as sufficient if the product-critical path is not covered.

## Risk-based process model

### Low-risk change

Examples: docs update, typo/copy fix, isolated helper, small test cleanup, non-behavioral refactor.

Process: normal patch, focused validation, commit, done.

### Medium-risk change

Examples: deterministic service behavior, simple new backend contract, small UI/backend integration, report section behavior, bounded data model expansion.

Process: light diagnostic, focused test, narrow patch, regression validation, smoke if user-visible.

### High-risk change

Examples: workout generation, exercise catalog selection/scoring, persistence/state behavior, nutrition targets/suggestions, AI/provider output, recommendation logic, cross-domain coaching synthesis.

Process: diagnostic first, failing/coverage test, narrow patch, regression validation, original smoke reproduction, Linux/browser smoke, project memory update, Architecture acceptance.

## Current boundaries

- Deterministic backend owns truth.
- Provider may propose only inside approved contracts.
- Backend validates and approves.
- User sees only approved output.
- Deterministic fallback remains mandatory.
- No provider may run on normal Today page load unless Architecture explicitly promotes it.
- No provider/AI workout generation is accepted.
- No CrewAI/Ollama/OpenAI/PydanticAI/LangGraph workout generation is accepted.
- No worker/queue/scheduler/polling is accepted unless explicitly scoped.
- No broad rewrite is authorized by process docs.
- Codex is not used by default.
- Exercise Eligibility Matrix v1 does not authorize rolling exposure, persistent exercise exposure tracking, nutrition, recovery, provider work, or Streamlit UI rewrites.

## Current next-roadmap candidates

After Exercise Eligibility Matrix v1 is accepted, likely roadmap candidates are:

- Nutrition Deterministic Food Suggestions v1.
- Nutrition AI Meal/Snack Candidate Contract v1.
- Catalog Reachability Audit v2.
- Workout Preview Rolling Exposure Rotation v2.
- Recovery engine improvements later.

## Historical continuity reminders

Historical project-memory entries remain valid context and should not be erased just because the current active milestone changed:

- Project Memory Alignment + North Star Architecture v1.
- `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is reference-only, not accepted.
- Provider Narrative QA Matrix v2.
- Daily Coach Same-Session Approved Preview Bridge v1 Retry.
- Same-Session Bridge Runtime QA v1.
- Daily Coach Narrative Product Voice Polish v1.
- Daily Coach Narrative Product Voice Runtime QA v1.
- PASS_WITH_NOTE product-voice outcomes remain context for future voice work.
- The product goal remains to sound right and be right.
- Local Developer Command Menu Audit + Repo-Owned Commands v1.
- `scripts/fitness_commands.ps1` remains the repo-owned command source.
- Local Command Menu App Runtime Correction v1 clarified that Linux is the canonical app runtime and `wapp` is Windows-local only.
- Daily Coach Async Service Shell / No Worker v1 remains service shell only; no provider execution added.
