# Next Milestone — Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

Owner: Backend Development with Architecture, QA, and Agent Engineering review.

Baseline: `main` at `718c614 Merge daily coach product voice audit gate fix v1`.

Recommended branch: `feature/daily-coach-wide-context-uncaged-gpt55-ceiling-trial-v1`.

Goal: implement a developer-only ceiling trial that tests whether GPT-5.5 can produce genuinely better Daily Coach copy when given a richer backend-approved context packet and fewer pre-draft writing shackles.

Required outputs:

- wide approved context packet builder;
- minimal writer prompt variants;
- exact first-pass GPT-5.5 draft capture;
- side-by-side comparison against deterministic and current narrow path;
- sanitized artifacts;
- token/cost telemetry fields where available;
- QA-friendly review summary and scoring template;
- baseline drift documentation;
- targeted tests for the new tool/service;
- proof normal Today behavior is unchanged.

Required prompt variants:

- `current_narrow_path`
- `wide_context_minimal_prompt`
- `wide_context_practical_coach`
- `wide_context_direct_coach`

Optional variant:

- `wide_context_no_style_guidance`

Provider configuration must support:

- `--provider openai --model gpt-5.5`
- future model swaps such as `gpt-5.4`, `gpt-5.4-mini`, and local Ollama models

Boundaries:

- no normal Today behavior changes;
- no provider promotion;
- no production UI;
- no raw provider envelope persistence;
- no raw DB rows;
- no secrets;
- no broad phrase-cage rebuild;
- no unrelated rich-day copy cleanup.

Known baseline drift to document, not patch here:

- `tests/test_daily_narrative_rich_day_service.py` copy-expectation mismatches on the supplied 718c614 snapshot.
- Example: expected `Read the day before adding more`; actual `Consider the full day`.
- Full-suite green must not be claimed if this remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_UNCAGED_GPT55_CEILING_TRIAL_V1_IMPLEMENTATION_COMPLETE`.
