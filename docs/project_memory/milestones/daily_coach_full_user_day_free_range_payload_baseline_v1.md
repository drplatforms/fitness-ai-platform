# Daily Coach Full User-Day Free-Range Payload Baseline v1

Status: Backend implementation patch prepared for local validation.

Baseline branch: `main`.

Baseline commit: `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Requested final status: `DAILY_COACH_FULL_USER_DAY_FREE_RANGE_PAYLOAD_BASELINE_V1_IMPLEMENTATION_COMPLETE`.

## Purpose

This milestone stops the phrase-cleanup loop and creates a developer-only free-range Daily Coach provider trial.

The product question is:

```text
Can GPT-5.5 write a genuinely useful Daily Coach note when given the full useful user-day picture and no app-copy cage?
```

The new path gives the provider a neutral structured user-day packet instead of app-generated Daily Coach prose, deterministic coach copy, phrase bans, fallback copy, or Product Voice Audit repair context.

## Implementation

Added a separate developer-only service and CLI:

```text
models/daily_coach_full_user_day_models.py
services/daily_coach_full_user_day_free_range_service.py
tools/dev_daily_coach_full_user_day_free_range_trial.py
```

The new path builds a `DailyCoachFullUserDayPacket` with structured projections of:

- user/profile context
- today context
- selected UserHealthState fields and explicit field coverage
- nutrition actuals, targets, statuses, and deltas
- broader food candidates with macro values
- structured training facts
- structured recovery/readiness facts
- deterministic calculations as facts
- concise do-not-infer safety boundaries

The provider receives one rendered prompt containing a JSON data packet.

The provider does not receive old Daily Coach copy, deterministic fallback copy, current narrow-path output, Product Voice Audit findings, phrase-ban lists, or raw provider envelopes.

## Prompt variants

Implemented variants:

```text
free_range_full_user_day_minimal
free_range_full_user_day_practical_coach
free_range_full_user_day_direct_coach
```

Repeated runs are supported with `--repeat` so QA can evaluate whether good output is repeatable.

## Provider payload debug artifact

This milestone adds explicit opt-in payload-debug artifacts:

```text
--write-provider-payload-debug
provider_input_prompt.md
provider_payload_debug.json
```

These artifacts include the exact prompt string sent to the provider, prompt character count, structured packet, food candidates, macro/training/recovery field lists, and prompt/packet diagnostic scans.

They do not include API keys, environment dumps, raw provider response envelopes, raw database rows, raw chain of thought, or unbounded private notes.

## Artifacts

The new tool writes:

```text
run_config.json
provider_input_prompt.md                  # only with --write-provider-payload-debug
provider_payload_debug.json                # only with --write-provider-payload-debug
full_user_day_packet.json
full_user_day_packet_summary.md
prompt_variants.md
first_pass_drafts.md
first_pass_drafts_compact.md
side_by_side_comparison.md
best_variant_summary.md
product_language_findings.md
claim_risk_summary.md
consistency_summary.md
token_cost_telemetry.md
token_cost_telemetry.csv
artifact_safety_summary.md
pasteback_report.md
```

`first_pass_drafts.md` preserves exact first-pass provider text. No repair, fallback, phrase cleanup, or product-language rewrite runs before first-pass capture.

## Boundaries

Preserved:

- normal Today behavior unchanged
- no Streamlit changes
- no API route changes
- no full report behavior changes
- deterministic remains default
- OpenAI remains opt-in/evaluation-only
- no provider promotion
- no production use of GPT-5.5
- no raw provider envelope persistence
- no secrets persisted
- no raw DB row artifacts
- no public UI exposure
- no parser relaxation
- no Product Voice Audit rewrite
- no new product approval gate
- no meal planning changes
- no workout generation changes
- no nutrition target changes
- no recovery score changes
- no RAG
- no embeddings
- no multi-agent runtime

## Known baseline drift

Known baseline drift remains intentionally unpatched:

```text
tests/test_daily_narrative_rich_day_service.py
expected: Read the day before adding more
actual: Consider the full day
```

Do not claim full-suite green if this drift remains.

## Validation focus

Targeted tests cover:

- exact provider input prompt debug artifact opt-in
- no secrets/raw provider envelope in debug artifacts
- macro targets/actuals/deltas in packet
- more than three food candidates when upstream data allows
- food macro values
- no `approved option` wording in food candidates/prompt
- no deterministic Daily Coach prose examples in the prompt
- no phrase-ban prompt scaffolding
- first-pass draft capture before audit/repair/fallback
- repeated-run support
- token/cost telemetry
- CLI behavior
- normal Today unchanged by isolation
- OpenAI opt-in/evaluation-only behavior

## End
