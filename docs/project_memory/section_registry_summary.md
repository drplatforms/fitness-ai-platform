# Section Registry Summary

Last updated: 2026-06-18

## Current full-report sections

| Section id | Display purpose | Current maturity | Provider status |
|---|---|---:|---|
| overall_score | High-level score/status | 1 | None |
| profile_context | User profile and context | 1 | None |
| grounded_recommendation | Approved action-plan recommendation | 3 | Not provider-owned |
| nutrition_target_display | Backend-approved target display | 2 | None |
| nutrition_report_section | Backend-owned nutrition evidence/claims/fallback boundary plus isolated opt-in provider implementation, full-report opt-in integration, accepted diagnostic visibility, and practical_food_focus contract tuning | 4 | Full-report opt-in only; not Level 5 |
| training | Training report section | 5 | direct_ollama opt-in integrated |
| biggest_issue | Current issue summary | 1 | None |
| likely_cause | Possible contributing factor | 1 | None |
| priority_action | Highest-priority action | 1 | None |
| best_recommendation | Best recommendation summary | 1 | None |

## Provider-integrated report sections

`training` only.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` has a proven isolated opt-in provider path, an implemented full-report opt-in integration gate, accepted diagnostic visibility, and a practical_food_focus contract fix. It is not Level 5 until runtime QA, persisted-history inspection, leakage checks, provider quality review, and Architecture approval pass.

## Next likely section path

Nutrition Provider Practical Food Focus Contract Fix v1 has implemented the next provider-quality tuning step after diagnostic QA identified `practical_food_focus` as the repeated rejection field.

The next step is Nutrition Provider Practical Food Focus Runtime QA v1. Level 5 still requires Architecture approval after runtime QA, persisted-history inspection, composition fallback checks, raw/debug leakage checks, and provider approval consistency improves.
