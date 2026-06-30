# Current State — Daily Coach Fully Free Source-Data Lab v1

Current source of truth: `main` at `56d63c4 Merge daily coach free-range decaging diagnostic baseline v4`.

Active backend milestone: `Daily Coach Fully Free Source-Data Lab v1`.

Status: Architecture merged and snapshotted the free-range decaging v4 diagnostic baseline, then routed Backend to build a separate developer-only source-data lab from `main`, not from the unmerged feature chain.

Purpose: test whether GPT-5.5 can produce a meaningfully better Daily Coach note when it receives clean, organized source data and almost no coaching cage. This is a single-model lab, not multi-agent orchestration, RAG, embeddings, vector search, production provider enablement, or normal Today replacement.

Implementation direction: add a separate developer-only lab tool, build `fully_free_source_data_packet` artifacts, use a minimal prompt, support fully free prompt variants, capture exact first-pass drafts, and add post-hoc audits for source-data completeness, model freedom, backend-prose contamination, completion diagnostics, claim risk, artifact safety, and token/cost telemetry.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

Current source of truth: `feature/daily-coach-free-range-voice-precision-payload-enrichment-v2` at `d731a6c Enrich free range voice precision payload`.

Active backend milestone: `Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3`.

Status: Architecture classified v2 as a promising partial with product signal, but found truncation, raw-number formatting leaks, thin food context, and one targeted regression. Backend is continuing the developer-only free-range experiment from the unmerged v2 feature branch, not `main`.

Purpose: improve output completion, display-ready numeric surfaces, macro/food card artifacts, AI snack candidates, bounded food seeding, weight-anomaly handling, workout/session naming visibility, and voice-style diagnostics while preserving the full first-pass coach note.

Implementation direction: keep first-pass drafts exact and unmodified; keep diagnostics post-hoc only; fix deterministic provider live-opt-in regression; add completion diagnostics; expand practical food candidates; add food option/macro display cards, AI snack candidates, number-formatting and voice-style summaries; preserve provider-input debug and model-input manifest artifacts.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Free-Range Voice + Precision + Payload Enrichment v2

Current source of truth: `feature/daily-coach-full-user-day-free-range-payload-baseline-v1` at `eb26c59 Add daily coach full user-day free-range trial`.

Active backend milestone: `Daily Coach Free-Range Voice + Precision + Payload Enrichment v2`.

Status: Architecture accepted the v1 free-range thesis as materially better but requested one more developer-only iteration before merge/product-renderer work. Backend is enriching the free-range path with voice variants, precision metadata, broader inspectable food context, set-level data availability reporting, and stronger model-input manifest artifacts.

Purpose: determine whether GPT-5.5 continues improving when it receives a broad neutral full user-day packet with clearer precision/quote metadata, more useful food candidate structure, multiple coach voices, and exact provider-input inspection.

Implementation direction: keep the full coach note intact, preserve exact first-pass draft capture, add strict/empathetic/hypeman coach variants, expose food/macro precision and quote style, make model input inspectable through `model_input_manifest.md`, summarize food candidates and precision, and keep all audits post-hoc only.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_VOICE_PRECISION_PAYLOAD_ENRICHMENT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Full User-Day Free-Range Payload Baseline v1

Current source of truth: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Active backend milestone: `Daily Coach Full User-Day Free-Range Payload Baseline v1`.

Status: Architecture stopped the phrase-cleanup loop after provider payload forensics showed GPT-5.5 still received app/deterministic prose through the rendered prompt. Backend is implementing a developer-only free-range payload baseline from the last accepted main snapshot, not from the failed v2 branch.

Purpose: answer whether GPT-5.5 can write a genuinely useful Daily Coach note when given a broad neutral structured user-day packet instead of app-generated coach prose, deterministic fallback copy, phrase bans, repair context, or Product Voice Audit scaffolding.

