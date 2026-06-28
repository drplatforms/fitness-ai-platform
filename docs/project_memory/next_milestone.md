# Next Milestone — Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3 QA

Owner: QA / Regression Testing with Backend and Agent Engineering support.

Baseline: implementation branch `feature/daily-coach-provider-voice-context-freedom-rich-synthesis-v3`.

Recommended QA status: `DAILY_COACH_PROVIDER_VOICE_CONTEXT_FREEDOM_RICH_SYNTHESIS_V3_QA_PASS`.

## Goal

Validate that v3 makes provider Daily Coach copy materially more natural, specific, and useful while preserving deterministic default, opt-in providers, strict parser behavior, approved-value quote validation, and sanitized diagnostics.

## Primary case

- user_id: 102
- date: 2026-06-27
- provider: openai
- model: gpt-5.5

## Pass focus

- `approved_context_brief` is present and claim-backed;
- `claim_backing_map` guides natural phrasing without creating new authority;
- today_story uses structured coaching meaning instead of deterministic/report phrasing;
- rich context uses adaptive verbosity without filler or fact dumping;
- flagged phrases such as `main lever`, `effort anchor`, and `planned effort range` do not appear in approved output;
- every concrete value/status/food/amount is declared in `quoted_values_used`;
- normal artifacts remain sanitized and raw provider output remains local-only diagnostics.

---

# Next Milestone — Daily Coach Provider Context Selection & Coaching Synthesis v2 QA

Owner: QA / Regression Testing with Backend and Agent Engineering support.

Baseline: implementation branch `feature/daily-coach-context-selection-coaching-synthesis-v2`.

Recommended QA status: `DAILY_COACH_PROVIDER_CONTEXT_SELECTION_COACHING_SYNTHESIS_V2_QA_PASS`.

## Goal

Validate that v2 improves context selection, today_story usage, adaptive verbosity, priority-action specificity, and gpt-5.5 coaching usefulness while preserving deterministic default, opt-in providers, parser behavior, quote/value validation, and sanitized diagnostics.

## Primary case

- user_id: 102
- date: 2026-06-27
- provider: openai
- model: gpt-5.5

## Pass focus

- output uses 3-6 approved claims when context supports it;
- every concrete value/status/food/amount is declared in quoted_values_used;
- today_story improves specificity;
- priority_action is concrete;
- adaptive verbosity is useful and scannable, not generic or report-like;
- no raw provider output or secrets are committed.

---

# Next Milestone — Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

Owner: Backend Development with Agent Engineering guidance.

Baseline: `60fe77b Use OpenAI Responses API for Daily Coach narrative provider`.

Recommended branch: `feature/daily-coach-provider-copy-grounding-context-enrichment-v1`.

Requested implementation status: `DAILY_COACH_PROVIDER_COPY_GROUNDING_APPROVED_CONTEXT_ENRICHMENT_V1_IMPLEMENTATION_COMPLETE`.

## Goal

Make provider-generated Daily Coach copy more specific, coach-like, and useful by enriching backend-approved context packaging while preserving strict quote/value validation and deterministic fallback.

## Scope

- Add optional approved claim metadata.
- Add high-value/preferred claim packaging.
- Add claim usage rules and field role guidance.
- Update provider prompt framing for practical coach voice.
- Add diagnostic quality fields to the provider trial matrix.
- Update voice contract docs.

## Non-goals

- No provider default changes.
- No OpenAI promotion.
- No parser/validator/quote-value relaxation.
- No provider output persistence.
- No Streamlit provider controls.
- No nutrition/workout/recovery/report behavior changes.
- No RAG, Prompt Lab, embeddings, or multi-agent orchestration.

---

# Next Milestone — Daily Coach Provider Trial Diagnostics v1

Owner: Backend Development / Provider Runtime / Agent Engineering.

Source baseline: `main` at `a6cd8d0` plus Daily Coach Narrative Provider Trial Matrix v1 tooling at `4641c91`.

Recommended branch: `feature/daily-coach-provider-trial-diagnostics-v1`.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

## Goal

Improve Daily Coach provider trial diagnostics without changing product runtime behavior.

## Scope

- Add explicit local raw-provider-output diagnostic mode, off by default.
- Keep normal JSONL/Markdown artifacts sanitized.
- Add safe OpenAI key/config diagnostics without exposing secret values.
- Classify provider failures more clearly than generic failure where metadata allows.
- Add optional Ollama unload cleanup support for trial matrix runs.
- Record cleanup failures as warnings/safe metadata, not provider-quality failures.
- Preserve deterministic default and opt-in provider behavior.

## Non-goals

- No provider default changes.
- No Streamlit provider controls.
- No normal endpoint behavior changes.
- No parser/validator/quote-value relaxation.
- No provider narrative persistence.
- No nutrition/workout/recovery/report changes.
- No live provider calls in tests.
- No raw provider diagnostics or secrets committed.


---

# Next Milestone — Daily Coach Provider Human Voice & Food Action Specificity v4 QA

Owner: QA / Agent Engineering / Architecture.

Baseline implementation branch:
`feature/daily-coach-provider-human-voice-food-action-specificity-v4`

Primary QA objective:
Verify that v4 materially improves human voice, food action specificity, recovery phrasing, and priority action clarity without weakening backend truth validation.

Primary QA target:

- user_id: 102
- provider: openai
- model: gpt-5.5
- fallback_used should be false for valid provider output
- final_narrative_source should be openai_approved

Pass focus:

- uses friendly food labels instead of awkward canonical labels;
- avoids invented serving units;
- avoids repeatedly rejected phrases;
- food action is concrete but not meal planning;
- recovery phrasing is natural and safe;
- every concrete value/status/food/amount remains quote-backed;
- invalid candidates still fallback deterministically.
