# Current Project State

Last updated: 2026-06-21

## Project

AI Health Coach / fitness-ai

## Current source-of-truth branch

`main`

## Current active milestone

`Async Daily Coach Narrative Design v1`

Status: `DESIGN IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Purpose: document the future async Daily Coach Narrative architecture without implementing runtime provider execution. The design defines model lanes, async lifecycle, validation boundaries, invalidation rules, UI states, raw-output policy, persistence options, and phased implementation while preserving deterministic Today availability.
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
- Provider Narrative QA Matrix v2 runtime results
- Developer Delivery Workflow Contract v1
- Developer Delivery Workflow Script Safety Addendum v1
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1 results
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1 results
- Local Developer Command Menu Audit + Repo-Owned Commands v1

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



## Local Developer Command Menu Audit + Repo-Owned Commands v1 status

Local helper commands now live in `scripts/fitness_commands.ps1`, with optional profile installation through `scripts/install_fitness_commands_profile.ps1`.

The command menu is documented in `docs/project_memory/local_developer_command_menu.md`.

This milestone preserves existing commands including `fitness`, `app`, `lstop`, `lrestart`, and `lupdate`, adds workflow safety helpers including `fsnap`, `fbranch`, `fmerge`, `fsweep`, `fmem`, `fports`, `fkill`, `fdoctor`, `lpull`, `lvalidate`, and `lollama`, and keeps command logic out of hidden profile-only state.

Runtime truth encoded by the command menu:

- Windows source repo: `C:\projects\fitness_ai`
- Linux mirror repo: `~/projects/fitness-ai-platform`
- Windows Ollama: `http://127.0.0.1:11434`
- Linux-to-Windows Ollama: `OLLAMA_BASE_URL=http://192.168.1.104:11434`
- Windows Streamlit default: `http://127.0.0.1:8510`

This is docs/tooling/local command work only. It does not change provider, runtime, Streamlit app, FastAPI, schema, persistence, reports, Daily Next Action, nutrition, workout, catalog, or model eligibility behavior.

Hotfix status before acceptance: local smoke found Linux command-script issues in `lstatus`, `lpull`, and `lollama`. The command-menu hotfix updates safe Bash payloads, uses `git log -5 --oneline --decorate`, removes escaped `find` parentheses from `lstatus`, and uses `printf` so `lollama` does not print a literal `\n`.

## Developer Delivery Workflow Contract v1 status
## Developer Delivery Workflow Script Safety Addendum v1 status

Developer Delivery Workflow Script Safety Addendum v1 is a docs/tooling-only hardening milestone.

It adds `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md` and updates project-memory checks so future agents have an explicit rule for safe generated scripts.

The key rule is that merge scripts must run:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

If the accepted final feature commit is not an ancestor of `main`, scripts must stop before push, snapshot, or Linux pull.

This milestone exists because a clean working tree does not prove that the correct milestone was merged.


Developer Delivery Workflow Contract v1 is a docs/tooling-only milestone.

Primary doc:

`docs/project_memory/developer_delivery_workflow_contract.md`

Standing workflow rules:

- patch-first delivery is the default implementation path
- snapshot restore is fallback only
- commands start from `C:\projects\fitness_ai` unless stated otherwise
- branch/path verification is required before applying changes
- validation is required before commit
- staging is explicit
- snapshot creation follows the standard PowerShell command
- when Dustin provides a snapshot filename, Linux pull must be provided immediately
- Linux mirror path is `~/projects/fitness-ai-platform`
- Ollama runs on Windows by default
- Linux-to-Windows provider runtime uses `OLLAMA_BASE_URL=http://192.168.1.104:11434`

This contract does not change runtime behavior.

## Provider Narrative QA Matrix v2 status

The matrix tooling is available at `tools/provider_narrative_qa_matrix.py`.

The sanitized runtime matrix result doc is:

`docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md`

