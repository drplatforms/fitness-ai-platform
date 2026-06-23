# Next Milestone

Current authorized milestone:
Weekly Coach Summary Async Service Shell / No Worker v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
WEEKLY_COACH_SUMMARY_ASYNC_SERVICE_SHELL_NO_WORKER_V1_ACCEPTED

Purpose:
Add deterministic backend service shell functions around the accepted Weekly Coach Summary contracts without persistence, provider runtime, worker, queue, scheduler, polling, API, or Streamlit UI.

Recommended next milestone after acceptance:
Weekly Coach Summary Async Persistence Design v1

Alternative next milestone:
Weekly Coach Summary Developer Mode Inspection v1

Why:
The deterministic preview output is now useful. The next durable architecture step should define safe persistence before UI exposure, unless Architecture decides the app needs Developer Mode inspection first.

Still not authorized:

- Weekly Coach Summary persistence schema/service
- Weekly Coach Summary provider runtime
- normal Today provider execution
- provider execution on page load
- automatic async job generation
- worker / queue / scheduler / polling
- public/default weekly summary display
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
