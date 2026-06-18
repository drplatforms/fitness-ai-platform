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

`Nutrition Level 5 Promotion Runtime QA v1` accepted `nutrition_report_section` as Level 5 runtime validated under explicit opt-in provider gates. Per-report persisted metadata lists `nutrition_report_section` only when approved Nutrition provider output actually rendered. Fallback or disabled-gate Nutrition reports remain explicit and do not imply provider approval. Forced-invalid fallback runtime QA confirmed that fallback reports keep `provider_integrated_report_sections=training`.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` is now a Level 5 opt-in provider-integrated full-report section after accepted provider-approved seeded runtime QA, the explicit Nutrition Provider Level 5 Promotion v1 patch, and accepted Nutrition Level 5 Promotion Runtime QA v1. This promotion does not make direct_ollama default, remove fallback, remove gates, or merge Nutrition Target Display into Nutrition Report Section.

## Latest runtime validation

Nutrition Level 5 Forced-Fallback Runtime QA v1 passed with `NUTRITION_LEVEL_5_RUNTIME_SEMANTICS_COMPLETE`:

- forced-invalid users 101-105 all passed deterministic fallback semantics
- `nutrition_fallback_used=true`
- `nutrition_fallback_reason=qa_forced_invalid_provider_output`
- `nutrition_section_source=deterministic_nutrition_report_section_fallback`
- `provider_integrated_report_sections=training`
- live model was not called
- leakage checks were clean
- qwen3 was not used
- control user 102 remained provider-approved when forced-invalid mode was disabled

Nutrition Level 5 Promotion Runtime QA v1 previously passed with `NUTRITION_REPORT_SECTION_LEVEL_5_RUNTIME_VALIDATED`:

- users 101-105 all passed provider-approved Level 5 runtime QA
- approved reports included `provider_integrated_report_sections=training,nutrition_report_section`
- disabled-gate user 101 kept `provider_integrated_report_sections=training`
- Nutrition Report Section remained Level 5 with `provider_status=opt_in_full_report_integrated`
- Nutrition Target Display remained separate Level 2 with `provider_status=none`
- public/persisted leakage checks were clean

Fallback runtime semantics are now runtime-tested through the QA-only forced-invalid provider mode. This closes the prior documented coverage gap. Public-facing wording should remain conservative: the forced-invalid mode is QA-only, disabled by default, and not normal user behavior.

## Next likely section path

Next recommended milestone should be selected separately: Demo / Deployment Packaging Design v1 for recruiter/demo readiness, Nutrition Explanation Value-Aware Copy v1 for product depth, or a UI/README/portfolio polish pass.

## Daily Coaching Product Loop planning note

`Daily Coaching Product Loop v1` does not change section maturity or provider ownership.

The planned `Daily Next Action Panel v1` should consume existing backend-approved section state and routing signals. It should not become a new provider-owned report section, and it should not merge `nutrition_target_display` with `nutrition_report_section`.

Expected ownership:

- Backend owns next-action selection, reason codes, workflow pointers, and eligibility checks.
- Streamlit renders the selected action on the Today page.
- AI/provider output may be displayed only after existing backend validation and must not independently control navigation or daily action ranking.