Runtime matrix results are recorded. `qwen2.5:3b` remains the recommended bridge baseline candidate. `qwen2.5:7b`, `qwen3:8b`, and `qwen3:14b` are approved probes only. `qwen3:32b` and `qwen3:30b-a3b` are not bridge-ready. No model is promoted.

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


### Daily Coach Same-Session Approved Preview Bridge v1 Retry
Status: accepted on `main` as the controlled manual bridge.
The bridge is limited to manual Developer Mode session approval. `qwen2.5:3b` is the only bridge baseline. Approved provider narrative may display in Today Coach Note only after explicit session approval and only for the active Streamlit session. No provider call occurs on normal Today load, no provider text is persisted, and no model is promoted.
### Same-Session Bridge Runtime QA v1
Current branch: `feature/same-session-bridge-runtime-qa-v1`

Status: `PASS / DOCS CLOSEOUT READY FOR ARCHITECTURE REVIEW`

Runtime QA result doc:

`docs/project_memory/runtime_qa/same_session_bridge_runtime_qa_v1_results.md`

Runtime QA recorded the accepted bridge as safe across the required manual QA conditions:

- QA 102 `qwen2.5:3b` happy path passed.
- Normal Today load remained deterministic.
- No provider call occurred on normal Today load.
- Developer Mode provider preview remained manual only.
- Explicit session approval worked.
- Approval remained session-only and did not persist.
- Non-bridge model approval was blocked.
- Fallback/rejected provider paths were blocked.
- Context/session boundaries were safe.
- No raw/rejected/provider/debug leakage appeared in normal UI.
- No DB/report/file persistence was observed.
- Diagnostics remained sanitized/readable.
- No PyArrow diagnostic rendering issue was observed.


### Daily Coach Narrative Product Voice Polish v1
Status: accepted as a narrow voice-polish milestone inside the manual same-session bridge.

This milestone improves approved Daily Coach provider narrative voice inside the existing manual same-session bridge. It refines prompt guidance and adds stricter product-voice validation so qwen2.5:3b approved copy is more coach-like, useful, concise, and grounded.

Implemented voice boundaries:

- `qwen2.5:3b` remains bridge baseline only.
- No qwen3 model is bridge-enabled.
- No model/provider default is promoted.
- Provider preview remains manual Developer Mode only.
- Normal Today load remains deterministic and must not call the provider.
- Approval remains explicit, manual, session-only, and non-persistent.
- Generic/template/meta copy is rejected or flagged.
- Unsupported claims remain blocked.
- Raw/rejected provider output and provider/model/debug internals remain hidden from normal UI.
- No DB/report/file/schema behavior changed.

### Daily Coach Narrative Product Voice Runtime QA v1
Current branch: `feature/daily-coach-narrative-product-voice-runtime-qa-v1`

Status: `PASS / DOCS CLOSEOUT READY FOR ARCHITECTURE REVIEW`

Runtime QA result doc:

`docs/project_memory/runtime_qa/daily_coach_narrative_product_voice_runtime_qa_v1_results.md`

Runtime QA passed for the accepted Daily Coach Narrative Product Voice Polish v1. The qwen2.5:3b approved runtime narrative is acceptable for the current manual same-session bridge baseline while all accepted safety boundaries remain intact.

Recorded runtime result:

- QA 102 qwen2.5:3b happy path passed.
- Provider was `direct_ollama`.
- Model was `qwen2.5:3b`.
- parse_success was true.
- validation_success was true.
- approved_narrative_returned was true.
- fallback_used was false.
- latency was approximately 22.5 seconds.
- approval was eligible and the approval button was visible.
- session approval worked.
- Today Coach Note updated after approval.
- normal Today UI remained free of provider/model/debug internals.
- no raw/rejected provider output was displayed.
- no persistence was observed.
- Developer Mode diagnostics remained sanitized/readable.
- no PyArrow diagnostic rendering issue was observed.

Voice quality: `PASS_WITH_NOTE`

