# Current Project State

Last updated: 2026-06-20

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`main`

## Current active milestone

`Provider Narrative QA Matrix v2`

Status: `IMPLEMENTED / AWAITING_RUNTIME_MATRIX_RESULTS`

Purpose: characterize local model behavior through the stabilized manual Developer Mode Daily Coach provider-preview lane before any same-session approval retry.

North-star references remain preserved in repo memory:
- Technical future architecture ledger: `docs/project_memory/future_architecture_ledger.md`
- Premium product/backend blueprint: `docs/project_memory/premium_platform_blueprint.md`

## Latest accepted main baseline

The accepted main baseline before this provider-reliability branch includes:

- Supercharger / session-brief developer tooling
- Catalog Import Pipeline v1
- Catalog Source Evaluation v1
- Food Catalog Import Batch v1
- Exercise Catalog Import Batch v1
- Daily Next Action deterministic service
- Coach's Read / Daily Coach Synthesis
- Today Coach Note deterministic path
- Today UX Polish v1, with global theme cleanup still parked
- Workout Substitution UX v1
- Workout Exercise Count Preference v1
- Workout Daily State Lifecycle v1
- Daily Coach Developer Preview Stabilization v1
- Daily Coach Provider Preview Contract Reliability v1
- Project Memory Alignment + North Star Architecture v1
- Future Architecture Ledger
- Premium Platform Blueprint

The prior same-session approval bridge branch is not accepted and is reference-only.

Provider Narrative QA Matrix v2 is implemented on this branch as developer-only QA tooling and project memory. It characterizes model behavior through the existing manual Developer Mode provider-preview debug route and does not affect normal Today behavior.

## Definition of Done update

Project memory is now a first-class system component.

A feature branch or milestone is not done until the relevant project memory docs reflect:

- what changed
- what did not change
- what is accepted
- what remains parked
- what is explicitly not approved
- what future agents must not assume

Any meaningful commit that changes behavior, architecture boundaries, provider behavior, persistence, routing, UI, tests, accepted status, or project scope must update project memory in the same branch.

Memory drift is architecture drift.

## Provider Narrative QA Matrix v2 status

The matrix tooling is available at `tools/provider_narrative_qa_matrix.py`.

The sanitized runtime matrix result doc is:

`docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md`

Final acceptance requires runtime matrix results from the manual debug route. `qwen2.5:3b` should remain the bridge baseline candidate if it stays contract-approved. qwen3-family models remain probes only unless a future Architecture decision promotes a model after QA evidence.

## Current product surfaces

### Today

The Today flow contains distinct surfaces:

- Daily Next Action: deterministic backend decision and CTA.
- Today Coach Note: deterministic, short, user-facing note based on the Daily Next Action.
- Coach's Read / Daily Coach Synthesis: deterministic synthesis surface for broader daily context.
- Daily Grounded Recommendation: deterministic grounded recommendation panel.
- Developer Preview: Daily Coach Narrative: Developer Mode-only manual preview/debug lane.

These surfaces must not be collapsed into each other without Architecture approval.

Daily Coach Provider Preview Contract Reliability v1 adds deterministic normalization and diagnostics for manual provider previews only:

- clean valid JSON, markdown-fenced JSON, qwen `<think>...</think>` wrappers, and single embedded JSON objects can be parsed when otherwise safe
- ambiguous multi-object output fails safely
- validation failures return sanitized diagnostics without exposing rejected provider text
- `approved_narrative_returned` is true only when parse and validation both succeed
- normal Today page load remains deterministic and must not call the provider

Provider Narrative QA Matrix v2 adds developer-only matrix tooling for comparing local models. It does not promote any model and does not add provider output to normal Today UI.

### Workout

Accepted workout capabilities include:

- improved substitution UX
- Quick / Standard / Full workout size preference
- deterministic count resolution with safe maximum of 7
- daily workout state lifecycle
- stale prior-day selected/active/substituted state expiration or ignore behavior
- completed workout history preservation

### Nutrition and reports