Implementation direction: build a `DailyCoachFullUserDayPacket`, render it as provider-visible data, support minimal/practical/direct free-range prompt variants, support repeated runs, capture exact first-pass drafts before any post-hoc diagnostics, and add opt-in provider payload debug artifacts (`provider_input_prompt.md` and `provider_payload_debug.json`).

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULL_USER_DAY_FREE_RANGE_PAYLOAD_BASELINE_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Wide Context Copy Cleanup + QA Readability v1

Current source of truth: `main` at `42d0bd4 Merge daily coach wide context ceiling trial v1`.

Active backend milestone: `Daily Coach Wide Context Copy Cleanup + QA Readability v1`.

Status: Backend implementation patch is ready for local validation after Architecture routed the merged wide-context ceiling-trial baseline back for a narrow copy/readability patch. Live QA classified the prior result as `CONTEXT_HELPED_BUT_NOT_ENOUGH`.

Purpose: keep the wide-context ceiling-trial architecture, but clean backend-shaped wording from prompt/context packaging and make QA artifacts easier to inspect from the terminal. This remains developer-only. It is not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit/fallback-gate milestone.

Implementation direction: preserve backend truth and safety boundaries while making writer-facing context more human-facing; avoid wording such as `Nutrition is lagging`, `approved option`, `gap is still open`, and `planned workout as written`; add terminal-friendly compact artifacts, product-language findings, best-variant summary, and pasteback report support.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614/42d0bd4 lineage, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated milestones unless directly scoped.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_COPY_CLEANUP_QA_READABILITY_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

Current source of truth: `main` at `718c614 Merge daily coach product voice audit gate fix v1`.

Active backend milestone: `Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1`.

Status: Architecture accepted Backend Continuation Onboarding and directed Backend to proceed with the ceiling trial. Backend implementation is complete and ready for Architecture / QA review.

Purpose: answer whether GPT-5.5 can write genuinely better Daily Coach copy when given richer backend-approved context and fewer pre-draft writing shackles. This is a developer-only ceiling trial, not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit phrase patch.

Implementation direction: wide context packet builder, minimal writer prompt variants, exact first-pass draft capture, side-by-side comparison against deterministic and current narrow path, token/cost telemetry fields, sanitized artifacts, QA scoring template, and baseline drift documentation.

Known baseline drift documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614 snapshot, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside the ceiling trial unless it directly blocks targeted validation. Full-suite green must not be claimed if this drift remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_UNCAGED_GPT55_CEILING_TRIAL_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1

Current source of truth: `feature/daily-coach-natural-draft-product-voice-audit-v2` at `9ba9579 Add daily coach natural draft product voice audit v2`.

Active backend patch: `Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1`.

Status: Architecture routed v2 back to Backend for a focused approval-gate and audit-calibration patch.

QA found v2 architecture is useful as a diagnostic system, but final approval was wrong: failed fallback could still become final approved copy, Product Voice Audit was too lenient, food-action language was incomplete, and repair gave up too early when first-pass copy only needed light wording cleanup.

Patch direction: keep the writer loose, sharpen the reviewer, prefer light product-voice repair over fallback when factual claims are safe, and block final approval when fallback itself fails Product Voice Audit.

