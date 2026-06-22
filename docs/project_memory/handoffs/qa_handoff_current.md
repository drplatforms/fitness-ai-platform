## Current Implementation Update — Developer Mode Persistence Inspection v1

Status: `AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION`

Branch: `feature/developer-mode-persistence-inspection-v1`

Latest accepted milestone: `Daily Coach Async Persistence Service Shell v1`

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_SERVICE_SHELL_V1_ACCEPTED`

This milestone adds Developer Mode-only read-only inspection of persisted Daily Coach async job and approved narrative state. It may show sanitized persistence metadata and displayable/public_safe approved narrative content inside Developer Mode only. It must not add provider runtime, worker/queue/scheduler/polling, automatic async job creation, normal Today provider calls, public async narrative display, raw provider output display, rejected provider output display, full prompt/raw context/scratchpad display, or debug/provider metadata in normal UI.

Codex do not use by default.

## Current Implementation Update — Daily Coach Async Persistence Service Shell v1

Status: `AUTHORIZED FOR BACKEND IMPLEMENTATION`

Branch: `feature/daily-coach-async-persistence-service-shell-v1`

Latest accepted milestone: `Daily Coach Async Persistence Contracts + Schema v1`

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_CONTRACTS_SCHEMA_V1_ACCEPTED`

This milestone adds a bounded deterministic service/repository shell around the accepted `daily_coach_async_jobs` and `daily_coach_approved_narratives` schema. It is service/repository shell only: no provider runtime, no worker/queue/scheduler, no FastAPI behavior change, no Streamlit behavior change, no normal Today provider call, no public async narrative display, no raw provider output persistence, and no rejected provider output persistence.

Codex do not use by default.

# QA Handoff Current

Current milestone: Daily Coach Async Persistence Contracts + Schema v1

Status: IMPLEMENTED / READY FOR QA REVIEW

Branch: `feature/daily-coach-async-persistence-contracts-schema-v1`

Latest accepted milestone: Daily Coach Async Persistence Design v1

Latest accepted status: `DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED`

## QA focus

QA should review the schema/contracts diff and confirm boundary preservation.

PASS if:

- `daily_coach_async_jobs` exists
- `daily_coach_approved_narratives` exists
- `daily_coach_job_events` is deferred
- required columns exist
- `expired` is part of the job status contract and DB CHECK constraint
- stale/expired/displayable/public_safe fields exist
- context hash/version fields exist
- fallback and sanitized provider metadata fields exist
- forbidden raw/rejected provider output fields do not exist
- full prompt/raw context/scratchpad fields do not exist
- no provider runtime, API, Streamlit, worker, queue, scheduler, or polling behavior is added

FAIL if the branch implements or authorizes:

- provider runtime
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 calls or bridge
- qwen3:32b promotion
- worker / queue / scheduler / polling
- API route behavior changes
- Streamlit behavior changes
- normal Today provider calls
- public async narrative display
- raw provider output persistence
- rejected provider output persistence

## QA validation expectation

Automated validation should be focused on schema/contracts, project-memory checks, and boundary tests.

Manual runtime restart is not required unless product/runtime files changed unexpectedly.

---

## Daily Coach Async Provider Runtime Prototype v1

Status: AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION

Branch: `feature/daily-coach-async-provider-runtime-prototype-v1`

Developer Mode-only manual provider runtime prototype. Provider runtime is disabled by default, manual-trigger only, and must not run on normal Today render or page load. Approved public-safe narrative persistence is allowed only after strict JSON parse and safety validation. Failure paths may persist sanitized metadata only. No qwen3 bridge, qwen3 promotion, qwen3:32b promotion, worker, queue, scheduler, polling, public async narrative display, raw provider output persistence, rejected provider output persistence, full prompt/raw context/scratchpad persistence, or debug/provider metadata in normal UI. Codex do not use by default.
