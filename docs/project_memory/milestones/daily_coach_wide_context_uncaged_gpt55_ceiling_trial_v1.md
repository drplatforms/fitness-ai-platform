# Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

Status: Backend implementation complete / ready for Architecture and QA review.

Baseline: `main` at `718c614 Merge daily coach product voice audit gate fix v1`.

Branch: `feature/daily-coach-wide-context-uncaged-gpt55-ceiling-trial-v1`.

Requested status: `DAILY_COACH_WIDE_CONTEXT_UNCAGED_GPT55_CEILING_TRIAL_V1_IMPLEMENTATION_COMPLETE`.

## Intent

This milestone adds a developer-only ceiling trial to answer one product question:

Can GPT-5.5 produce a genuinely better Daily Coach note when it receives a much richer backend-approved context packet and fewer pre-draft writing shackles?

This is not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit phrase patch.

## Implemented direction

The trial adds a parallel tool/service path:

- build a rich but sanitized wide context packet;
- compare against deterministic baseline and current narrow Natural Draft path;
- run minimal writer prompt variants;
- capture exact first-pass draft text;
- write sanitized side-by-side artifacts;
- record token/cost telemetry fields when a provider returns usage;
- document known baseline drift without patching unrelated rich-day copy tests.

## Prompt variants

Required variants implemented:

- `current_narrow_path`
- `wide_context_minimal_prompt`
- `wide_context_practical_coach`
- `wide_context_direct_coach`

Optional variant implemented:

- `wide_context_no_style_guidance`

## Context boundary

The wide context packet may include backend-approved facts and interpretations from:

- `DailyCoachSynthesis`
- `UserHealthState`
- `DailyCoachValueAwareProviderContext`
- `ApprovedCoachBrief`

The writer prompt receives a human-readable context rendering instead of old JSON schema/validator/cage language.

The packet and artifacts must not include:

- raw DB rows
- raw provider envelopes
- secrets
- raw source payloads
- private notes
- normal Today output changes

## Provider behavior

Supported CLI providers:

- `deterministic`
- `openai`
- `direct_ollama`

Default provider remains deterministic.

Live providers require explicit `--allow-live-provider`.

The default ceiling-discovery model is `gpt-5.5`, but the CLI supports `--model` so `gpt-5.4`, `gpt-5.4-mini`, or local Ollama models can be compared later without code rewrites.

## Token / cost telemetry

Each variant records telemetry fields where available:

- provider
- model
- scenario
- prompt variant
- input tokens
- output tokens
- total tokens
- cached input tokens
- estimated cost USD
- cost estimate basis

OpenAI usage is captured when the SDK returns it.

Cost is estimated only when explicit environment prices are provided:

- `DAILY_COACH_WIDE_CONTEXT_INPUT_COST_PER_MILLION`
- `DAILY_COACH_WIDE_CONTEXT_OUTPUT_COST_PER_MILLION`

Local Ollama runs record token counts when returned and use `local_ollama_no_api_cost`.

## Artifacts

Default artifact directory:

`docs/provider_trials/daily_coach_wide_context_uncaged_gpt55_ceiling_trial_v1`

Artifacts include:

- `run_config.json`
- `wide_context_packet_summary.json`
- `prompt_variants.md`
- `first_pass_drafts.md`
- `side_by_side_comparison.md`
- `review_summary.md`
- `token_cost_telemetry.md`
- `token_cost_telemetry.csv`
- `scoring_template.md`
- `baseline_drift.md`
- `artifact_safety_summary.md`

## Known baseline drift

Architecture directed Backend to document but not patch this drift inside the ceiling trial:

- `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied `718c614` snapshot.
- Example mismatch:
  - expected: `Read the day before adding more`
  - actual: `Consider the full day`
- This is not patched in this milestone.
- Full-suite green must not be claimed if that drift remains.

## Validation expectations

Targeted validation should include:

- focused wide-context service tests;
- focused CLI tests;
- py_compile of new tool/service/model;
- targeted ruff/black on touched files;
- artifact safety checks;
- project memory review;
- proof normal Today behavior is unchanged by no API/UI/Today service wiring.

Do not claim full regression pass unless full regression is actually green.