Required status: `DAILY_COACH_PRODUCT_VOICE_AUDIT_CALIBRATION_FINAL_APPROVAL_GATE_FIX_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Natural Draft + Product Voice Audit v2

Current source of truth: `main` at `4104796 Merge daily coach natural draft claim audit v1`.

Active backend milestone: `Daily Coach Natural Draft + Product Voice Audit v2`.

Status: Architecture approved for Backend implementation.

Natural Draft + Claim Audit v1 is merged as developer infrastructure but QA found it was only a technical partial: the factual reviewer existed, but product-quality review did not. V2 extends that path with first-pass model draft visibility, Product Voice Audit, food-action language checks, side-by-side comparison, repair delta reporting, humanized fallback, final approval gates, and reviewer conclusions.

Core principle: loosen the writer, tighten the reviewer, expose the first draft, and compare honestly. Deterministic fallback is the floor, not the goal.

V2 remains developer-only. Normal Today behavior is unchanged. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Backend remains final authority for facts, claim audit, product voice audit, repair limits, fallback, and final approval.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Natural Draft + Claim Audit v1

Current source of truth: `main` at `b9b46c9 Merge daily coach prompt lab voice lab v1`.

Active backend milestone: `Daily Coach Natural Draft + Claim Audit v1`.

Status: Architecture approved for Backend implementation.

Prompt Lab / Voice Lab v1 is merged as technical developer tooling, but product strategy has pivoted to Natural Draft + Claim Audit. The active architecture is: backend-approved coach brief → natural coach draft → deterministic claim extraction → backend claim audit → one targeted repair attempt → final approved copy or deterministic fallback.

Core principle: loosen the writer, tighten the reviewer. GPT-5.5 may draft naturally from a clean `ApprovedCoachBrief`, but Backend remains final authority for facts, interpretations, claim audit, repair limits, fallback, and final approval.

Boundaries remain unchanged: developer-only path; normal Today behavior unchanged; deterministic remains default; OpenAI/direct_ollama remain explicit opt-in/evaluation-only; no provider promotion; no public UI; no provider output persistence; no parser/validation/fallback relaxation; no raw DB access for provider; no RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, or queue changes.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_CLAIM_AUDIT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Prompt Lab / Voice Lab v1

Current source of truth: `main` at `2835d09 Merge daily coach plainspoken voice action clarity v5`.

Active backend milestone: `Daily Coach Provider Prompt Lab / Voice Lab v1`.

Status: Architecture approved for Backend implementation.

V5 technically passed infrastructure but failed product voice. The current milestone is developer-only Prompt Lab / Voice Lab tooling, not another one-off phrase-hardening patch.

The lab compares fixed scenario cases and prompt/context variants through the existing Daily Coach provider path, parser, validator, fallback boundary, sanitized artifacts, and manual scoring template.

Deterministic remains default. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Normal Today behavior, product persistence, Streamlit provider controls, parser rules, quote/value validation, and fallback behavior remain unchanged.

Requested final status: `DAILY_COACH_PROVIDER_PROMPT_LAB_VOICE_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Plainspoken Voice & Action Clarity v5

Current source of truth: `feature/daily-coach-provider-human-voice-food-action-specificity-v4` at `0ace3da`.

Active backend milestone: `Daily Coach Provider Plainspoken Voice & Action Clarity v5`.

Architecture status: approved for Backend implementation after the green v4 baseline snapshot.

Status: backend implementation patch ready for local validation.

V5 replaces phrase-ban-only tuning with a plainspoken coaching contract. The Daily Coach should say the actual action, use friendly food labels, explain the food reason, connect recovery to training behavior, and keep the priority action concrete without motivational packaging or backend/framework language.

Implemented direction:

- plainspoken voice contract and rejected phrase registry;
- `food_action_context` with friendly food options, macro reason, and backed food-action sentence patterns;
- prompt rewrite around plain examples and anti-examples;
- stronger visible-output validation for user-rejected phrases, canonical food leakage, unbacked food action, invented timing, invented pairings, and invented serving labels;
- trial-matrix v5 diagnostics for plainspoken phrase flags, food-gap reason use, food condition use, slogan-like phrases, and manual product voice scoring.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_PLAINSPOKEN_VOICE_ACTION_CLARITY_V5_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3

Current source of truth: `feature/daily-coach-context-selection-coaching-synthesis-v2` at `2cd7708`.

Active backend milestone: `Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3`.

Architecture status: approved for Backend implementation.

Status: backend implementation patch ready for local validation.

V3 addresses product-copy quality after v2 technical pass by giving providers a more natural, human-readable, claim-backed context starter while preserving strict backend truth boundaries. The implementation adds `approved_context_brief`, `claim_backing_map`, cleaned today_story phrasing, natural voice examples/anti-examples, explicit `verbosity_budget`, hard/diagnostic phrase checks, and v3 trial-matrix diagnostics.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_VOICE_CONTEXT_FREEDOM_RICH_SYNTHESIS_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Context Selection & Coaching Synthesis v2

