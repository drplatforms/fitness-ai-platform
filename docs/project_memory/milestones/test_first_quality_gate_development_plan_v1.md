# Test-First Quality Gate Development Plan v1

Status: authorized / docs-only implementation.

Branch: `feature/test-first-quality-gate-development-plan-v1`.

Source baseline: `main` at `b343a47`.

Milestone type: docs / project memory / process canonization only.

## Purpose

Canonize the development process learned from Workout Preview Full-Slot Rotation v1 and Exercise Catalog Utilization / Specialized Movement Coverage v1.

The project is now complex enough that generic green tests are not sufficient when the real user path is not represented by tests, diagnostics, or smoke reproduction.

## Doctrine

> Bite by bite, just bigger bites.

Large objectives may be authorized, but single patches stay narrow. Complexity determines process weight.

## Complex Backend Quality Gate

For complex features involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior:

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

## Bigger milestone / narrow patch rule

Bigger milestone is okay. Bigger single patch is not okay.

Large objectives may be authorized only when internally phased.

Example:

```text
Nutrition Meal Suggestion Engine v1
→ diagnostic / current data shape
→ candidate contract
→ deterministic suggestion engine
→ validation rules
→ focused tests
→ integration
→ smoke
```

## Patch stacking / stop condition rule

Patch stacking is not the goal.

If a complex milestone requires repeated patches, each patch must be tied to a newly understood failure, diagnostic, failing test, lint/pre-commit failure, or smoke regression.

Backend must stop and return to Architecture if any of these occur:

1. The same bug survives two implementation patches.
2. Tests pass but browser smoke fails.
3. Linux smoke fails after Windows green.
4. Candidate pools or data shape are unclear.
5. The implementation requires broader scope than approved.
6. More than the expected file-change budget is needed.
7. Persistence/state behavior becomes unstable.
8. A patch fails to apply because of drift and the next step is not obvious.
9. The branch starts accumulating unrelated fixes.
10. The implementation begins crossing into a deferred v2 milestone.

When stop conditions trigger: do not reset blindly, do not continue blind patching, produce a short diagnostic handoff, and request Architecture decision.

## Bug-to-regression-test rule

Every real smoke failure must become one of:

1. automated regression test,
2. diagnostic/coverage test,
3. documented limitation with explicit reason it cannot be automated yet,
4. backlog item if intentionally deferred.

No major smoke failure should disappear as tribal knowledge.

## File-change budget rule

Each milestone should state expected files or file categories.

Example expected files:

- one primary service,
- one diagnostic tool,
- one focused test file,
- project memory docs.

Unexpected files require pause and Architecture approval when they exceed the authorized scope.

## V1 / V2 scope rule

Architecture must define v1 acceptance and deferred v2 scope before implementation when a feature could expand.

Examples:

- Workout Preview Full-Slot Rotation v1 accepted immediate previous-preview anti-repeat and deferred rolling multi-refresh novelty.
- Exercise Catalog Utilization v1 accepted improved catalog breadth and specialized movement reachability past quality gates and deferred full eligibility matrix, rolling exposure tracking, deeper movement-family de-duplication, and complete catalog reachability.

## Decision log rule

Every accepted milestone should leave a short decision trail:

- accepted status,
- accepted branch,
- feature commit,
- main merge commit,
- feature snapshot,
- source baseline,
- what was accepted,
- what was deferred,
- next recommended milestone.

This must be reflected in current_state/project memory.

## Complex milestone Definition of Done

For complex milestones, Definition of Done includes:

1. Diagnostic evidence.
2. Failing/coverage test for the real behavior where practical.
3. Narrow implementation.
4. Targeted tests green.
5. Prior milestone regressions green.
6. Original failed/user-critical smoke path replayed.
7. Browser smoke green when user-visible.
8. Linux smoke green when runtime-relevant.
9. Project memory updated.
10. Clean working tree.
11. Feature branch committed and pushed.
12. Feature snapshot created only after green smoke.
13. Architecture acceptance before merge.
14. Main merge confirmed.
15. Linux main pull after merge when runtime-relevant.

## Provider / AI-specific rule

No provider output is accepted unless:

- schema-valid,
- validator-approved,
- fact-grounded,
- fallback-safe,
- no invented numbers,
- no invented foods,
- no invented exercises,
- no unsupported health claims,
- no hidden raw provider output in normal UI.

Provider may propose. Backend validates. User sees only approved output.

## Recent examples to preserve

Workout Preview Full-Slot Rotation v1:

- variation `0 -> 1` repeated Dumbbell Single-Leg RDL;
- quality gate reproduced and fixed the path;
- rolling multi-refresh novelty was explicitly deferred.

Exercise Catalog Utilization / Specialized Movement Coverage v1:

- diagnostic proved severe catalog underuse;
- coverage tests failed as expected;
- first implementation improved breadth but regressed preview rotation;
- lint/pre-commit caught cleanup issues;
- Linux smoke found an existing-test regression;
- patch drift blocked a follow-up patch;
- final repair succeeded only after blind closeout stopped.

## Scope boundaries

This milestone is docs-only.

No application behavior, service code, Streamlit UI, database schema, provider runtime, nutrition behavior, workout generation behavior, or exercise catalog logic may change.
