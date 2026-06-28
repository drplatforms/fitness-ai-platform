# Project Continuity Bootstrap — Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3

Current source of truth: `2cd7708 Add daily coach context selection coaching synthesis v2`.

Active milestone: `Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3`.

Architecture status: approved for Backend implementation.

## Current work

V3 keeps the strict provider safety fence from v1/v2 but changes the provider-facing context shape. The model gets a natural, claim-backed `approved_context_brief`, a `claim_backing_map`, cleaned today_story meaning, compact voice examples/anti-examples, and an explicit `verbosity_budget` so rich context can produce useful, grounded, scannable coaching instead of robotic report-like copy.

## Standing boundaries

Backend computes, validates, and approves facts. Provider output is candidate wording only. The backend parser, quote/value validator, approved narrative conversion, and deterministic fallback remain mandatory. Deterministic remains default. OpenAI and direct_ollama remain opt-in. Do not persist provider output, expose raw diagnostics publicly, add Streamlit provider controls, change nutrition/workout/recovery/report calculations, or add RAG/multi-agent/Prompt Lab work in this milestone.

---

# Project Continuity Bootstrap — Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

Current baseline: `60fe77b Use OpenAI Responses API for Daily Coach narrative provider`.

Active milestone: `Daily Coach Provider Copy Grounding & Approved Context Enrichment v1`.

Architecture status: approved for Backend implementation.

## Current work

Daily Coach provider runtime is now working through the OpenAI Responses API. The next bottleneck is copy/context quality.

This milestone enriches approved context packaging so providers can use 2-4 high-value backend-approved facts instead of writing generic or mechanical copy. It adds optional claim metadata, high-value/preferred claim lists, field-role guidance, prompt framing, and trial-matrix copy-quality diagnostics.

## Standing boundaries

Backend computes, validates, and approves facts. Provider output is candidate wording only. The backend parser, quote/value validator, approved narrative conversion, and deterministic fallback remain mandatory. Deterministic remains default. OpenAI and direct_ollama remain opt-in. Do not persist provider output, expose raw diagnostics publicly, add Streamlit provider controls, change nutrition/workout/recovery/report calculations, or add RAG/multi-agent/Prompt Lab work in this milestone.

# Project Continuity Bootstrap — Daily Coach Provider Trial Diagnostics v1

Current source of truth: `main` at `a6cd8d0` plus Daily Coach Narrative Provider Trial Matrix v1 tooling at `4641c91`.

Active milestone: `Daily Coach Provider Trial Diagnostics v1`.

Architecture status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_APPROVED_FOR_BACKEND`.

## Current work

Add diagnostics to `tools/run_daily_coach_provider_trial_matrix.py` so provider failures can be understood without changing product behavior.

Implemented/targeted diagnostics:

- explicit local raw-provider-output diagnostic mode;
- normal artifact sanitization remains default;
- safe OpenAI config/key presence metadata;
- provider error type classification;
- optional Ollama unload cleanup metadata;
- tests proving no live OpenAI/Ollama calls are required.

## Standing boundaries

Do not make OpenAI or direct_ollama default. Do not change normal Daily Coach endpoints. Do not relax parser/validator/quote-value safety. Do not commit raw provider outputs or secrets. Do not add Streamlit controls, persistence, RAG, multi-agent orchestration, nutrition/workout/recovery/report behavior changes, or schema changes.

---

## Continuity update — Daily Coach Provider Context Selection & Coaching Synthesis v2

V2 adds backend-derived today_story, expanded high-value claim selection, field-specific claim budgets, adaptive verbosity guidance, and trial-matrix v2 diagnostics. Deterministic remains default, OpenAI/direct_ollama remain opt-in, quote/value validation remains mandatory, and raw provider output remains local-only diagnostics.