The approved runtime narrative is acceptable for the current qwen2.5:3b manual bridge baseline, but it is not yet premium. The long-term product target remains: sound right and be right. Premium voice work remains a later milestone, likely involving qwen3 or premium async design after Architecture approval.

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
| daily coach same-session approval | Accepted manual Developer Mode, qwen2.5:3b-only, session-only bridge |
| workout planning | Deterministic generation with size preference and lifecycle cleanup |
| catalogs | Deterministic curated/imported canonical food and exercise foundations |

## Safe next sequence

1. Complete Daily Coach Narrative Product Voice Polish v1 local validation and manual QA.
2. Run Daily Coach Narrative Product Voice Runtime QA v1 across QA users/contexts before any broader provider design.
3. Keep Async Daily Coach Narrative Design v1 as a design-only future milestone unless Architecture explicitly authorizes implementation.
4. Keep Global Visual Theme Cleanup v1 parked as non-blocking UI polish.

## Non-negotiable constraints

- no model promotion without QA matrix and Architecture acceptance
- no widening same-session approval beyond the accepted manual Developer Mode qwen2.5:3b session-only bridge
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

## Async Daily Coach Narrative Design v1 status

Async Daily Coach Narrative Design v1 is implemented as a design-only milestone and ready for Architecture review.

Primary design doc:

`docs/project_memory/designs/async_daily_coach_narrative_design_v1.md`

The design defines the future async Daily Coach Narrative lifecycle, model lanes, state machine, validation gates, invalidation rules, raw output policy, UI display priority, persistence options, and phased implementation plan.

Current runtime behavior remains unchanged:

- normal Today load remains deterministic
- no provider call occurs on normal Today load
- Developer Mode provider preview remains manual
- explicit approval remains session-only
- `qwen2.5:3b` remains bridge baseline only
- qwen3 remains not bridge-enabled
- `qwen3:32b` is future premium async candidate only
- no model is promoted
- no DB schema change or provider cache is added
- deterministic fallback remains always available

<!-- START ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
## Async Daily Coach Narrative Implementation Plan v1

Status: Implemented for Architecture review
Date: 2026-06-21
Branch: feature/async-daily-coach-narrative-implementation-plan-v1

Architecture has documented the implementation plan for the future async Daily Coach Narrative system.

The plan keeps deterministic Today behavior as the always-available baseline and breaks future async work into phased milestones:

1. Async Contracts + Data Model
2. Async Service Shell / No Worker
3. Developer-Only Async Prototype
4. Validated Async Result Surface
5. Premium Model Research Lane
6. Product Eligibility Review

Current boundaries remain unchanged:

- no async runtime implemented
- no provider call on normal Today load
- no DB schema change
- no worker, queue, or scheduler
- no provider cache table
- no model promoted
- qwen2.5:3b remains bridge baseline only
- qwen3 remains not bridge-enabled
- qwen3:32b remains future premium async candidate only
- deterministic fallback remains always available
<!-- END ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->

<!-- START DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1 -->
## Daily Coach Async Contracts + Data Model v1 status

Current milestone: `Daily Coach Async Contracts + Data Model v1`

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

This milestone adds foundational backend contracts for future async Daily Coach Narrative jobs:

- `DailyCoachNarrativeJobStatus`
- `DailyCoachNarrativeModelLane`
- `DailyCoachNarrativeContextIdentity`
- `DailyCoachNarrativeJob`
- `ApprovedDailyCoachNarrativePayload`
- `SanitizedDailyCoachNarrativeDiagnostics`
- deterministic context hash helper

Boundary preserved:

- contracts/data-model foundation only
- no async runtime implemented
- no provider execution added
- no background worker added
- no queue added
- no scheduler added
- no DB schema change
- no `daily_coach_narrative_jobs` table created
- no provider cache table
- no provider call on normal Today load
- no UI display behavior changed
- no model promoted
- `qwen2.5:3b` remains bridge baseline only
- `qwen3` remains not bridge-enabled
- `qwen3:32b` remains future premium async candidate / research-only
- deterministic fallback remains always available
- raw/rejected output remains forbidden in normal UI
<!-- END DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1 -->
