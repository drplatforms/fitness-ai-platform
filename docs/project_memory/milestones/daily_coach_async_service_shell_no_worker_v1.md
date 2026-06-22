# Daily Coach Async Service Shell / No Worker v1 Milestone

Status: Implemented for Architecture review
Date: 2026-06-21
Branch: feature/daily-coach-async-service-shell-no-worker-v1

Daily Coach Async Service Shell / No Worker v1 adds an internal backend service shell for future async Daily Coach narrative jobs.

This milestone uses the accepted Daily Coach Async Contracts + Data Model v1 contracts and keeps normal Today behavior deterministic.

Implemented scope:

- `DailyCoachAsyncNarrativeService`
- `DailyCoachNarrativeJobRepositoryProtocol`
- `InMemoryDailyCoachNarrativeJobRepository`
- deterministic create/read/list/latest job behavior
- deterministic latest displayable job selection
- explicit status transition helper
- stale/context-valid helpers
- expiration/displayability helpers
- no-provider-execution service boundary tests
- no FastAPI route / no Streamlit display / no DB schema guard tests

Boundary preserved:

- service shell only
- no async runtime implemented
- no provider execution added
- no direct_ollama call added
- no CrewAI call added
- no background worker added
- no queue added
- no scheduler added
- no DB schema change
- no daily_coach_narrative_jobs table created
- no provider cache table
- no FastAPI route added
- no provider call on normal Today load
- no Streamlit async display behavior changed
- no model promoted
- qwen2.5:3b remains bridge baseline only
- qwen3 remains not bridge-enabled
- qwen3:32b remains future premium async candidate / research-only
- deterministic fallback remains always available
- validation boundary preserved
- raw/rejected output not approved for normal UI
- app/wapp Linux runtime hotfix remains intact
- Local Command Menu App Runtime Correction v1 remains intact
- `app` means Linux canonical app runtime
- wapp remains the explicit Windows-local escape hatch
- fports remains Windows-side port visibility only
- docs/project memory updated
- no qa_artifacts committed
- no snapshots committed
- workflow contract followed
- script safety addendum followed

Acceptance target:

`DAILY_COACH_ASYNC_SERVICE_SHELL_NO_WORKER_V1_ACCEPTED`
