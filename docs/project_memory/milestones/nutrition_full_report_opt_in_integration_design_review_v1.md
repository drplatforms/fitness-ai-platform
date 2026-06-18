# Nutrition Full Report Opt-In Integration Design Review v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / docs-only design review complete

Date/commit: 2026-06-18 / Unknown until committed; verify with `git log --oneline -5`

## Problem

Nutrition Provider Opt-In Runtime QA v1 proved that the isolated section-only Nutrition provider path can run safely behind explicit config gates. Architecture accepted the runtime QA result as `PASS_WITH_DEBUG_ENDPOINT_CLARIFICATION`.

The next risk is full-report integration. Nutrition should not be wired into async full-report generation, persisted history, or full-report composition without a design review that defines config gates, fallback behavior, metadata safety, runtime QA, and section maturity rules.

## What changed

Added a docs-only design review:

- `docs/project_memory/reviews/nutrition_full_report_opt_in_integration_design_review_v1.md`

Added/updated project memory:

- `docs/project_memory/milestones/nutrition_full_report_opt_in_integration_design_review_v1.md`
- `docs/project_memory/runtime_qa/nutrition_provider_opt_in_runtime_qa.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/section_registry_summary.md`

## Files/modules touched

Docs only.

No runtime code changed.

## Architecture decision

`Nutrition Provider Opt-In Runtime QA v1` is accepted.

Nutrition remains Level 4.

Training remains the only full-report provider-integrated section.

This design review recommends:

`READY_FOR_FULL_REPORT_OPT_IN_INTEGRATION_IMPLEMENTATION`

This means a future implementation milestone can wire Nutrition into full-report generation behind explicit gates, but Nutrition should not be promoted to Level 5 until runtime QA and Architecture acceptance.

## Validation/tests

Expected docs-only validation:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only`
- `git diff --check`

Runtime tests are not required because no runtime code changed.

## Runtime QA

No runtime QA is required for this docs-only review milestone.

Future runtime QA will be required after any full-report integration implementation.

## Known limitations

- No full-report integration code was added.
- Nutrition remains Level 4.
- No qwen3 testing is approved.
- No persisted-history metadata changes were made.
- The next implementation milestone must still rely on fake generators in pytest and explicit opt-in runtime QA before promotion.

## Next recommended step

`Nutrition Full Report Opt-In Integration v1`

Recommended scope:

- add explicit full-report Nutrition integration gate
- call existing Nutrition provider service from full-report composition only when allowed
- render distinct Nutrition Report Section while preserving Nutrition Target Display
- expose safe job metadata
- persist only exact-key allowlisted safe metadata
- add fake-provider full-report tests
- keep Nutrition Level 4 pending runtime QA
- no qwen3
- no Level 5 promotion
