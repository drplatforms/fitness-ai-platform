# Current Project State

Last updated: 2026-06-18

## Project

AI Health Coach / fitness-ai

## Current branch

`feature/daily-coaching-product-loop-v1`

## Latest accepted milestone

`Daily Coaching Product Loop v1` planning was accepted.

Planning status: `DAILY_COACHING_PRODUCT_LOOP_V1_PLAN_ACCEPTED`.

## Current implementation milestone

`Daily Next Action Panel v1` is implemented and pending QA.

Implementation status: `DAILY_NEXT_ACTION_PANEL_V1_IMPLEMENTED_PENDING_QA`.

The first product-loop slice adds a deterministic backend next-action service and Today-page action card. Backend owns the action decision; Streamlit renders one primary action; no provider output controls navigation or invents food, calorie, macro, workout, fatigue, or recovery claims.

## Next recommended milestone options

- Daily Next Action Panel v1 QA.
- Demo / Deployment Packaging Design v1.
- Nutrition Explanation Value-Aware Copy v1.
- UI polish / screenshot capture pass.
- GitHub README / portfolio update pass.

## Current model/provider status

- Deterministic path is default and must remain the public-safe baseline.
- `direct_ollama` with `qwen2.5:3b` is the practical supported opt-in model for Training and the isolated Nutrition provider implementation path.
- Nutrition section-only opt-in runtime QA passed with `qwen2.5:3b`.
- Nutrition full-report opt-in runtime QA passed as `PASS_WITH_SAFE_FALLBACK`: provider parsed, validator rejected one candidate, deterministic fallback completed and persisted safely.
- Nutrition full-report runtime matrix passed as `PASS_MATRIX_WITH_SAFE_FALLBACKS`: user 102 provider-approved, users 101/103/104/105 safe-fallback, no failures.
- Nutrition full-report retry matrix passed as `PASS_MATRIX_WITH_SAFE_FALLBACKS`: all seeded users safely fell back; approval quality did not improve.
- Nutrition diagnostic matrix retry passed with `PASS_DIAGNOSTICS_WITH_SAFE_FALLBACKS`; diagnostic propagation is working.
- Nutrition practical food focus runtime QA passed with `PASS_WITH_IMPROVED_DIAGNOSTICS`: user 105 is now provider-approved and the no-approved-suggestion path appears fixed.
- Nutrition approved suggestion context inspection/tuning added backend-approved `practical_food_focus` option lists and requires direct-Ollama to copy one exact backend-approved option sentence.
- Nutrition approved suggestion runtime QA passed with `PASS_PROVIDER_APPROVED_MATRIX`: users 101-105 were all provider-approved, practical_food_focus failures dropped to 0, fallback false for all users, and public/persisted leakage checks remained clean.
- Nutrition Provider Level 5 Promotion v1 promoted `nutrition_report_section` to Level 5 provider-integrated status while preserving opt-in gates, deterministic fallback, strict validation, and public/persisted sanitizer boundaries.
- Nutrition Level 5 Promotion Runtime QA v1 passed with users 101-105 all provider-approved at Level 5, `provider_integrated_report_sections=training,nutrition_report_section` on approved provider output, disabled-gate semantics preserved for user 101, and safety/leakage checks clean.
- Nutrition Level 5 Forced-Fallback Runtime QA v1 passed with `PASS_FORCED_FALLBACK_RUNTIME_QA`: users 101-105 forced invalid provider output, validation rejected, deterministic fallback rendered, live model was not called, `provider_integrated_report_sections=training`, leakage checks were clean, and qwen3 was not used.
- Control user 102 passed the normal provider-approved path with forced-invalid mode disabled: `nutrition_section_source=direct_ollama_approved` and `provider_integrated_report_sections=training,nutrition_report_section`.
- Nutrition Level 5 runtime semantics are complete across provider-approved, disabled-gate deterministic, and forced-invalid deterministic fallback paths.
- Full-report provider execution is async/background only.
- `qwen3` remains experimental only and is not promoted.
- The old CrewAI full-report coordinator can fail; deterministic fallback composition protects public report output.

## Current section maturity

