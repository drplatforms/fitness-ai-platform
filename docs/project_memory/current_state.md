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
