# Current Project State

Last updated: 2026-06-19

## Project

AI Health Coach / fitness-ai

## Current branch

`main`

## Latest accepted milestone

`Coach Voice Contract Tightening v1` was accepted and merged to main.

Final accepted status: `COACH_VOICE_CONTRACT_TIGHTENING_V1_ACCEPTED_WITH_MODEL_FINDINGS`.

Accepted model findings:

- `qwen3:8b` remains the best practical evaluation-only bounded coach voice candidate.
- `qwen3:32b` remains the best offline / chores-mode quality reference.
- `qwen2.5:3b` improved to a compliant small baseline but remains more generic.
- `qwen3:14b` partially improved but remains unreliable.
- `qwen3:30b-a3b` remains incompatible with the strict JSON-only contract.

No model is production-approved. No Today, Streamlit, report, provider, catalog, workout, or nutrition runtime path was changed.

## Current implementation milestone

`Daily Coach Narrative v1 Planning` was accepted by Architecture.

`Daily Coach Narrative Context Builder v1` is implemented and pending QA/Architecture review.

Implementation status: `DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_IMPLEMENTED_PENDING_QA`.

The context builder creates a deterministic `DailyCoachNarrativeContext` from the existing Daily Next Action state. It preserves the selected action and workflow target exactly, produces explicit approved facts/limitations/forbidden claims, and creates deterministic fallback wording. It does not call a model and does not integrate into Today, Streamlit, reports, or production provider paths.

## Next recommended milestone options

- Daily Coach Narrative Context Builder v1 Architecture/QA review.
- Daily Coach Narrative Offline Runtime QA v1 after Context Builder acceptance.
- Logging UX Speed & Friction Reduction v1.
- Nutrition Explanation Value-Aware Copy v1.

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

- Exercise Catalog Expansion v1 Architecture/QA review.
- Logging UX Speed & Friction Reduction v1.
- Bounded Coach Voice Bakeoff v1.
- Daily Coach Narrative v1.
- Nutrition Explanation Value-Aware Copy v1.
- Demo / Deployment Packaging Design v1.
- UI polish / screenshot capture pass.
- GitHub README / portfolio update pass.
- Public claims can now say Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode, while still clarifying that this mode is not normal user behavior.
- Next provider-quality section milestone.
- Keep deterministic fallback, provider gates, strict parser/validator behavior, and public/persisted sanitizer boundaries unchanged.
- Preserve the distinction between `nutrition_target_display` and `nutrition_report_section`.
- Preserve qwen2.5:3b as the only accepted Nutrition provider model; qwen3 remains experimental only.

## Current product loop direction

Daily Next Action Panel v1 is accepted and merged. The Today page now answers “What should I do today?” with one deterministic backend-owned next action.

Daily Coaching Product Loop v1 connects existing backend-approved state into a practical loop:

```text
recovery check-in
→ current recovery/training/nutrition state
→ nutrition target-vs-actual and logging completeness
→ workout preview / workout execution
→ report guidance
→ one backend-approved next action
```

Daily Next Action Panel v1 is accepted. The deterministic service returns exactly one action from the approved v1 action set, with backend-owned reason and workflow target. The Today page renders this card near the top without exposing raw provider/debug metadata.

Approved v1 action set: Complete recovery check-in, Keep training conservative, Log a meal or snack, Review nutrition target progress, Review today’s workout, Review today’s report guidance.

The panel remains backend-truth-owned. It surfaces one primary action, a short backend-supported reason, and a workflow pointer, but does not allow AI/provider output to invent navigation, food, calorie, macro, workout, fatigue, or recovery claims.

## Current catalog direction

Catalog Expansion & Curation v1 planning was accepted. Food Catalog Expansion v1 is now implemented pending review.

The app can now tell the user to log food or review a workout; the next product-quality bottleneck is whether those actions are easy and useful. Catalog expansion should remain deterministic, curated, inspectable, testable, and backend-owned.

Food Catalog Expansion v1 increases the starter canonical food catalog from 132 to 202 curated entries. The 70-entry expansion covers practical lean proteins, dairy/eggs, grains/starches, legumes, fruits, vegetables, fats/seeds, and simple convenience foods. Existing per-100g nutrient storage, manually curated source policy, Moderate confidence, default grams, aliases, and canonical search/logging behavior are preserved.

Exercise Catalog Expansion v1 remains recommended second to improve workout variety, equipment matching, substitutions, and recovery-aware options.

Do not add RAG, embeddings, scraping, AI-generated production catalog entries, meal planning, unreviewed food dumps, or clinical nutrition claims.



## Current AI provider evaluation direction

Bounded Coach Voice Bakeoff v1 and Coach Voice Contract Tightening v1 are accepted and merged to `main` as offline evaluation milestones.

Current accepted coach voice findings:

