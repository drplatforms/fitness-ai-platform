# Weekly Coach Summary QA Data Context Integration v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/weekly-coach-summary-qa-data-context-integration-v1`

This milestone integrates selected QA date-range fact inventory into a richer backend-owned deterministic `WeeklyCoachSummaryContext`.

Scope completed:

- Added a backend-owned QA context service for selected user/date ranges.
- Preserved typed `user_id`, `start_date`, and `end_date` inputs.
- Converted safe aggregate QA inventory into bounded Weekly Coach Summary context.
- Included selected user/date provenance, source metadata, data quality, limitations, and reason codes.
- Added safe aggregate recovery, nutrition, training, and workout execution summaries where available.
- Preserved the Developer Mode QA Date Range Debug flow.
- Preserved lazy navigation and Linux Developer page latency boundaries.
- Preserved provider-free deterministic generation.
- Kept normal/default UI and Today behavior unchanged.

Explicitly not included:

- provider runtime
- Ollama/CrewAI/qwen calls
- public/default Weekly Coach Summary display
- automatic generation
- worker/queue/scheduler/polling/background process
- database schema change
- raw rows, raw logs, raw notes, prompt text, scratchpad, or provider output display
