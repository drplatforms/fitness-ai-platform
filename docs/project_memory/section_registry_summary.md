# Section Registry Summary

Last updated: 2026-06-18

## Current full-report sections

| Section id | Display purpose | Current maturity | Provider status |
|---|---|---:|---|
| overall_score | High-level score/status | 1 | None |
| profile_context | User profile and context | 1 | None |
| grounded_recommendation | Approved action-plan recommendation | 3 | Not provider-owned |
| nutrition_target_display | Backend-approved target display | 2 | None |
| nutrition_report_section | Provider-integrated full-report Nutrition voice section with opt-in direct_ollama/qwen2.5 path, strict parser/validator, backend-approved practical_food_focus options, report-specific provider-integrated metadata, and deterministic fallback | 5 | direct_ollama opt-in integrated |
| training | Training report section | 5 | direct_ollama opt-in integrated |
| biggest_issue | Current issue summary | 1 | None |
| likely_cause | Possible contributing factor | 1 | None |
| priority_action | Highest-priority action | 1 | None |
| best_recommendation | Best recommendation summary | 1 | None |

## Provider-integrated report sections

Section maturity: `training`, `nutrition_report_section`.

`Nutrition Level 5 Promotion Runtime QA v1` accepted `nutrition_report_section` as Level 5 runtime validated under explicit opt-in provider gates. Per-report persisted metadata lists `nutrition_report_section` only when approved Nutrition provider output actually rendered. Fallback or disabled-gate Nutrition reports remain explicit and do not imply provider approval.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` is now a Level 5 opt-in provider-integrated full-report section after accepted provider-approved seeded runtime QA, the explicit Nutrition Provider Level 5 Promotion v1 patch, and accepted Nutrition Level 5 Promotion Runtime QA v1. This promotion does not make direct_ollama default, remove fallback, remove gates, or merge Nutrition Target Display into Nutrition Report Section.

## Latest runtime validation

Nutrition Level 5 Promotion Runtime QA v1 passed with `NUTRITION_REPORT_SECTION_LEVEL_5_RUNTIME_VALIDATED`:

- users 101-105 all passed provider-approved Level 5 runtime QA
- approved reports included `provider_integrated_report_sections=training,nutrition_report_section`
- disabled-gate user 101 kept `provider_integrated_report_sections=training`
- Nutrition Report Section remained Level 5 with `provider_status=opt_in_full_report_integrated`
- Nutrition Target Display remained separate Level 2 with `provider_status=none`
- public/persisted leakage checks were clean

Fallback runtime semantics were not tested because no safe QA-only forced-invalid provider mode was used. This is accepted as an honest coverage note and should not be represented as completed runtime fallback coverage.

## Next likely section path

After closeout, this branch is a candidate for merge planning. Reasonable next product-facing milestones are UI polish / screenshot capture, GitHub README / portfolio update, optional forced-fallback runtime QA harness, or the next provider-quality section milestone.
