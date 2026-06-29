# Next Milestone — Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

Source baseline: `feature/daily-coach-free-range-voice-precision-payload-enrichment-v2` at `d731a6c Enrich free range voice precision payload`.

Backend branch: `feature/daily-coach-free-range-output-completion-coach-surface-polish-data-seeding-v3`.

Requested status: `DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_COMPLETE`.

Architecture decision: continue the free-range coach experiment. Do not merge v2 yet, do not move to docs cleanup, do not onboard new Architecture continuation, and do not switch to a restrictive reviewer/renderer gate.

Required implementation:

- fix deterministic provider opt-in regression so deterministic runs never require `--allow-live-provider` while OpenAI/direct_ollama remain explicit opt-in
- add completion/truncation diagnostics with finish reason, output tokens, max output tokens, completion status, and local truncation heuristics
- increase developer-only output token budget for the free-range path
- add display-ready numeric values for calories, macros, weight change, volume load, RIR, recovery fields, and food values
- add compact macro display card artifacts
- add food option card artifacts
- add developer-only AI snack / mini-meal candidate artifacts from known candidate foods only
- add bounded practical food seed expansion for this free-range scenario/candidate builder
- add low-confidence/anomaly handling for suspicious weight trends without deleting raw debug evidence
- add workout/session naming visibility fields (`internal_workout_model`, `user_facing_session_name`, `session_type`, `session_intensity`, `session_name_source`)
- preserve exact first-pass drafts before diagnostics, repair, fallback, or phrase cleanup
- preserve provider payload debug, full user-day packet, model input manifest, precision/food/voice summaries, token/cost telemetry, and artifact safety
- update pasteback report with completion, cards, snacks, number formatting, weight trend handling, session naming, voice findings, claim risk, consistency, token/cost, artifact safety, and known baseline drift

Boundaries:

- developer-only experiment
- normal Today unchanged
- no production Today replacement
- no restrictive reviewer/renderer gate
- no OpenAI default or provider promotion
- no public UI or Streamlit controls
- no raw provider envelope persistence, secrets, or raw DB dumps
- no medical advice generation
- no meal planning/workout generation/nutrition target/recovery score changes
- no RAG, embeddings, multi-agent runtime, local/cheaper model comparison, Headroom/context compression, or full 450–500 food expansion

Known baseline drift remains documented and unpatched: `tests/test_daily_narrative_rich_day_service.py` expected `Read the day before adding more` vs actual `Consider the full day`.

---

# Next Milestone — Daily Coach Free-Range Voice + Precision + Payload Enrichment v2

Recommended branch: `feature/daily-coach-free-range-voice-precision-payload-enrichment-v2`.

Baseline: `feature/daily-coach-full-user-day-free-range-payload-baseline-v1` at `eb26c59 Add daily coach full user-day free-range trial`.

Baseline snapshot: `fitness_ai_FEATURE_snapshot_2026-06-29_eb26c59_feature-daily-coach-full-user-day-free-range-payload-baseline-v1_backend-baseline-for-free-range-v2.zip`.

Requested final status: `DAILY_COACH_FREE_RANGE_VOICE_PRECISION_PAYLOAD_ENRICHMENT_V2_IMPLEMENTATION_COMPLETE`.

## Goal

Continue the developer-only free-range coach path with voice variants, precision metadata, richer food candidate packet shape, workout/set-data visibility, recovery field coverage, and exact model-input inspection.

## Required implementation

- preserve full first-pass coach note without pre-audit mutation
- add strict, empathetic, and hypeman voice variants
- keep practical/direct/minimal variants available
- add food and macro precision metadata
- add quote-style guidance for direct values vs estimates
- expose 8-15 food candidates when upstream data allows
- report workout/set-level data availability honestly
- preserve broad recovery/readiness context
- keep post-hoc audit only
- write `model_input_manifest.md`, `voice_variant_summary.md`, `precision_usage_summary.md`, and `food_candidate_summary.md`
- update pasteback report with best voice, full best note, precision, food count, set-data availability, recovery fields, claim risk, consistency, token/cost, artifact safety, and baseline drift

## Boundaries

No production Today replacement, Today-card renderer/compressor, OpenAI default, provider promotion, public UI, Streamlit controls, final approval bypass, raw DB dumps, raw provider envelope persistence, secrets in artifacts, medical advice generation, meal planning changes, workout generation changes, nutrition target changes, recovery score changes, RAG, embeddings, multi-agent runtime, Headroom/context compression, local/cheaper model comparison, project memory handoff-compression/stale-doc hygiene, or full 450-500 food expansion.

## Known baseline drift

Continue documenting the existing `tests/test_daily_narrative_rich_day_service.py` copy-expectation drift. Do not patch it unless Architecture explicitly scopes that cleanup.

---

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
