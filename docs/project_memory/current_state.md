# Current Project State

Last updated: 2026-06-18

## Project

AI Health Coach / fitness-ai

## Current branch

`feature/training-evidence-claim-service`

## Latest accepted milestone

`Nutrition Full Report Runtime QA Matrix v1`

Runtime QA result: `PASS_MATRIX_WITH_SAFE_FALLBACKS`.

## Current provisional milestone

`Nutrition Provider Matrix Rejection Analysis v1` is implemented and pending Architecture review.

## Next recommended milestone after Nutrition Provider Matrix Rejection Analysis v1

If Architecture accepts this analysis, the next recommended milestone is:

`Nutrition Provider Matrix Retry Runtime QA v1`

This should rerun users 101-105 through the opt-in Nutrition full-report runtime matrix with qwen2.5:3b. It should not run qwen3 and should not promote Nutrition to Level 5.

## Current model/provider status

- Deterministic path is default and must remain the public-safe baseline.
- `direct_ollama` with `qwen2.5:3b` is the practical supported opt-in model for Training and the isolated Nutrition provider implementation path.
- Nutrition section-only opt-in runtime QA passed with `qwen2.5:3b`.
- Nutrition full-report opt-in runtime QA passed as `PASS_WITH_SAFE_FALLBACK`: provider parsed, validator rejected one candidate, deterministic fallback completed and persisted safely.
- Nutrition full-report runtime matrix passed as `PASS_MATRIX_WITH_SAFE_FALLBACKS`: user 102 provider-approved, users 101/103/104/105 safe-fallback, no failures.
- Full-report provider execution is async/background only.
- `qwen3` remains experimental only and is not promoted.
- The old CrewAI full-report coordinator can fail; deterministic fallback composition protects public report output.

## Current section maturity

| Section | Current status | Maturity |
|---|---|---|
| training | Provider-integrated full-report section, opt-in direct_ollama/qwen2.5 path | Level 5 |
| nutrition_target_display | Backend-approved target display contract; input to Nutrition Report Section | Level 2 |
| nutrition_report_section | Backend-owned evidence/claims/fallback boundary plus isolated opt-in provider implementation; section-only runtime QA accepted; full-report runtime matrix accepted with safe fallbacks; matrix rejection analysis adds safe unavailable-food-suggestion handling; not Level 5 | Level 4 |
| grounded_recommendation | Strong approved contract but cross-domain; not next provider voice section | Level 3 |
| overall_score | Deterministic/coordinator-structured | Level 1 |
| profile_context | Deterministic/coordinator-structured | Level 1 |
| biggest_issue | Deterministic/coordinator-structured | Level 1 |
| likely_cause | Deterministic/coordinator-structured | Level 1 |
| priority_action | Deterministic/coordinator-structured | Level 1 |
| best_recommendation | Deterministic/coordinator-structured | Level 1 |

Provider-integrated report sections: `training` only.

## What is safe to build next

- Nutrition Provider Matrix Retry Runtime QA v1.
- Rerun users 101-105 full opt-in Nutrition full-report runtime matrix with qwen2.5:3b.
- Verify whether numeric allowlist plus unavailable-food-suggestion prompt/validator improvements improve approval rate while preserving fallback safety.
- Additional negative parser/validator tests after observing real qwen2.5 output.

## What must not be changed casually

- Deterministic default behavior.
- Parser/validator strictness.
- Provider opt-in boundary.
- Report persistence safety boundary.
- Full-report composition fallback boundary.
- Training evidence/claim validator rules.
- Nutrition boundary rule that provider execution is isolated/config-gated and not full-report integrated yet.
- The rule that Training is the only provider-integrated full-report section.
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
3. Accidentally expanding provider ownership beyond Training.
4. Nutrition full-report runtime safety or matrix safety being mistaken for Level 5 promotion before Architecture approval.
5. Legacy CrewAI coordinator being mistaken for the future full-report voice layer.
6. Generic coaching language degrading product quality even when technically safe.
7. Safe Nutrition provider metadata accidentally leaking raw/debug fields into persisted history during runtime QA or future promotion work.

## What a new AI assistant should read first

Read `docs/project_memory/README.md`, then this file, then the role-specific handoff under `docs/project_memory/handoffs/`.