Accepted report provider boundaries include:

- Training Report Section provider path remains opt-in/validated with deterministic fallback.
- Nutrition Report Section is Level 5 provider-integrated on approved opt-in provider output, with deterministic fallback and strict sanitizer boundaries.
- Full-report provider execution remains gated and background-safe where applicable.
- Provider metadata and persistence boundaries remain explicit.

## Current provider doctrine

- Deterministic paths remain the default.
- Backend owns facts, calculations, constraints, validation, persistence, and fallback.
- AI/provider output may explain or phrase backend-approved truth only.
- Validators decide what reaches user-facing display.
- Manual Developer Mode preview lanes are allowed only when scoped.
- No provider may run on normal Today page load unless explicitly approved later.
- `qwen3:8b`, `qwen3:14b`, `qwen3:30b-a3b`, and `qwen3:32b` are not production-promoted.
- `qwen3:32b` remains a future premium coach candidate only.
- No raw or rejected provider output may appear in normal UI.
- No provider narrative persistence is approved for Daily Coach.

## Current Daily Coach provider status

Accepted:

- Daily Coach Narrative Context Builder v1
- Daily Coach Narrative Offline Provider QA v1
- Daily Coach Narrative Provider Contract Tightening v1.1
- Daily Coach Narrative Developer Preview v1
- Daily Coach Narrative Today Developer Panel v1
- Daily Coach Developer Preview Stabilization v1

Not accepted:

- `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1`

Reference-only branch reason:

- attempted same-session approval before the developer-preview and provider-preview diagnostics were stable enough
- exposed Streamlit Developer Mode diagnostics fragility
- exposed provider preview contract reliability gaps
- not merged
- replaced by the stabilization then provider-contract-reliability sequence

## Current catalog status

The catalog foundation is accepted for the current phase:

- Catalog Import Pipeline v1: accepted deterministic staged import tooling.
- Catalog Source Evaluation v1: accepted approved small-batch source candidates.
- Food Catalog Import Batch v1: accepted first 20 reviewed USDA/FDC generic food rows.
- Exercise Catalog Import Batch v1: accepted first 18 manually curated home-equipment exercise rows.

No new catalog import, scraping, external API ingestion, or AI-generated catalog truth is approved unless a future milestone explicitly authorizes it.

## Current section maturity

| Area | Current accepted status |
|---|---|
| training report section | Provider-integrated, opt-in, validated, deterministic fallback protected |
| nutrition report section | Level 5 provider-integrated on approved opt-in provider output; deterministic fallback protected |
| nutrition target display | Backend-approved display contract, not provider-authored truth |
| daily next action | Deterministic decision service |
| today coach note | Deterministic normal Today UI card |
| coach's read / daily coach synthesis | Deterministic synthesis surface |
| daily coach narrative developer preview | Manual Developer Mode preview/debug only |
| daily coach same-session approval | Not accepted; reference-only failed branch |
| workout planning | Deterministic generation with size preference and lifecycle cleanup |
| catalogs | Deterministic curated/imported canonical food and exercise foundations |

## Safe next sequence

1. Complete Project Memory Alignment + North Star Architecture v1.
2. Resume or accept Daily Coach Provider Preview Contract Reliability v1 only after docs are aligned.
3. Retry Daily Coach Same-Session Approved Preview Bridge only after provider preview contract reliability is proven manually and by tests.
4. Keep Global Visual Theme Cleanup v1 parked as non-blocking UI polish.

## Non-negotiable constraints

- no model promotion without QA matrix and Architecture acceptance
- no same-session approval unless explicitly reauthorized after reliability work
- no Daily Coach narrative persistence yet
- no provider call on normal Today load
- no raw/rejected provider output in normal UI
- no schema/persistence/report changes without explicit milestone scope
- no RAG/vector/MoE/MCP/frontend rewrite implementation during docs alignment
- no Aider unless explicitly reapproved
- no Headroom reintroduction
- no Claude workflow
- no `CLAUDE.md`
- `qa_artifacts/` remains local-only and uncommitted
