# Prompt Lab Lifecycle Contract

**Status:** Active development contract
**Current accepted main:** `23b5378 Merge daily coach fully free source-data lab evidence v1`

Prompt Lab is a controlled engineering workflow for provider/prompt experiments. It is not a production runtime feature and not permission for endless same-lane tuning.

## Required Records

Each prompt experiment must record prompt family/version, branch/commit, baseline prompt/version, model/provider, scenario set, output artifacts, acceptance decision, rollback path, prompt changelog, provider/model matrix, token/cost telemetry, and artifact safety status.

## Evaluation Rules

Use stable scenarios or captured source-data packets. Compare against the accepted baseline, not memory. Review factuality, claim risk, usefulness, naturalness, source-data use, backend-bound language, repetition, food/training/recovery guidance, and cost.

## Acceptance Criteria

Accept only if product-relevant quality improves without increasing unsafe claims, invented facts, raw-data exposure, or provider dependency beyond scope.

## Post-Hoc Audit vs Generation-Time Cage

Post-hoc audit reports findings after generation. Generation-time cage constrains the model before generation. Ceiling tests should prefer clean source data and post-hoc audit; product surfaces may need generation-time constraints when scoped.

## Stop Condition

Stop prompt/provider iteration when outputs are competent but generic, prompts are being tuned around weak source data, backend intelligence is thin, UI/renderer boundaries are not ready, or repeated experiments do not beat baseline.

Current stop condition has been reached for Daily Coach provider voice iteration. Fully Free Source-Data Lab v1 was useful but not meaningfully better than v4. Provider voice iteration is paused until Backend Intelligence Foundation improves the source-data brain.
