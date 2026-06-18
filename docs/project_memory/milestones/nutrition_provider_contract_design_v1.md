# Nutrition Provider Contract Design v1

Branch: `feature/training-evidence-claim-service`

Status: Design complete / pending Architecture review

Date/commit if known: Unknown / verify with git log.

## Problem

Nutrition Report Section Boundary v1 created backend-owned evidence, claims, validation, and deterministic fallback. Nutrition is still not provider-integrated. Before any qwen/provider implementation, the project needs an exact provider-safe contract.

## What changed

Added a design document defining:

- provider-safe nutrition context shape
- exact CandidateNutritionReportSection JSON schema
- strict parser rules
- strict validator rules
- numeric validation policy
- logging-completeness confidence ceilings
- canonical food validation rules
- unsupported claim rejection categories
- safe metadata allowlist
- provider fallback design
- pytest plan
- future runtime QA matrix

## Files/modules touched

- `docs/project_memory/designs/nutrition_provider_contract_design_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/milestones/nutrition_provider_contract_design_v1.md`

## Architecture decision

Design only. Do not implement provider execution, do not call `direct_ollama` from Nutrition, do not promote qwen3, and do not mark Nutrition provider-integrated.

## Validation/tests

Docs-only validation is sufficient:

- `scripts/dev_commit_check.ps1 -Mode docs-only`
- `git diff --check`

## Runtime QA

Not required because no runtime behavior changed.

## Known limitations

- Provider-safe context model is not implemented yet.
- Parser/validator scaffolding is not implemented yet.
- Nutrition provider execution is not implemented and remains not approved.

## Next recommended step

Nutrition Provider Contract Scaffolding v1, also known as Nutrition Provider Parser Validator Scaffolding v1.
