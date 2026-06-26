# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Current source baseline: `main` at `b343a47` after Exercise Catalog Utilization / Specialized Movement Coverage v1 was accepted and merged.

Current authorized milestone: Test-First Quality Gate Development Plan v1.

Milestone type: docs / project memory / process canonization only.

No application behavior, service code, Streamlit UI, database schema, provider runtime, nutrition behavior, workout generation behavior, or exercise catalog logic may change in this milestone.

## Current accepted chain

### Workout Preview Full-Slot Rotation v1

Accepted and merged.

- Feature commit: `3b32f97`
- Main merge commit: `f39b403`
- Snapshot: `fitness_ai_snapshot_2026-06-25_3b32f97_fix-first-refresh-workout-slot-rotation.zip`
- Accepted scope: immediate previous-preview anti-repeat.
- Deferred: rolling multi-refresh novelty.

### Exercise Catalog Utilization / Specialized Movement Coverage v1

Accepted and merged.

- Feature commit: `1d44b3d`
- Main merge commit: `b343a47`
- Snapshot: `fitness_ai_snapshot_2026-06-26_1d44b3d_preserve-primary-workout-rotation-after-catalog-expansion.zip`
- Accepted scope: improved deterministic catalog breadth and specialized movement reachability past quality gates.
- Preserved: sizing, immediate refresh anti-repeat, selected/Active persistence, Today de-dup, and no provider/AI workout path.
- Deferred: full eligibility matrix, complete catalog reachability, rolling exposure, deeper movement-family de-duplication.

## Core doctrine

Backend owns truth.

AI/provider may propose or explain only inside validated contracts.

Backend validates and approves.

User sees only approved output.

Deterministic fallback always works.

## Bite by bite, just bigger bites

The permanent development doctrine is:

> Bigger milestone is okay. Bigger single patch is not okay.

Large objectives may be authorized only when internally phased. Single patches remain narrow and tied to a specific diagnostic, test, implementation, or documented process change.

Example:

```text
Large milestone
→ diagnostic / current data shape
→ failing or coverage test
→ narrow implementation
→ focused validation
→ prior-regression validation
→ original smoke reproduction
→ project memory update
→ Architecture acceptance
```

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

Low-risk changes use normal patch/focused validation.

Medium-risk changes require light diagnostic, focused test, narrow patch, regression validation, and smoke if user-visible.

High-risk changes require diagnostic first, failing/coverage test, narrow patch, regression validation, original smoke reproduction, Linux/browser smoke when runtime-relevant, project memory update, and Architecture acceptance.

High-risk examples include workout generation, exercise catalog selection/scoring, persistence/state behavior, nutrition targets/suggestions, AI/provider output, recommendation logic, and cross-domain coaching synthesis.

## Patch stacking stop conditions

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

When a stop condition triggers: do not reset blindly, do not continue blind patching, produce a short diagnostic handoff, and request an Architecture decision.

## Bug-to-regression-test rule

Every real smoke failure must become one of:

1. automated regression test,
2. diagnostic/coverage test,
3. documented limitation with an explicit reason it cannot be automated yet,
4. backlog item if intentionally deferred.

No major smoke failure should disappear as tribal knowledge.

Recent examples:

- Workout Preview Full-Slot Rotation v1: `variation 0 -> variation 1` repeated Dumbbell Single-Leg RDL; the quality gate reproduced and fixed this path.
- Exercise Catalog Utilization v1: catalog breadth was too low, preview rotation regressed after expansion, and home-gym hinge/vertical_pull regression was caught by Linux validation.

## Provider / AI-specific rule

No provider output is accepted unless it is schema-valid, validator-approved, fact-grounded, fallback-safe, and free of invented numbers, invented foods, invented exercises, unsupported health claims, and hidden raw provider output in normal UI.

Provider may propose. Backend validates. User sees only approved output.

## Delivery style

Dustin runs the commands.

Assistants provide copy/paste-ready PowerShell and bash command blocks.

Long handoffs must be one copy/paste-ready code block.

Do not use `git add .`.

Do not commit snapshots, `qa_artifacts`, runtime artifacts, patch files, or temp scripts.

Temporary patch/apply artifacts live outside the repo, normally in `C:\projects`.

Windows repo: `C:\projects\fitness_ai`.

Linux runtime repo: `~/projects/fitness-ai-platform`.

Architecture owns merges to `main`.

Backend owns feature-branch implementation, validation, push, snapshot, and handoff.