- `qwen3:8b` remains the best practical evaluation-only bounded coach voice candidate.
- `qwen3:32b` remains the best offline / chores-mode quality reference, but it is too slow for tight Today UI.
- `qwen2.5:3b` improved to a compliant small baseline after contract tightening, but copy remains more generic.
- `qwen3:14b` partially improved but remains unreliable.
- `qwen3:30b-a3b` remains incompatible with strict JSON-only output.

No model is production-approved. `qwen3` remains not approved. No model may write to Today, Streamlit, reports, production provider paths, next-action selection, food suggestions, exercise suggestions, targets, workouts, recovery status, nutrition claims, or medical claims.

Daily Coach Narrative v1 Planning is the current docs-only bridge from offline bakeoff evidence toward a future bounded daily narrative layer.

Current planned future narrative sequence:

```text
Daily Next Action state
→ DailyCoachNarrativeContext
→ CandidateDailyCoachNarrative JSON attempt
→ narrative parser/validator
→ ApprovedDailyCoachNarrative or deterministic fallback
→ future Developer Mode preview
→ future normal Today UI only after Architecture acceptance
```

Recommended next milestone after planning acceptance: `Daily Coach Narrative Context Builder v1`.

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
10. Catalog expansion becoming an unreviewed dump instead of deterministic curated seed data.
11. Food catalog entries creating false precision through weak source/confidence handling.
12. Exercise catalog expansion changing workout generation behavior before the curation plan is accepted.

## What a new AI assistant should read first

Read `docs/project_memory/README.md`, then this file, then the role-specific handoff under `docs/project_memory/handoffs/`.

## Coach Voice Contract Tightening v1

Coach Voice Contract Tightening v1 is accepted and merged to `main`.

Final accepted status: `COACH_VOICE_CONTRACT_TIGHTENING_V1_ACCEPTED_WITH_MODEL_FINDINGS`.

The tightened prompt/schema packaging improved model compliance across all five accepted context packs while preserving strict validators and production boundaries.

Accepted model findings:

- `qwen3:8b`: 5/5 pass, best practical evaluation-only bounded coach voice candidate, not production-approved.
- `qwen3:32b`: 5/5 pass, best offline / chores-mode quality reference, too slow for tight Today UI, not production-approved.
- `qwen2.5:3b`: 5/5 pass after contract tightening, useful compliant small baseline, still more generic.
- `qwen3:14b`: 2/5 pass, partial improvement, still unreliable.
- `qwen3:30b-a3b`: 0/5 pass, still incompatible with strict JSON-only output.

No model is promoted. qwen3 remains not approved. No Today, Streamlit, report, production provider, catalog, workout generation, nutrition formula, fallback, or provider gate behavior changed.

## Daily Coach Narrative v1 Planning

Daily Coach Narrative v1 Planning is implemented as a docs-only milestone on `feature/daily-coach-narrative-v1-planning` pending Architecture acceptance.

Planning status: `DAILY_COACH_NARRATIVE_V1_PLANNED_PENDING_ARCHITECTURE_ACCEPTANCE`.

The planned future narrative layer would explain the backend-selected Daily Next Action with compact coach-style language while preserving backend authority over action selection, workflow target, confidence, approved facts, forbidden claims, and fallback behavior.

Proposed future context:

```text
Daily Next Action state
→ DailyCoachNarrativeContext
→ CandidateDailyCoachNarrative JSON attempt
→ narrative parser/validator
→ ApprovedDailyCoachNarrative or deterministic fallback
```

Planning confirms:

- the narrative may explain the approved action but may not choose or change it
- the model owns wording only
- backend owns truth, confidence, approved facts, forbidden claims, validation, and fallback
- output should use the tightened coach voice JSON object unless a later implementation proves a need to specialize it
- failed model output falls back to deterministic Daily Next Action wording
- the first implementation slice should be `Daily Coach Narrative Context Builder v1`, with no model call

Normal Today UI integration remains out of scope until later runtime QA and Architecture acceptance.

## Daily Coach Narrative Context Builder v1

Daily Coach Narrative Context Builder v1 is implemented on `feature/daily-coach-narrative-context-builder-v1` pending QA/Architecture acceptance.

Implementation status: `DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_IMPLEMENTED_PENDING_QA`.

Implemented:

- `DailyCoachNarrativeContext` model
- deterministic context builder service
- context validation helper
- focused unit tests
- project memory milestone/review docs

The builder consumes the existing deterministic Daily Next Action result and returns a compact backend-approved context packet for future narrative provider QA. It preserves `next_action_id`, `next_action_title`, `next_action_reason`, `workflow_target`, `priority`, and `severity` exactly. `approved_focus` is exactly the Daily Next Action title.

The builder creates explicit approved facts, approved limitations, forbidden claim categories, and deterministic fallback wording. It filters raw/debug/provider-like evidence keys and does not expose raw logs, raw provider output, raw validation errors, raw debug payloads, full catalog dumps, or unfiltered history.

No model is called. No qwen, Ollama, direct_ollama, or CrewAI path is introduced. No Today/Streamlit/report integration occurs in this slice.