Current source of truth: accepted copy-grounding branch baseline at `2bbffdb`.

Active backend milestone: `Daily Coach Provider Context Selection & Coaching Synthesis v2`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone improves provider context selection and coaching synthesis by adding deterministic `today_story`, expanded high-value claim selection, field-specific claim budgets, adaptive verbosity guidance, prompt synthesis framing, and v2 trial-matrix diagnostics.

Adaptive verbosity rule: the target is useful, grounded, scannable coaching, not maximum brevity. More words are allowed only when approved context is rich and the extra words improve actionability, connect multiple domains, or explain food/training/recovery context clearly. Shorter copy is required when context is sparse, generic, report-like, repetitive, or unsupported.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_CONTEXT_SELECTION_COACHING_SYNTHESIS_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

Current source of truth: `main` / accepted runtime-fix baseline at `60fe77b`.

Active backend milestone: `Daily Coach Provider Copy Grounding & Approved Context Enrichment v1`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone enriches provider-approved context packaging and prompt guidance so OpenAI can write more specific Daily Coach copy without weakening the existing parser, quote/value validator, fallback path, or deterministic default.

Implemented direction:

- approved value claim metadata: `priority`, `section_hint`, `coaching_use`, `display_hint`, `value_style`;
- provider context packaging: `provider_task_context`, `high_value_claims`, `preferred_claims_by_field`, `claim_usage_rules`, `field_role_guidance`;
- prompt/field-role guidance for practical coach copy using 2-4 high-value claims;
- trial-matrix copy-quality diagnostics and manual review placeholders.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_COPY_GROUNDING_APPROVED_CONTEXT_ENRICHMENT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Trial Diagnostics v1

Current source of truth: `main` at `a6cd8d0` plus accepted Daily Coach Narrative Provider Trial Matrix tooling at `4641c91`.

Active backend milestone: `Daily Coach Provider Trial Diagnostics v1`.

Status: Architecture approved for Backend implementation.

Diagnostics v1 improves the provider trial matrix only. It adds explicit local raw-provider-output diagnostics, safer OpenAI configuration/error classification, safe provider config metadata, optional Ollama unload cleanup, and artifact-safety guardrails.

Deterministic remains default. `direct_ollama` and `openai` remain opt-in. No product runtime, Streamlit, persistence, parser, validator, quote/value, nutrition, workout, recovery, or report behavior changes are authorized.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

---

# Current State Update — Daily Coach Narrative Provider Trial Matrix v1

Current source of truth: `main`.

Required source main commit: `a6cd8d0`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_a6cd8d0_daily-coach-narrative-approved-value-quote-validation-v1.zip`.

Previous accepted statuses:

- `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED_AND_MERGED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_QA_V1_PASS`

Current backend milestone: Daily Coach Narrative Provider Trial Matrix v1.

Branch: `feature/daily-coach-narrative-provider-trial-matrix-v1`.

Commit-check mode: code.

QA class: CLASS 2 / CLASS 5 HYBRID.

Status: backend implementation in progress.

Requested final status: `DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.

## Goal

Add repeatable provider trial matrix tooling for Daily Coach value-aware narratives.

The tool compares the same approved Daily Coach contexts across:

- deterministic;
- direct_ollama;
- openai.

The matrix records schema adherence, parse/validation/fallback behavior, quote/value discipline, latency, approved narrative output, rendered narrative output, and manual-review placeholders without changing runtime defaults.

## Implemented direction

Provider evaluation must run through the accepted Daily Coach value-aware narrative path and approved value quote validation path.

Live providers are skipped unless explicitly enabled with `--allow-live-providers`.

Generated artifacts must not include raw provider output or secrets.

The normal app/runtime behavior remains unchanged.

## Scope boundaries

Deterministic remains default.

`direct_ollama` remains opt-in offline/developer mode.

`openai` remains opt-in hosted comparison provider.

No provider default change is authorized.

No live provider calls are allowed in automated tests.

No Streamlit provider controls are added.

No provider narratives are persisted.