| Section | Current status | Maturity |
|---|---|---|
| training | Provider-integrated full-report section, opt-in direct_ollama/qwen2.5 path | Level 5 |
| nutrition_target_display | Backend-approved target display contract; input to Nutrition Report Section | Level 2 |
| nutrition_report_section | Provider-integrated full-report section with opt-in direct_ollama/qwen2.5 path, strict parser/validator boundary, backend-approved practical_food_focus options, report-specific provider-integrated metadata, and deterministic fallback | Level 5 |
| grounded_recommendation | Strong approved contract but cross-domain; not next provider voice section | Level 3 |
| overall_score | Deterministic/coordinator-structured | Level 1 |
| profile_context | Deterministic/coordinator-structured | Level 1 |
| biggest_issue | Deterministic/coordinator-structured | Level 1 |
| likely_cause | Deterministic/coordinator-structured | Level 1 |
| priority_action | Deterministic/coordinator-structured | Level 1 |
| best_recommendation | Deterministic/coordinator-structured | Level 1 |

Provider-integrated section maturity: `training` and `nutrition_report_section`. Per-report `provider_integrated_report_sections` metadata still lists Nutrition only when approved provider output actually rendered; fallback and disabled-gate Nutrition reports remain explicit.

## What is safe to build next

- Daily Coaching Product Loop v1 planning/design.
- Daily Next Action Panel v1 as a narrow deterministic Today-page implementation slice.
- Demo / Deployment Packaging Design v1.
- Nutrition Explanation Value-Aware Copy v1.
- UI polish / screenshot capture pass.
- GitHub README / portfolio update pass.
- Public claims can now say Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode, while still clarifying that this mode is not normal user behavior.
- Next provider-quality section milestone.
- Keep deterministic fallback, provider gates, strict parser/validator behavior, and public/persisted sanitizer boundaries unchanged.
- Preserve the distinction between `nutrition_target_display` and `nutrition_report_section`.
- Preserve qwen2.5:3b as the only accepted Nutrition provider model; qwen3 remains experimental only.

## Current product loop direction

The next product development priority is daily usefulness: help the user answer “What should I do today?” from the Today page without reopening provider safety or Level 5 semantics.

Daily Coaching Product Loop v1 should connect existing backend-approved state into a practical loop:

```text
recovery check-in
→ current recovery/training/nutrition state
→ nutrition target-vs-actual and logging completeness
→ workout preview / workout execution
→ report guidance
→ one backend-approved next action
```

Daily Next Action Panel v1 is implemented pending QA. The deterministic service returns exactly one action from the approved v1 action set, with backend-owned reason and workflow target. The Today page renders this card near the top without exposing raw provider/debug metadata.

Approved v1 action set: Complete recovery check-in, Keep training conservative, Log a meal or snack, Review nutrition target progress, Review today’s workout, Review today’s report guidance.

The panel remains backend-truth-owned. It surfaces one primary action, a short backend-supported reason, and a workflow pointer, but does not allow AI/provider output to invent navigation, food, calorie, macro, workout, fatigue, or recovery claims.

## What must not be changed casually

- Deterministic default behavior.
- Parser/validator strictness.
- Provider opt-in boundary.
- Report persistence safety boundary.
- Full-report composition fallback boundary.
- Training evidence/claim validator rules.
- Nutrition boundary rule that provider execution and full-report integration remain explicitly config-gated.
- The rule that provider-integrated metadata must not imply provider-approved Nutrition content when Nutrition falls back or is not attempted.
- The debug endpoint clarification: `validation_errors=[]` and `raw_output_preview_truncated=null` are acceptable only in explicit debug endpoint metadata and remain forbidden in public/user-facing/persisted output.

## Expected validation/tests

For docs-only memory/review updates:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only`
- `git diff --check`
- Verify required docs exist.
- Verify headings are present and accurate.
- Verify no runtime code changed.

For code/tooling changes:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code`
- Relevant focused tests.
- Full `pytest` when practical.
- No live Ollama calls in pytest.

## Top open risks

1. Context loss across long chat sessions.
2. Accidentally treating qwen3 as promoted or default.
3. Accidentally expanding provider ownership beyond Training and Nutrition Report Section.
4. Nutrition Level 5 runtime validation being mistaken for direct_ollama default approval.
5. Future public-facing wording overstating the QA-only forced-invalid mode as normal production behavior.
6. Future changes accidentally marking fallback or disabled-gate Nutrition reports as provider-approved.
7. Legacy CrewAI coordinator being mistaken for the future full-report voice layer.
8. Generic coaching language degrading product quality even when technically safe.
9. Safe Nutrition provider metadata accidentally leaking raw/debug fields into persisted history during future runtime QA or provider work.

## What a new AI assistant should read first

Read `docs/project_memory/README.md`, then this file, then the role-specific handoff under `docs/project_memory/handoffs/`.
