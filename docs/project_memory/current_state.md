# Current State Update — Daily Coach Narrative Value-Aware Provider Comparison v1

Current source of truth: `main`.

Required source main commit: `e1f7bd3`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-26_e1f7bd3_nutrition-actuals-provenance-debug-integration-design-v1.zip`.

Previous accepted nutrition/debug milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

Current backend milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

Branch: `feature/daily-coach-narrative-provider-comparison-v1`.

Commit-check mode: code.

QA class: CLASS 2 / CLASS 5 HYBRID — opt-in provider-backed user-facing narrative candidate path with parser/validator/fallback boundaries.

Status: backend implementation complete / ready for Architecture review.

Requested final status: `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.

## Implemented provider-comparison path

Added the first value-aware Daily Coach narrative provider-comparison path over `DailyCoachSynthesis`:

- normal endpoint: `GET /daily-coach/{user_id}/narrative?date=YYYY-MM-DD`
- debug endpoint: `GET /daily-coach/{user_id}/narrative/debug?date=YYYY-MM-DD`

The normal endpoint returns approved narrative content only.

The debug endpoint returns the same approved content plus public-safe runtime metadata and provider-context summary for QA/developer inspection.

## Provider options

Supported configured providers:

- `deterministic` — default;
- `direct_ollama` — opt-in local/offline developer comparison provider;
- `openai` — opt-in hosted comparison provider.

Environment variables:

- `DAILY_COACH_NARRATIVE_PROVIDER`
- `DAILY_COACH_NARRATIVE_MODEL`
- `DAILY_COACH_NARRATIVE_DIRECT_OLLAMA_TIMEOUT_SECONDS`
- `DAILY_COACH_NARRATIVE_OPENAI_TIMEOUT_SECONDS`
- `OLLAMA_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` optional.

## Value-aware provider context

Provider candidates receive a compact backend-approved value context.

Allowed context may include:

- approved recovery readiness;
- approved fatigue risk;
- approved sleep/energy/soreness summary;
- approved nutrition actuals;
- approved macro target/gap status;
- approved food suggestion context;
- approved workout guidance;
- approved training/execution context;
- approved limitations/confidence.

Providers may quote values only when the values are present in the approved context.

## Backend approval boundary

The implemented pattern is:

`DailyCoachSynthesis -> value-aware provider context -> CandidateDailyCoachValueNarrative -> strict parser -> backend validator -> ApprovedDailyCoachValueNarrative -> deterministic renderer -> deterministic fallback if provider fails`

Provider output is never user-facing unless parser and validator approve it.

## Guardrails added

Provider candidates are rejected when they:

- use extra/missing schema keys;
- return markdown/code fences/prose wrappers;
- use invalid confidence;
- contradict `DailyCoachSynthesis.confidence`;
- say recovery is missing when recovery signal/context exists;
- say `without needing to address training or recovery`;
- say `no recovery notes` when recovery context exists;
- claim the user is under-eating without backend approval;
- quote calorie targets when calorie targets are not display-approved;
- prescribe exact food amounts without approved food suggestion context;
- expose raw/debug/provider/internal metadata;
- include forbidden causal/medical/training claims.

## Regression case protected

User/date parity case protected:

- user 102 / 2026-06-27;
- recovery state exists;
- recovery score 90;
- fatigue risk Low;
- readiness High;
- `DailyCoachSynthesis.recovery_signal` exists.

Provider narrative must not claim recovery is missing for this case.

## Scope boundaries

No nutrition actuals provenance debug endpoint behavior changed.

No Target-vs-Actual totals changed.

No nutrition logging behavior changed.

No workout/recommendation behavior changed.

No report behavior changed.

No Streamlit UI changed.

No provider is enabled by default.

No snapshots committed.

## Files updated

Runtime/model/service/test files:

- `models/daily_coach_value_narrative_models.py`
- `services/daily_coach_value_narrative_service.py`
- `services/daily_coach_narrative_validation_service.py`
- `api/routes/daily_coach.py`
- `tests/test_daily_coach_value_narrative_service.py`
- `tests/test_daily_coach_value_narrative_api.py`

Project-memory files:

- `docs/project_memory/current_state.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/project_continuity_bootstrap.md`
- `docs/project_memory/project_state.json`
- `docs/project_memory/handoffs/backend_handoff_current.md`
- `docs/project_memory/handoffs/architecture_handoff_current.md`
- `docs/project_memory/handoffs/qa_handoff_current.md`
- `docs/project_memory/milestones/daily_coach_narrative_value_aware_provider_comparison_v1.md`

## Architecture review step

Return to Architecture for review and acceptance decision.

Requested final status:

`DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED`.


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
