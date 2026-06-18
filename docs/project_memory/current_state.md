# Current Project State

Last updated: 2026-06-18

## Project

AI Health Coach / fitness-ai

## Current branch

`feature/training-evidence-claim-service`

## Latest accepted milestone

`Nutrition Provider Contract Scaffolding v1`

## Current provisional milestone

`Nutrition Provider Opt-In Implementation v1` is implemented locally and pending Architecture review.

## Next recommended milestone after Nutrition Provider Opt-In Implementation v1

If Architecture accepts this implementation, the next recommended milestone is `Nutrition Provider Opt-In Runtime QA v1`.

Do not wire Nutrition into async full-report generation or persistence until Architecture explicitly approves that integration milestone.

## Current model/provider status

- Deterministic path is default and must remain the public-safe baseline.
- `direct_ollama` with `qwen2.5:3b` is the practical supported opt-in model for Training and the isolated Nutrition provider implementation path.
- Full-report provider execution is async/background only.
- `qwen3` remains experimental only and is not promoted.
- The old CrewAI full-report coordinator can fail; deterministic fallback composition protects public report output.

## Current section maturity

| Section | Current status | Maturity |
|---|---|---|
| training | Provider-integrated full-report section, opt-in direct_ollama/qwen2.5 path | Level 5 |
| nutrition_target_display | Backend-approved target display contract; input to future Nutrition Report Section | Level 2 |
| nutrition_report_section | Backend-owned evidence/claims/fallback boundary plus isolated opt-in provider implementation; not full-report integrated | Level 4 |
| grounded_recommendation | Strong approved contract but cross-domain; not next provider voice section | Level 3 |
| overall_score | Deterministic/coordinator-structured | Level 1 |
| profile_context | Deterministic/coordinator-structured | Level 1 |
| biggest_issue | Deterministic/coordinator-structured | Level 1 |
| likely_cause | Deterministic/coordinator-structured | Level 1 |
| priority_action | Deterministic/coordinator-structured | Level 1 |
| best_recommendation | Deterministic/coordinator-structured | Level 1 |

Provider-integrated report sections: `training` only.

## What is safe to build next

- Architecture review of Nutrition Provider Opt-In Implementation v1.
- Nutrition Provider Opt-In Runtime QA v1 if Architecture accepts this implementation.
- Additional fake-provider parser/validator/fallback tests after observing real provider output.
- Safe runtime QA planning for Nutrition provider opt-in behavior.

## What must not be changed casually

- Deterministic default behavior.
- Parser/validator strictness.
- Provider opt-in boundary.
- Report persistence safety boundary.
- Full-report composition fallback boundary.
- Training evidence/claim validator rules.
- Nutrition boundary rule that provider execution is isolated/config-gated and not full-report integrated yet.
- The rule that Training is the only provider-integrated full-report section.

## Expected validation/tests

For docs-only memory/review updates:

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
4. Nutrition provider execution moving too fast into full-report integration before explicit runtime QA and Architecture approval.
5. Legacy CrewAI coordinator being mistaken for the future full-report voice layer.
6. Generic coaching language degrading product quality even when technically safe.

## What a new AI assistant should read first

Read `docs/project_memory/README.md`, then this file, then the role-specific handoff under `docs/project_memory/handoffs/`.
