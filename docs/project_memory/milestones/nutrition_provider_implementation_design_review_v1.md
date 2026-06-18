# Nutrition Provider Implementation Design Review v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / docs-only design review complete

Date/commit: 2026-06-18 / Unknown until committed; verify with `git log --oneline -5`

## Problem

Nutrition Provider Contract Scaffolding v1 established code-level parser, validator, fallback, and metadata scaffolding, but Architecture required a design review before any Nutrition provider execution code is added.

The project needed to define exactly how a future opt-in Nutrition provider should be wired while preserving deterministic defaults, strict validation, safe fallback, no live Ollama in pytest, and Training as the only currently provider-integrated section.

## What changed

Added a docs-only design review:

- `docs/project_memory/reviews/nutrition_provider_implementation_design_review_v1.md`

Updated project memory state and open questions:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Files/modules touched

Docs only.

No runtime code changed.

## Architecture decision

`Nutrition Provider Contract Scaffolding v1` is accepted.

This review recommends:

`READY_FOR_PROVIDER_IMPLEMENTATION_V1`

This means a future opt-in provider implementation milestone can be approved if Architecture agrees.

It does not mean Nutrition is provider-integrated in the full report yet.

## Validation/tests

Expected docs-only validation:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only`
- `git diff --check`

Runtime tests are not required because no runtime code changed.

## Runtime QA

Not required for this docs-only review milestone.

Future runtime QA will be required before Nutrition provider promotion or Level 5 status.

## Known limitations

- No provider execution exists yet.
- Nutrition remains not provider-integrated.
- No qwen3 testing is approved.
- The next implementation milestone must still use fake generators in pytest and explicit runtime opt-in before real provider QA.

## Next recommended step

`Nutrition Provider Implementation v1`

Alternative safer name:

`Nutrition Provider Opt-In Implementation v1`

Recommended scope:

- implement provider execution behind explicit opt-in config
- mirror Training provider service pattern where appropriate
- keep Nutrition parser/validator/context separate
- use qwen2.5:3b for initial opt-in runtime QA
- no qwen3
- no Level 5 promotion
- no live Ollama in pytest