No parser, validator, quote/value, nutrition, workout, recovery, report, schema, or persistence behavior is changed.

No snapshots are committed.

## Architecture review step

Return to Architecture after implementation and validation.

Requested final status:

`DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.


## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- Provider Narrative QA Matrix v2
- Daily Coach Async Service Shell / No Worker v1
- Daily Coach Async Provider Runtime Design v1
- qwen3:32b research / future premium async candidate only
- deterministic fallback remains mandatory
- Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries
- AI explains backend-approved truth
- no provider on normal Today page load unless explicitly configured

## Historical continuity anchors — additional reference-only preservation

These phrases are preserved to avoid losing accepted historical continuity context:

- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- No provider may run on normal Today page load
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- service shell only
- no provider execution added


---

# Current Implementation Update — Daily Coach Provider Human Voice & Food Action Specificity v4

Status: Backend v4 patch candidate built from v3 baseline `e23a435`.

This milestone addresses the v3 product-copy failure after technical validation passed. It improves provider-facing human voice and food action specificity while preserving strict backend truth boundaries.

Implemented direction:

- friendly food labels are generated for provider/user-facing copy;
- canonical food labels remain traceability/debug context;
- serving display remains conservative and backend-approved only;
- nutrition_action_context explains the approved food action without letting the model invent meal plans;
- claim_backing_map separates internal meaning from user-facing phrase examples;
- approved_context_brief and today_story avoid known awkward framework phrases;
- prompt examples now directly ban the phrases rejected in QA/user critique;
- validation catches canonical food label leakage, unquoted friendly foods, invented serving wording, and repeatedly rejected phrases;
- trial matrix diagnostics include v4 food/voice fields.

Boundaries preserved:

- deterministic default unchanged;
- OpenAI/direct_ollama opt-in only;
- parser and quote/value validation remain strict;
- no provider persistence;
- no Streamlit changes;
- no nutrition target, workout, recovery, or report architecture changes.


---

# Current Implementation Update — Daily Coach Free-Range Prompt + Payload Decaging v4

Status: Backend v4 patch candidate built from v3 baseline `c36c50a`.

This milestone continues the unmerged free-range Daily Coach experiment and addresses the v3 finding that the coach output was still too backend-bound. The implementation splits internal/debug payloads from the model-facing coach-facts surface, decages the provider prompt when explicitly requested, and adds direct/hypeman-clean variants while preserving exact first-pass output and post-hoc-only diagnostics.

Implemented direction:

- deterministic provider remains runnable without `--allow-live-provider` while OpenAI/direct_ollama remain explicit opt-in;
- debug payloads may retain backend/internal fields, but `model_facing_coach_facts.md/json` exposes cleaner coaching source material;
- `--prefer-decaged-prompt` uses `MODEL_FACING_COACH_FACTS_JSON` instead of the full backend-shaped packet;
- the decaged prompt tells GPT-5.5 not to echo field labels/internal categories and to use editorial judgment;
- the prompt specifically discourages main-note numeric overload, panic-level macro deficit framing, Markdown bold, emoji headers, decorative Markdown, and repeated `roughly` wording;
- direct/hypeman-oriented clean variants were added for the v4 voice matrix;
- completion diagnostics now report expected/captured/complete/truncated/skipped counts;
- food/snack formatting aggregates mini-meal macros before display;
- new artifacts include model-facing coach facts, decaging summary, and backend label exposure summary;
- provider payload debug includes both debug packet and model-facing facts so Architecture/QA can inspect the split.

Boundaries preserved:

- developer-only experiment;
- normal Today unchanged;
- no production Today replacement;
- no restrictive renderer/reviewer gate;
- no OpenAI default or provider promotion;
- no public UI or Streamlit controls;
- no raw provider envelope persistence, secrets, or raw DB dumps;
- no medical advice generation;
- no meal planning, workout generation, nutrition target, recovery score, RAG, embeddings, multi-agent runtime, Headroom/context compression, local/cheaper model comparison, or full 450–500 food expansion.
