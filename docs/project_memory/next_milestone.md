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
