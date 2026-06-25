# Current Handoff — Daily Narrative Rich-Day Targeting + Context Differentiation v1

Status: implemented / ready for review.

Branch: `feature/daily-narrative-rich-day-targeting-context-differentiation-v1`

Latest milestone work:

- Added Daily Narrative rich-day scan service and CLI.
- Added Developer Mode rich-day candidate display.
- Added public-safe per-day fact inventory/counts/reason codes to Daily Narrative context summary.
- Added deterministic next-action differentiation based on selected facts.
- Preserved normal Today behavior and manual-only provider boundary.

Validation should include:

- `python tools/dev_daily_narrative_rich_day_scan.py --user-id 102 --start-date 2026-05-31 --end-date 2026-06-06 --top 10`
- `python tools/dev_daily_narrative_rich_day_scan.py --user-id 105 --start-date 2026-05-31 --end-date 2026-06-06 --top 10`
- rich day vs low-data day vs no-data day comparison in Developer Mode.

No public/default Daily Narrative provider display, automatic generation, worker, queue, scheduler, polling, CrewAI, qwen3 promotion, 14B promotion, or 32B call was added.

## Workout Plan Selection Persistence + Today Workout De-dup v1

Current authorized hotfix: fix Workout preview -> Select This Workout -> Active Workout persistence and remove the duplicate full workout selection flow from Today. Workout page is canonical for Plan / Active / Review. Today shows only compact workout status and route-to-Workout behavior.

Boundaries: no provider/AI workout generation, no CrewAI/Ollama changes, no automatic generation, no worker/queue/scheduler/polling, no exercise variety/rotation work, no Streamlit theme cleanup.
