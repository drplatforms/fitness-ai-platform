# Current State

Latest implementation milestone:
Daily Coach Async Approved Preview Bridge Implementation v1 — Feature Flag Disabled by Default

Current status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
DAILY_COACH_ASYNC_APPROVED_PREVIEW_BRIDGE_IMPLEMENTATION_V1_ACCEPTED

Accepted design foundation:
Daily Coach Async Approved Preview Bridge Design v1

Current behavior:

- approved preview bridge implementation exists behind disabled-by-default flag
- `DAILY_COACH_ASYNC_APPROVED_PREVIEW_ENABLED=false` by default
- normal Today unchanged when flag disabled
- Today preview reads only already-approved persisted async narratives
- preview appears only when all eligibility gates pass
- deterministic Daily Next Action remains primary
- preview is clearly secondary
- Developer Mode diagnostics remain gated and sanitized
- no provider call on Today render
- no provider call on page load
- no async job creation from Today
- no public/default async narrative display
- no worker / queue / scheduler / polling
- qwen3 remains not bridge-enabled
- qwen3:32b remains not promoted

Important docs:

- `docs/project_memory/designs/daily_coach_async_approved_preview_bridge_design_v1.md`
- `docs/project_memory/milestones/daily_coach_async_approved_preview_bridge_implementation_v1.md`
- `docs/project_memory/reviews/daily_coach_async_approved_preview_bridge_implementation_v1.md`
