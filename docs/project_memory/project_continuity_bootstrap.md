# Project Continuity Bootstrap — Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1

Current source of truth: `23b5378 Merge daily coach fully free source-data lab evidence v1`.

Active milestone: `Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1`.

Architecture status: approved for Backend implementation as docs-only repo patch.

## Current work

Move repo docs from stale Fully Free Source-Data Lab implementation state to the accepted `23b5378` evidence state. Record provider voice iteration pause, canonical seven team lanes, and Backend Intelligence Foundation as the next center of gravity.

## Standing boundaries

Docs/process/development architecture only. No runtime behavior changes, provider changes, UI changes, schema/migration changes, RAG, embeddings, vector search, multi-agent runtime, custom GPT build, or provider prompt experiment.

---

# Project Continuity Bootstrap — Daily Coach Provider Plainspoken Voice & Action Clarity v5

Current source of truth: `0ace3da Add daily coach provider human voice food action specificity v4`.

Active milestone: `Daily Coach Provider Plainspoken Voice & Action Clarity v5`.

Architecture status: approved for Backend implementation.

## Current work

V5 is the final manual voice-correction milestone before Prompt Lab / Voice Lab should become active. The goal is not more factual freedom. The goal is bounded provider freedom: plainspoken synthesis from backend-approved facts, friendly food labels, backed macro-gap context, direct training instructions, clear recovery implication, strict quote/value validation, and deterministic fallback.

Backend adds a plainspoken voice contract, rejected phrase registry, `food_action_context`, stronger prompt examples, validation for rejected phrases and unbacked food actions, and v5 trial-matrix diagnostics.

## Standing boundaries

Backend computes, validates, and approves facts. Provider output is candidate wording only. The backend parser, quote/value validator, approved narrative conversion, and deterministic fallback remain mandatory. Deterministic remains default. OpenAI and direct_ollama remain opt-in. Do not persist provider output, expose raw diagnostics publicly, add Streamlit provider controls, change nutrition/workout/recovery/report calculations, or add RAG/multi-agent/Prompt Lab work in this milestone.

## Patch safety note

Do not use broad variable-removal scripts for reused local variables such as `nutrition` or `recovery`; scope edits by function/block anchors.

---

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


---

# Continuity Note — Daily Coach Provider Human Voice & Food Action Specificity v4

Use v3 commit `e23a435` as the v4 baseline. v4 is not a provider authority expansion. It is a provider-materials and validation hardening milestone focused on human voice, friendly food labels, serving-display safety, nutrition action context, and banned awkward phrases.

Important patch lesson: do not use broad variable-removal scripts for reused local variables like `nutrition` or `recovery`; scope edits by function/block anchors.
