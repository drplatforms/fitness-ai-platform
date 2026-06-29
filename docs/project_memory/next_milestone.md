# Next Milestone — Daily Coach Full User-Day Free-Range Payload Baseline v1

Recommended branch: `feature/daily-coach-full-user-day-free-range-payload-baseline-v1`.

Baseline: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Requested final status: `DAILY_COACH_FULL_USER_DAY_FREE_RANGE_PAYLOAD_BASELINE_V1_IMPLEMENTATION_COMPLETE`.

## Goal

Create a developer-only free-range Daily Coach provider trial that gives GPT-5.5 a broad neutral structured user-day packet instead of app/deterministic prose.

The milestone must answer:

```text
Can GPT-5.5 write a genuinely useful Daily Coach note when given the full useful user-day picture and no app-copy cage?
```

## Required implementation

- separate free-range service/tool path
- structured full user-day packet
- UserHealthState projection with included/omitted field coverage
- nutrition targets/actuals/deltas when available
- broader food candidate list with macro values when upstream data allows
- structured training and recovery facts
- minimal free-range prompt variants
- repeated-run support
- exact first-pass capture before post-hoc diagnostics
- opt-in provider payload debug artifacts
- token/cost telemetry
- pasteback report and QA-readable artifacts
- project memory updates

## Required artifacts

```text
provider_input_prompt.md                  # only with --write-provider-payload-debug
provider_payload_debug.json                # only with --write-provider-payload-debug
full_user_day_packet.json
full_user_day_packet_summary.md
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

## Boundaries

No production Today replacement, OpenAI default, provider promotion, public UI, Streamlit controls, final approval bypass, raw DB dumps, raw provider envelope persistence, secrets in artifacts, medical advice generation, meal planning changes, workout generation changes, nutrition target changes, recovery score changes, RAG, embeddings, multi-agent runtime, or stale-doc hygiene side quests.

## Known baseline drift

Continue documenting the existing `tests/test_daily_narrative_rich_day_service.py` copy-expectation drift. Do not patch it unless Architecture explicitly scopes that cleanup.

---

# Next Milestone — Daily Coach Wide Context Copy Cleanup + QA Readability v1

Owner: Backend Development with Architecture, QA, and Agent Engineering review.

Baseline: `main` at `42d0bd4 Merge daily coach wide context ceiling trial v1`.

Baseline snapshot: `fitness_ai_snapshot_2026-06-28_42d0bd4_main_merge-daily-coach-wide-context-ceiling-trial-v1.zip`.

Recommended branch: `feature/daily-coach-wide-context-copy-cleanup-qa-readability-v1`.

Goal: keep the wide-context ceiling-trial architecture, but improve user-facing first-pass copy language, prompt/context packaging, and terminal-friendly QA artifact readability.

Required outputs:

- prompt/context cleanup for backend-shaped user-facing wording;
- food choices represented as plain food language, not internal approval language;
- product-language diagnostic scan for QA readability;
- compact first-pass draft artifact;
- variant score summary artifact;
- best variant summary artifact;
- product language findings artifact;
- pasteback report artifact printable with `cat "$out/pasteback_report.md"`;
- optional CLI print flags for first pass, compact comparison, best variant, product issues, and pasteback report path;
- targeted tests for copy cleanup, scan behavior, artifact generation, and CLI flags;
- project memory updates.

Boundaries:

- no normal Today behavior changes;
- no Streamlit changes;
- no API route changes;
- no full report behavior changes;
- deterministic remains default;
- OpenAI remains opt-in/evaluation-only;
- no provider promotion;
- no raw provider envelope persistence;
- no secrets, raw DB rows, or public UI exposure;
- no parser relaxation;
- no Product Voice Audit rewrite;
- no meal planning, workout generation, nutrition target mutation, or recovery score mutation.

Known baseline drift to document, not patch here:

- `tests/test_daily_narrative_rich_day_service.py` copy-expectation mismatches on the supplied baseline lineage.
- Example: expected `Read the day before adding more`; actual `Consider the full day`.
- Full-suite green must not be claimed if this remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_COPY_CLEANUP_QA_READABILITY_V1_IMPLEMENTATION_COMPLETE`.
